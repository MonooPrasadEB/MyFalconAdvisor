
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timezone
import json, threading, time, hashlib, logging, logging.handlers, difflib, uuid

# ---------------- Models ----------------
@dataclass
class ComplianceRule:
    rule_id: str
    regulation_source: str
    rule_name: str
    description: str
    severity: str
    applies_to: List[str]
    effective_date: datetime
    last_updated: datetime
    params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComplianceViolation:
    rule_id: str
    violation_type: str
    severity: str
    description: str
    recommended_action: str
    auto_correctable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TradeComplianceCheck:
    trade_approved: bool
    violations: List[ComplianceViolation]
    warnings: List[str]
    recommendations: List[str]
    requires_disclosure: bool
    compliance_score: int

@dataclass
class PortfolioComplianceCheck:
    overall_compliant: bool
    violations: List[ComplianceViolation]
    warnings: List[str]
    recommendations: List[str]
    next_review_date: datetime
    compliance_score: int

@dataclass
class PolicySet:
    version: str
    rules: Dict[str, 'ComplianceRule']

@dataclass
class PolicySnapshot:
    version: str
    checksum: str
    loaded_at: datetime
    rules: Dict[str, 'ComplianceRule']

# ---------------- Utils ----------------
def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _parse_dt(v: Any) -> datetime:
    if isinstance(v, datetime): return v
    return datetime.fromisoformat(str(v).replace("Z","+00:00"))

def _rule_to_json(r: ComplianceRule) -> Dict[str, Any]:
    d = asdict(r); d["effective_date"]=r.effective_date.isoformat(); d["last_updated"]=r.last_updated.isoformat(); return d

def _policy_to_json(policy: PolicySet) -> Dict[str, Any]:
    return {"version": policy.version, "rules": {rid: _rule_to_json(r) for rid, r in policy.rules.items()}}

def _dataclass_to_dict(obj):
    if hasattr(obj, "__dataclass_fields__"):
        d = asdict(obj)
        for k,v in list(d.items()):
            if isinstance(v, datetime): d[k]=v.isoformat()
            elif isinstance(v, list): d[k]=[_dataclass_to_dict(x) for x in v]
        return d
    return obj

