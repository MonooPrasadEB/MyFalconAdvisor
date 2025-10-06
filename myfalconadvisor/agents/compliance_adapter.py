
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from myfalconadvisor.core.compliance_agent import (
    PolicyStore, ComplianceChecker, default_rules, _dataclass_to_dict, AuditLogger
)
import json, logging



class ComplianceAdapter:
    def __init__(self, policy_path: Optional[str]="policies.json", watch: bool=True, watch_interval_sec: int=5, db_service=None):
        self.log = logging.getLogger("compliance.adapter")
        self.store = PolicyStore(Path(policy_path) if policy_path else None, logger=self.log)
        if policy_path and Path(policy_path).exists():
            self.store.load_from_file()
        else:
            self.store.load_from_dict(default_rules("v1"))
            if policy_path:
                Path(policy_path).write_text(json.dumps(default_rules("v1"), indent=2), encoding="utf-8")
        if watch and policy_path:
            self.store.start_file_watcher(interval_sec=watch_interval_sec)
        
        # Set up database logging if db_service is provided
        if db_service:
            AuditLogger.get().set_db_service(db_service)
        
        self.checker = ComplianceChecker(self.store)

    def check_trade(self, **kwargs): 
        res = self.checker.check_trade_compliance(**kwargs)
        return _dataclass_to_dict(res)

    def check_trade_compliance(self, **kwargs): 
        return self.check_trade(**kwargs)

    def check_portfolio(self, **kwargs):
        res = self.checker.check_portfolio_compliance(**kwargs)
        return _dataclass_to_dict(res)

    def check_portfolio_compliance(self, **kwargs):
        return self.check_portfolio(**kwargs)

    def get_policies(self) -> Dict[str, Any]:
        snap = self.store.snapshot()
        return {"version": snap.version, "checksum": snap.checksum, "loaded_at": snap.loaded_at.isoformat(),
                "rules": {k: self._rule_to_dict(v) for k,v in snap.rules.items()}}

    def update_policies(self, new_policies: Dict[str, Any]) -> Dict[str, Any]:
        snap = self.store.update_policies(new_policies)
        return {"version": snap.version, "checksum": snap.checksum, "loaded_at": snap.loaded_at.isoformat()}

    def load_policies_from_file(self, path: str) -> Dict[str, Any]:
        self.store._policy_path = Path(path)
        snap = self.store.load_from_file()
        return {"version": snap.version, "checksum": snap.checksum, "loaded_at": snap.loaded_at.isoformat()}

    @staticmethod
    def _rule_to_dict(r) -> Dict[str, Any]:
        from dataclasses import asdict
        d = asdict(r); d["effective_date"]=r.effective_date.isoformat(); d["last_updated"]=r.last_updated.isoformat(); return d
