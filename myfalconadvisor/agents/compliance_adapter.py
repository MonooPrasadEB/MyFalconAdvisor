from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
import json, logging

from myfalconadvisor.core.compliance_agent import (
    PolicyStore, ComplianceChecker, default_rules, _dataclass_to_dict
)

def _resolve_policy_path(policy_path: Optional[str]) -> Optional[Path]:
    """
    Prefer the given path if it exists; otherwise fall back to
    myfalconadvisor/core/policies.json to avoid 'file not found'.
    """
    if policy_path:
        p = Path(policy_path)
        if p.is_file():
            return p
    pkg_default = Path(__file__).resolve().parents[1] / "core" / "policies.json"
    if pkg_default.is_file():
        return pkg_default
    return Path(policy_path) if policy_path else None

class ComplianceAdapter:
    def __init__(self, policy_path: Optional[str] = "policies.json",
                 watch: bool = True, watch_interval_sec: int = 5):
        self.log = logging.getLogger("compliance.adapter")

        p = _resolve_policy_path(policy_path)
        self.store = PolicyStore(p if p else None, logger=self.log)

        if p and p.exists():
            self.store.load_from_file()
        else:
            data = default_rules("v1")
            self.store.load_from_dict(data)
            if p:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(data, indent=2), encoding="utf-8")

        if watch and p:
            self.store.start_file_watcher(interval_sec=watch_interval_sec)

        self.checker = ComplianceChecker(self.store)

    def check_trade(self, **kwargs) -> Dict[str, Any]:
        res = self.checker.check_trade_compliance(**kwargs)
        return _dataclass_to_dict(res)   # ✅ use the top-level import

    def check_trade_compliance(self, **kwargs) -> Dict[str, Any]:
        return self.check_trade(**kwargs)

    def check_portfolio(self, **kwargs) -> Dict[str, Any]:
        res = self.checker.check_portfolio_compliance(**kwargs)
        return _dataclass_to_dict(res)   # ✅ use the top-level import

    def check_portfolio_compliance(self, **kwargs) -> Dict[str, Any]:
        return self.check_portfolio(**kwargs)

    def get_policies(self) -> Dict[str, Any]:
        snap = self.store.snapshot()
        return {
            "version": snap.version,
            "checksum": snap.checksum,
            "loaded_at": snap.loaded_at.isoformat(),
            "rules": {k: self._rule_to_dict(v) for k, v in snap.rules.items()},
        }

    def update_policies(self, new_policies: Dict[str, Any]) -> Dict[str, Any]:
        snap = self.store.update_policies(new_policies)
        return {
            "version": snap.version,
            "checksum": snap.checksum,
            "loaded_at": snap.loaded_at.isoformat(),
        }

    def load_policies_from_file(self, path: str) -> Dict[str, Any]:
        p = Path(path)
        self.store._policy_path = p
        snap = self.store.load_from_file()
        return {
            "version": snap.version,
            "checksum": snap.checksum,
            "loaded_at": snap.loaded_at.isoformat(),
        }

    @staticmethod
    def _rule_to_dict(r) -> Dict[str, Any]:
        from dataclasses import asdict
        d = asdict(r)
        d["effective_date"] = r.effective_date.isoformat()
        d["last_updated"] = r.last_updated.isoformat()
        return d