# ---------------- Audit ----------------
class AuditLogger:
    _instance: Optional["AuditLogger"] = None
    def __init__(self, log_path: Optional[str]="compliance.log", db_service=None):
        self.logger = logging.getLogger("compliance"); self.logger.setLevel(logging.INFO)
        fmt = logging.Formatter("%(message)s")
        handlers=[logging.StreamHandler()]
        if log_path:
            handlers.append(logging.handlers.TimedRotatingFileHandler(log_path, when="midnight", backupCount=14, encoding="utf-8"))
        for h in handlers: h.setFormatter(fmt); self.logger.addHandler(h)
        self.db_service = db_service
    @classmethod
    def get(cls, db_service=None): 
        if not cls._instance: cls._instance=AuditLogger(db_service=db_service)
        return cls._instance
    def set_db_service(self, db_service):
        """Set the database service for PostgreSQL logging."""
        self.db_service = db_service
    def _emit(self, payload: Dict[str,Any]):
        self.logger.info(json.dumps(payload))
        if not self.db_service: return
        try:
            if payload.get("event")=="policy_change":
                # Log to audit_trail table using existing method
                self.db_service.create_audit_entry(
                    user_id="system",
                    entity_type="policy",
                    entity_id=payload["new_version"],
                    action="policy_update",
                    old_values={"version": payload.get("old_version"), "checksum": payload.get("old_checksum")},
                    new_values={"version": payload["new_version"], "checksum": payload["new_checksum"], "diff": payload.get("diff")}
                )
            elif payload.get("event")=="compliance_event":
                # Log to compliance_checks table
                result = payload.get("result", {})
                input_data = payload.get("input", {})
                check_result = "pass" if payload.get("decision") == "approved" else "fail"
                if len(result.get("warnings", [])) > 0 and check_result == "pass":
                    check_result = "warning"
                    
                severity_map = {"critical": "critical", "major": "high", "warning": "medium", "advisory": "low"}
                violations = result.get("violations", [])
                severity = "low"
                if violations:
                    severity = severity_map.get(violations[0].get("severity", "warning"), "medium")
                
                # Map event type to check_type (must be: suitability, concentration, liquidity, regulatory, risk_limit)
                type_mapping = {
                    "trade": "regulatory",
                    "portfolio": "concentration",
                    "recommendation": "suitability"
                }
                check_type = type_mapping.get(payload.get("type"), "regulatory")
                
                # Extract user_id, portfolio_id from input if available
                user_id = input_data.get("user_id") or input_data.get("client_profile", {}).get("client_id")
                portfolio_id = input_data.get("portfolio_id")
                transaction_id = input_data.get("transaction_id")
                recommendation_id = input_data.get("recommendation_id")
                
                # Validate UUIDs - set to None if not valid UUID format or if they don't exist in DB
                # For standalone compliance checks (no transaction yet), these will be None
                # They'll be populated when integrated with execution_agent
                import re
                uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
                if portfolio_id and not uuid_pattern.match(str(portfolio_id)):
                    portfolio_id = None
                if transaction_id and not uuid_pattern.match(str(transaction_id)):
                    transaction_id = None
                if recommendation_id and not uuid_pattern.match(str(recommendation_id)):
                    recommendation_id = None
                
                # Note: Foreign key constraints mean these UUIDs must exist in their respective tables
                # If they don't exist, set to None (compliance check can still proceed)
                
                # Use raw SQL insert via engine
                if hasattr(self.db_service, 'engine') and self.db_service.engine:
                    from sqlalchemy import text
                    with self.db_service.engine.connect() as conn:
                        insert_query = """
                        INSERT INTO compliance_checks(
                            user_id, portfolio_id, transaction_id, recommendation_id,
                            check_type, rule_name, rule_description, check_result, 
                            violation_details, severity, checked_at
                        )
                        VALUES (
                            :user_id, :portfolio_id, :transaction_id, :recommendation_id,
                            :check_type, :rule_name, :rule_description, :check_result, 
                            :violation_details, :severity, NOW()
                        )
                        """
                        conn.execute(text(insert_query), {
                            "user_id": user_id,
                            "portfolio_id": portfolio_id,
                            "transaction_id": transaction_id,
                            "recommendation_id": recommendation_id,
                            "check_type": check_type,
                            "rule_name": ",".join(payload.get("rule_ids", [])),
                            "rule_description": f"Compliance check for {payload.get('subject')}",
                            "check_result": check_result,
                            "violation_details": json.dumps({"input": input_data, "result": result, "score": payload.get("score")}),
                            "severity": severity
                        })
                        conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to log to database: {e}")
    def policy_change(self, old, new, diff_text=None):
        self._emit({"event":"policy_change","changed_at":datetime.now(timezone.utc).isoformat(),
                    "old_version":old.version,"old_checksum":old.checksum,
                    "new_version":new.version,"new_checksum":new.checksum,"diff":diff_text})
    def compliance_event(self, event_type, subject, input_obj, result_obj, rule_ids, score):
        self._emit({"event":"compliance_event","id":str(uuid.uuid4()),"at":datetime.now(timezone.utc).isoformat(),
                    "type":event_type,"subject":subject,"rule_ids":rule_ids,
                    "decision":"approved" if (result_obj.get("trade_approved") or result_obj.get("overall_compliant")) else "rejected",
                    "score":score,"input":input_obj,"result":result_obj})

def policies_to_markdown(snapshot: PolicySnapshot, out_path="Policies.md"):
    lines=[f"# Compliance Policies", f"- **Version**: {snapshot.version}", f"- **Checksum**: `{snapshot.checksum}`", f"- **Generated**: {datetime.now(timezone.utc).isoformat()}", ""]
    for rid, r in sorted(snapshot.rules.items()):
        lines += [f"## {rid} — {r.rule_name}", f"- Source: **{r.regulation_source}**",
                  f"- Severity: **{r.severity}**", f"- Applies To: {', '.join(r.applies_to)}",
                  f"- Effective: {r.effective_date} | Last Updated: {r.last_updated}",
                  f"- Params: `{json.dumps(r.params)}`","", r.description,""]
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")

# ---------------- Policy store ----------------
class PolicyStore:
    def __init__(self, policy_path: Optional[Path]=None, logger: Optional[logging.Logger]=None):
        self._lock=threading.RLock(); self._snapshot=None; self._subs=[]; self._policy_path=policy_path; self._logger=logger or logging.getLogger("compliance")
    def load_from_dict(self, data: Dict[str,Any]):
        rules={}
        for rid,raw in data["rules"].items():
            rules[rid]=ComplianceRule(rule_id=raw["rule_id"], regulation_source=raw["regulation_source"], rule_name=raw["rule_name"],
                                      description=raw.get("description",""), severity=raw["severity"], applies_to=raw.get("applies_to", []),
                                      effective_date=_parse_dt(raw["effective_date"]), last_updated=_parse_dt(raw.get("last_updated") or datetime.now(timezone.utc).isoformat()),
                                      params=raw.get("params", {}))
        policy=PolicySet(version=data.get("version","v1"), rules=rules)
        raw_sorted=json.dumps(_policy_to_json(policy), sort_keys=True)
        snap=PolicySnapshot(version=policy.version, checksum=_sha256(raw_sorted), loaded_at=datetime.now(timezone.utc), rules=policy.rules)
        with self._lock:
            old=self._snapshot; self._snapshot=snap
        if old: self._log_policy_change(old, snap)
        self._notify(snap); return snap
    def load_from_file(self):
        assert self._policy_path, "Policy path is not set"
        text=self._policy_path.read_text(encoding="utf-8")
        if self._policy_path.suffix.lower() in (".yaml",".yml"):
            import yaml; data=yaml.safe_load(text)
        else: data=json.loads(text)
        return self.load_from_dict(data)
    def update_policies(self, new_data: Dict[str,Any]): return self.load_from_dict(new_data)
    def snapshot(self): 
        with self._lock:
            if not self._snapshot: raise RuntimeError("Policies not loaded"); 
            return self._snapshot
    def subscribe(self, cb): self._subs.append(cb)
    def _notify(self, snap): 
        for cb in list(self._subs):
            try: cb(snap)
            except Exception: self._logger.exception("Policy subscriber failed")
    def start_file_watcher(self, interval_sec=5):
        assert self._policy_path is not None
        def _loop():
            last=None
            while True:
                try:
                    text=self._policy_path.read_text(encoding="utf-8"); cur=_sha256(text)
                    if cur!=last: self.load_from_file(); last=cur
                except Exception: self._logger.exception("Policy watcher error")
                time.sleep(interval_sec)
        threading.Thread(target=_loop, daemon=True).start()
    def _log_policy_change(self, old, new):
        try:
            old_d={"version":old.version,"rules":{k:asdict(v) for k,v in old.rules.items()}}
            new_d={"version":new.version,"rules":{k:asdict(v) for k,v in new.rules.items()}}
            diff="\n".join(difflib.unified_diff(json.dumps(old_d,indent=2,sort_keys=True).splitlines(),
                                                json.dumps(new_d,indent=2,sort_keys=True).splitlines(),
                                                fromfile=f"policies@{old.version}", tofile=f"policies@{new.version}"))
            AuditLogger.get().policy_change(old,new,diff); policies_to_markdown(new,"Policies.md")
        except Exception:
            # Silently fail - this is non-critical logging
            pass

# ---------------- Checker ----------------
class ComplianceChecker:
    def __init__(self, policy_store: PolicyStore, db_service=None):
        self.policy_store=policy_store
        self.db_service=db_service; self._snap=policy_store.snapshot(); policy_store.subscribe(self._on_update); self.audit=AuditLogger.get()
    def _on_update(self, snap): self._snap=snap
    def get_rule(self, rid): return self._snap.rules.get(rid)
    def validate_position_concentration(self, position_value, portfolio_value, symbol=None, user_id=None, portfolio_data=None):
        """Enhanced position concentration validation with existing position analysis."""
        v=[]; warnings=[]; rule=self.get_rule("CONC-001")
        if not rule: return v, warnings
        
        # Enhanced logic: Check total position (existing + new trade)
        existing_position_value = 0
        current_price = 0
        
        # Try to get existing position data
        if portfolio_data and symbol:
            # Look in assets first
            for asset in portfolio_data.get('assets', []):
                if asset.get('symbol') == symbol:
                    existing_quantity = float(asset.get('quantity', 0))
                    current_price = float(asset.get('current_price', 0))
                    existing_position_value = existing_quantity * current_price
                    break
            
            # Then check holdings if not found
            if not existing_position_value:
                for holding in portfolio_data.get('holdings', []):
                    if holding.get('symbol') == symbol:
                        existing_quantity = float(holding.get('quantity', 0))
                        current_price = float(holding.get('current_price', 0))
                        existing_position_value = existing_quantity * current_price
                        break
        
        # Calculate new total position
        new_total_position_value = existing_position_value + position_value
        new_position_pct = (new_total_position_value / portfolio_value * 100) if portfolio_value > 0 else 0
        
        # MAJOR VIOLATION: >50% concentration (BLOCKS trade)
        if new_position_pct > 50:
            v.append(ComplianceViolation(
                rule_id=rule.rule_id, 
                violation_type="concentration_risk", 
                severity="major",  # This will block the trade
                description=f"Position would be {new_position_pct:.1f}% of portfolio (exceeds 50% limit). This violates diversification principles and regulatory suitability standards.",
                recommended_action=f"Reduce trade size to keep {symbol or 'position'} under 50% of portfolio value",
                auto_correctable=True,
                metadata={"new_position_pct": new_position_pct, "limit": 50}
            ))
        
        # WARNING: 25-50% concentration (allows trade with warning)
        elif new_position_pct >= 25:
            warnings.append(f"Large position: {new_position_pct:.1f}% concentration in {symbol or 'this security'}")
        
        return v, warnings
    def validate_sector_concentration(self, sector_alloc):
        v=[]; rule=self.get_rule("CONC-002")
        if not rule: return v
        limit=float(rule.params.get("max_sector",0.40))
        for sector,alloc in sector_alloc.items():
            if alloc>limit:
                v.append(ComplianceViolation(rule_id=rule.rule_id, violation_type="sector_concentration", severity=rule.severity,
                                             description=f"Sector '{sector}' at {alloc:.0%} exceeds {limit:.0%} limit",
                                             recommended_action="Rebalance across sectors",
                                             metadata={"sector":sector,"allocation":alloc,"limit":limit}))
        return v
    def validate_wash_sale(self, trade_type, account_type, symbol=None, user_id=None, portfolio_id=None, quantity=0):
        """Enhanced wash sale validation with database lookup for actual violations."""
        warnings=[]; viol=[]; rule=self.get_rule("TAX-001")
        if not rule: 
            return warnings, viol
        
        # Only check for BUY orders in taxable accounts
        if trade_type != "buy" or account_type != "taxable":
            return warnings, viol
            
        # Use enhanced detection if we have required parameters
        if not hasattr(self, 'db_service') or not self.db_service:
            return warnings, viol
            
        if not user_id:
            return warnings, viol
        
        if symbol and user_id and hasattr(self, 'db_service') and self.db_service:
            try:
                # Enhanced wash sale detection with database queries
                violations = self._check_wash_sale_violation_enhanced(
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    buy_quantity=quantity
                )
                
                if violations:
                    # Real violation detected - BLOCK the trade
                    for violation in violations:
                        viol.append(ComplianceViolation(
                            rule_id=rule.rule_id,
                            violation_type="wash_sale",
                            severity="major",  # Block the trade
                            description=violation.get('description', 'Wash sale violation detected'),
                            recommended_action=violation.get('recommendation', 'Wait 31 days after sale or use tax-advantaged account'),
                            metadata=violation
                        ))
                    return warnings, viol
                    
            except Exception as e:
                # Fall through to basic warning if enhanced detection fails
                pass
        
        # Basic warning if enhanced detection unavailable or no violation found
        warnings.append("Verify no wash sale violation if selling similar security at loss within 30 days")
        return warnings, viol
    
    def _check_wash_sale_violation_enhanced(self, user_id, portfolio_id, symbol, buy_quantity):
        """Enhanced wash sale detection with database queries."""
        try:
            from datetime import datetime, timezone, timezone, timedelta
            from sqlalchemy import text
            
            if not self.db_service or not hasattr(self.db_service, 'engine'):
                return []
                
            # Query for SELL transactions of the same symbol within 30 days
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            
            with self.db_service.engine.connect() as conn:
                query = text("""
                    SELECT t.id, t.symbol, t.quantity, t.price, t.created_at,
                           pa.average_cost
                    FROM transactions t
                    JOIN portfolios p ON t.user_id = p.user_id
                    LEFT JOIN portfolio_assets pa ON p.portfolio_id = pa.portfolio_id AND t.symbol = pa.symbol
                    WHERE t.user_id = :user_id
                      AND t.symbol = :symbol
                      AND t.transaction_type = 'sell'
                      AND t.status = 'executed'
                      AND t.created_at >= :thirty_days_ago
                    ORDER BY t.created_at DESC
                """)
                
                result = conn.execute(query, {
                    'user_id': user_id,
                    'symbol': symbol,
                    'thirty_days_ago': thirty_days_ago
                })
                
                violations = []
                total_disallowed_loss = 0
                
                for sell in result:
                    # Get cost basis from portfolio_assets
                    average_cost = float(sell.average_cost) if sell.average_cost else None
                    sell_price = float(sell.price) if sell.price else None
                    
                    # If we don't have average_cost, get current price as fallback
                    if not sell_price:
                        try:
                            from ..tools.alpaca_trading_service import alpaca_trading_service
                            sell_price = alpaca_trading_service._get_current_price(symbol)
                        except:
                            sell_price = 0
                    
                    # Conservative approach: assume loss if we can't determine cost basis
                    if not average_cost:
                        average_cost = sell_price * 1.1  # Assume 10% loss
                    
                    # Calculate loss per share
                    loss_per_share = max(0, average_cost - sell_price)
                    
                    if loss_per_share > 0:
                        # This is a wash sale violation
                        sell_quantity = float(sell.quantity)
                        disallowed_quantity = min(buy_quantity, sell_quantity)
                        disallowed_loss = loss_per_share * disallowed_quantity
                        total_disallowed_loss += disallowed_loss
                        
                        days_ago = (datetime.now(timezone.utc) - sell.created_at).days
                        
                        violations.append({
                            'violation_detected': True,
                            'symbol': symbol,
                            'sell_date': sell.created_at.strftime('%Y-%m-%d'),
                            'days_ago': days_ago,
                            'sell_price': sell_price,
                            'average_cost': average_cost,
                            'loss_per_share': loss_per_share,
                            'disallowed_loss': disallowed_loss,
                            'disallowed_quantity': disallowed_quantity,
                            'description': f"Wash sale violation: You sold {symbol} at a loss ${loss_per_share:.2f}/share {days_ago} days ago. Repurchasing now will disallow ${disallowed_loss:.2f} in tax losses.",
                            'recommendation': f"Wait until {(sell.created_at + timedelta(days=31)).strftime('%Y-%m-%d')} (31 days after sale) or use a tax-advantaged account."
                        })
                
                return violations
                
        except Exception as e:
            print(f"Error in enhanced wash sale detection: {e}")
            return []
    
    def validate_pattern_day_trader(self, equity_value, client_type):
        warnings=[]; viol=[]; rule=self.get_rule("TRAD-001")
        if not rule: return warnings, viol
        if equity_value < float(rule.params.get("min_equity",25000)) and client_type=="individual":
            warnings.append("Under $25K equity; limit day trades to 3 per 5 days")
            viol.append(ComplianceViolation(rule_id=rule.rule_id, violation_type="pattern_day_trader", severity=rule.severity,
                                            description="Account under $25K - risk of PDT violations",
                                            recommended_action="Limit day trades to 3 per rolling 5-day window or raise equity above $25K"))
        return warnings, viol
    def validate_penny_stock(self, price):
        v=[]; rule=self.get_rule("PENNY-001")
        if not rule: return v
        thr=float(rule.params.get("min_price",5.0))
        if price<thr:
            v.append(ComplianceViolation(rule_id=rule.rule_id, violation_type="penny_stock", severity=rule.severity,
                                         description=f"Security price ${price:.2f} below ${thr:.2f} penny-stock threshold",
                                         recommended_action="Ensure heightened disclosure and suitability"))
        return v
    def validate_market_manipulation(self, trade_value, portfolio_value):
        warnings=[]; 
        if portfolio_value>0 and trade_value>portfolio_value*0.5:
            warnings.append("Large trade size - ensure no market manipulation concerns")
        return warnings
    def validate_suitability(self, recommendation_risk, client_risk_tolerance):
        violations=[]; warnings=[]; r1=self.get_rule("SUIT-001"); r2=self.get_rule("SUIT-002"); r3=self.get_rule("SUIT-003")
        risk_map={"conservative":1,"moderate":2,"aggressive":3}; rec=risk_map.get(recommendation_risk,2); cli=risk_map.get(client_risk_tolerance,2)
        if r1 and rec>cli+1:
            violations.append(ComplianceViolation(rule_id=r1.rule_id, violation_type="suitability", severity=r1.severity,
                                                  description=f"Recommendation risk '{recommendation_risk}' exceeds client tolerance '{client_risk_tolerance}'",
                                                  recommended_action="Adjust recommendation to match client profile"))
        if r2: warnings.append("Confirm aggregated transaction suitability over time (Quantitative Suitability)")
        if r3: warnings.append("Ensure research/analysis supports the recommendation (Reasonable Basis)")
        return violations, warnings
    def calculate_compliance_score(self, violations, warnings):
        score=100
        for v in violations: score -= {"critical":40,"major":30,"warning":20,"advisory":10}.get(v.severity,15)
        score -= 5*len(warnings); return max(0, score)
    def check_trade_compliance(self, *, trade_type, symbol, quantity, price, portfolio_value, client_type="individual", account_type="taxable", user_id=None, portfolio_id=None, transaction_id=None, recommendation_id=None):
        # Debug logging removed for cleaner output
        violations=[]; warnings=[]; recommendations=[]
        
        # Handle None price by fetching current market price
        if price is None:
            try:
                from ..tools.alpaca_trading_service import alpaca_trading_service
                price = alpaca_trading_service._get_current_price(symbol)
                # Debug logging removed for cleaner output
            except Exception as e:
                price = 0.0  # Fallback to prevent crash
        
        trade_value = quantity * price
        # Debug logging removed for cleaner output
        
        conc_v, conc_w = self.validate_position_concentration(trade_value, portfolio_value, symbol=symbol, user_id=user_id, portfolio_data=None); violations += conc_v; warnings += conc_w
        
        ws_w, ws_v = self.validate_wash_sale(trade_type, account_type, symbol=symbol, user_id=user_id, portfolio_id=portfolio_id, quantity=quantity); warnings += ws_w; violations += ws_v
        p_w, p_v  = self.validate_pattern_day_trader(portfolio_value, client_type); warnings += p_w; violations += p_v
        violations += self.validate_penny_stock(price)
        warnings += self.validate_market_manipulation(trade_value, portfolio_value)
        score=self.calculate_compliance_score(violations, warnings)
        trade_approved = not any(v for v in violations if v.severity in ("critical","major"))
        requires_disclosure = len(violations)>0
        result = TradeComplianceCheck(trade_approved, violations, warnings, recommendations, requires_disclosure, score)
        
        # Convert UUIDs to strings for JSON serialization
        audit_input = {
            "trade_type":trade_type,"quantity":quantity,"price":price,"portfolio_value":portfolio_value,
            "client_type":client_type,"account_type":account_type,
            "user_id":str(user_id) if user_id else None,
            "portfolio_id":str(portfolio_id) if portfolio_id else None,
            "transaction_id":str(transaction_id) if transaction_id else None,
            "recommendation_id":str(recommendation_id) if recommendation_id else None
        }
        
        AuditLogger.get().compliance_event("trade", symbol, audit_input, _dataclass_to_dict(result), [v.rule_id for v in violations], score)
        return result
    def check_portfolio_compliance(self, *, assets, portfolio_value, client_profile):
        violations=[]; warnings=[]; recommendations=[]
        sector_alloc={}
        for a in assets:
            sector=a.get("sector","Unknown"); alloc=float(a.get("allocation",0))/100.0
            sector_alloc[sector]=sector_alloc.get(sector,0.0)+alloc
        violations += self.validate_sector_concentration(sector_alloc)
        v_s, w_s = self.validate_suitability(client_profile.get("target_risk","moderate"), client_profile.get("risk_tolerance","moderate"))
        violations += v_s; warnings += w_s
        score=self.calculate_compliance_score(violations, warnings)
        overall = not any(v for v in violations if v.severity in ("critical","major"))
        result = PortfolioComplianceCheck(overall, violations, warnings, recommendations, datetime.now(timezone.utc), score)
        AuditLogger.get().compliance_event("portfolio", client_profile.get("client_id","unknown"),
            {"assets":assets,"portfolio_value":portfolio_value,"client_profile":client_profile},
            _dataclass_to_dict(result), [v.rule_id for v in violations], score)
        return result

# ---------------- Defaults ----------------
def default_rules(version="v1"):
    now=datetime.now(timezone.utc).isoformat()
    return {"version":version,"rules":{
        "CONC-001":{"rule_id":"CONC-001","regulation_source":"SEC","rule_name":"Position Concentration Limit","description":"Individual position should not exceed threshold of portfolio value","severity":"warning","applies_to":["individual","institutional"],"effective_date":"2000-01-01T00:00:00Z","last_updated":now,"params":{"max_position":0.25}},
        "CONC-002":{"rule_id":"CONC-002","regulation_source":"SEC","rule_name":"Sector Concentration Limit","description":"Single sector allocation should not exceed threshold of portfolio","severity":"warning","applies_to":["individual","institutional"],"effective_date":"2000-01-01T00:00:00Z","last_updated":now,"params":{"max_sector":0.40}},
        "CONC-003":{"rule_id":"CONC-003","regulation_source":"FINRA","rule_name":"Concentrated Position Disclosure","description":"Must disclose risks for concentrated positions","severity":"major","applies_to":["advisor"],"effective_date":"2012-07-09T00:00:00Z","last_updated":now},
        "SUIT-001":{"rule_id":"SUIT-001","regulation_source":"FINRA","rule_name":"Suitability Rule 2111","description":"Recommendations must be suitable for client based on profile","severity":"critical","applies_to":["advisor"],"effective_date":"2010-07-09T00:00:00Z","last_updated":now},
        "SUIT-002":{"rule_id":"SUIT-002","regulation_source":"FINRA","rule_name":"Quantitative Suitability","description":"Series of transactions must be suitable in aggregate","severity":"critical","applies_to":["advisor"],"effective_date":"2010-07-09T00:00:00Z","last_updated":now},
        "SUIT-003":{"rule_id":"SUIT-003","regulation_source":"FINRA","rule_name":"Reasonable Basis","description":"Advisors must have reasonable basis for recommendations","severity":"warning","applies_to":["advisor"],"effective_date":"2010-07-09T00:00:00Z","last_updated":now},
        "TAX-001":{"rule_id":"TAX-001","regulation_source":"IRS","rule_name":"Wash Sale Rule Section 1091","description":"Cannot claim loss if repurchasing substantially identical security within 30 days","severity":"warning","applies_to":["individual","institutional"],"effective_date":"1921-01-01T00:00:00Z","last_updated":now},
        "TRAD-001":{"rule_id":"TRAD-001","regulation_source":"FINRA","rule_name":"Pattern Day Trader Rule","description":"Accounts under $25K limited to 3 day trades per 5-day period","severity":"warning","applies_to":["individual"],"effective_date":"2001-02-27T00:00:00Z","last_updated":now,"params":{"min_equity":25000}},
        "TRAD-002":{"rule_id":"TRAD-002","regulation_source":"SEC","rule_name":"Market Manipulation Prevention","description":"Cannot engage in manipulative or deceptive trading practices","severity":"critical","applies_to":["individual","advisor"],"effective_date":"1934-06-06T00:00:00Z","last_updated":now},
        "PENNY-001":{"rule_id":"PENNY-001","regulation_source":"SEC","rule_name":"Penny Stock Disclosure","description":"Trades in penny stocks (< $5) require heightened suitability and disclosure","severity":"advisory","applies_to":["individual","advisor"],"effective_date":"2001-07-09T00:00:00Z","last_updated":now,"params":{"min_price":5.0}}
    }}

if __name__=="__main__":
    # optional demo execution (without database)
    p = Path("policies.json")
    if not p.exists(): p.write_text(json.dumps(default_rules("v1"), indent=2), encoding="utf-8")
    store = PolicyStore(policy_path=p, logger=logging.getLogger("compliance")); store.load_from_file(); store.start_file_watcher(3)
    checker = ComplianceChecker(store)
    res = checker.check_trade_compliance(trade_type="buy", symbol="ABC", quantity=100, price=4.5, portfolio_value=20000, client_type="individual", account_type="taxable")
    print(json.dumps(_dataclass_to_dict(res), indent=2))
