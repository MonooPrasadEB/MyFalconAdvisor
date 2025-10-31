"""
Trade Execution & Compliance workflow tests.

Validates the supervisor's pending trade approval flow and compliance review logic
without touching live services by stubbing database and execution layers.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple
from unittest.mock import patch

# Ensure project root is on sys.path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from myfalconadvisor.core.supervisor import investment_advisor_supervisor
from myfalconadvisor.agents.execution_agent import execution_service
from myfalconadvisor.tools.database_service import database_service


class _FakeResult:
    """Simple result proxy to emulate SQLAlchemy fetch helpers."""

    def __init__(self, rows: Optional[List[Tuple[Any, ...]]] = None, row: Optional[Tuple[Any, ...]] = None):
        self._rows = rows or []
        self._row = row

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._row


class _PendingSession:
    """Context manager that returns canned results for pending-trade lookups."""

    def __init__(self, debug_rows: List[Tuple[Any, ...]], pending_row: Optional[Tuple[Any, ...]]):
        self._calls = 0
        self._debug_rows = debug_rows
        self._pending_row = pending_row

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, *_args, **_kwargs):
        self._calls += 1
        if self._calls == 1:
            return _FakeResult(rows=self._debug_rows)
        return _FakeResult(row=self._pending_row)

    def commit(self):
        # No-op for selects
        return None


class _UpdateSession:
    """Context manager that records UPDATE executions for trade approval flow."""

    def __init__(self, log_store: List[Tuple[str, dict]]):
        self._log_store = log_store

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement, params=None):
        sql = str(statement)
        params = params or {}
        if "SET status = 'approved'" in sql:
            self._log_store.append(("approved", params))
        elif "SET status = 'executed'" in sql:
            self._log_store.append(("executed", params))
        else:
            self._log_store.append(("other", params))
        return None

    def commit(self):
        self._log_store.append(("commit", {}))


def test_extreme_concentration_block():
    """Ensure high-concentration trades are blocked before reaching compliance reviewer."""
    print("\n🧪 Test: Extreme concentration guardrail")
    supervisor = investment_advisor_supervisor

    trade = {
        "symbol": "AAPL",
        "action": "buy",
        "quantity": 400,
        "price": 100.0,
        "order_type": "market"
    }

    client_profile = {"risk_tolerance": "moderate"}
    portfolio_data = {
        "total_value": 100_000,
        "assets": [
            {
                "symbol": "AAPL",
                "quantity": 200,
                "current_price": 100.0,
                "market_value": 20_000.0
            }
        ]
    }

    with patch.object(supervisor.compliance_reviewer, "review_investment_recommendation") as review_mock:
        response = supervisor._execute_real_compliance_review(
            [trade],
            client_profile,
            portfolio_data,
            user_id="user-123",
            context="Please buy more AAPL"
        )

    passed = "EXTREME CONCENTRATION RISK" in response and not review_mock.called
    print("✅ Guardrail blocked trade" if passed else "❌ Guardrail failed")
    return passed


def test_compliance_review_runs_with_moderate_warning():
    """Verify compliance review executes and returns formatted warnings for moderate concentration."""
    print("\n🧪 Test: Compliance review with moderate concentration warning")
    supervisor = investment_advisor_supervisor

    trade = {
        "symbol": "MSFT",
        "action": "buy",
        "quantity": 50,
        "price": 100.0,
        "order_type": "market",
        "rationale": "Increase exposure to large-cap tech"
    }

    client_profile = {"risk_tolerance": "moderate"}
    portfolio_data = {
        "total_value": 50_000,
        "assets": [
            {
                "symbol": "MSFT",
                "quantity": 100,
                "current_price": 100.0,
                "market_value": 10_000.0
            }
        ]
    }

    mock_review_response = {
        "compliance_score": 85,
        "compliance_issues": [
            {"description": "Document suitability rationale", "severity": "minor"}
        ],
        "status": "approved"
    }

    with patch.object(
        supervisor.compliance_reviewer,
        "review_investment_recommendation",
        return_value=mock_review_response
    ) as review_mock:
        response = supervisor._execute_real_compliance_review(
            [trade],
            client_profile,
            portfolio_data,
            user_id="user-abc",
            context="Purchase MSFT"
        )

    contains_score = ("Compliance Score" in response) and ("85/100" in response)
    includes_warning = "⚠️ CONCENTRATION WARNING" in response
    review_called = review_mock.called

    passed = contains_score and includes_warning and review_called
    status_msg = "✅ Compliance review executed" if passed else "❌ Compliance review failed"
    print(status_msg)

    if review_called:
        args, kwargs = review_mock.call_args
        context = kwargs.get("recommendation_context", {})
        if context.get("quantity") != 50:
            passed = False
            print("⚠️ Quantity mismatch in recommendation context")

    return passed


def test_pending_transaction_lookup_returns_latest():
    """Confirm pending transaction lookup pulls the most recent pending trade."""
    print("\n🧪 Test: Pending transaction lookup")
    supervisor = investment_advisor_supervisor

    debug_rows = [
        ("user-999", "TSLA", "pending"),
        ("user-123", "NVDA", "pending"),
    ]
    pending_row = (
        "txn-001",
        "NVDA",
        "buy",
        10,
        420.50,
        "2025-10-30 21:40:00",
        "Pending compliance approval",
        "user-123"
    )

    def fake_get_session():
        return _PendingSession(debug_rows, pending_row)

    with patch.object(database_service, "get_session", side_effect=fake_get_session):
        result = supervisor._check_pending_transaction("user-123")

    passed = (
        isinstance(result, dict)
        and result.get("transaction_id") == "txn-001"
        and result.get("symbol") == "NVDA"
        and result.get("action") == "buy"
        and result.get("quantity") == 10
    )

    print("✅ Pending trade found" if passed else "❌ Pending trade lookup failed")
    return passed


def test_stream_trade_approval_executes_successfully():
    """Validate the streaming approval flow updates DB status and returns final metadata."""
    print("\n🧪 Test: Streaming trade approval success path")
    supervisor = investment_advisor_supervisor

    pending_trade = {
        "transaction_id": "txn-777",
        "symbol": "NVDA",
        "action": "buy",
        "quantity": 5,
        "price": 850.25
    }

    call_log: List[Tuple[str, dict]] = []

    def fake_get_session():
        return _UpdateSession(call_log)

    mock_execution_result = {
        "status": "filled",
        "filled_quantity": 5,
        "fill_price": 852.10
    }

    async def _collect_chunks():
        chunks = []
        async for chunk in supervisor._stream_trade_approval(
            pending_trade,
            user_id="user-123",
            portfolio_data={"assets": []},
            session_id="sess-999"
        ):
            chunks.append(chunk)
        return chunks

    with patch.object(database_service, "get_session", side_effect=fake_get_session), patch.object(
        execution_service,
        "process_ai_recommendation",
        return_value=mock_execution_result
    ) as exec_mock:
        chunks = asyncio.run(_collect_chunks())

    first_chunk = chunks[0]
    success_chunk = next((c for c in chunks if c["type"] == "content" and "Trade Executed Successfully" in c["content"]), None)
    final_chunk = chunks[-1]

    approved_updates = [entry for entry in call_log if entry[0] == "approved"]
    executed_updates = [entry for entry in call_log if entry[0] == "executed"]

    passed = (
        first_chunk["type"] == "content"
        and "Trade Approved" in first_chunk["content"]
        and success_chunk is not None
        and final_chunk["type"] == "final"
        and final_chunk["result"]["workflow_complete"] is True
        and len(approved_updates) == 1
        and len(executed_updates) == 1
        and exec_mock.called
    )

    print("✅ Trade approval stream completed" if passed else "❌ Trade approval stream failed")
    return passed


def main():
    """Run trade execution & compliance tests and report score."""
    tests = [
        ("Extreme concentration guardrail", test_extreme_concentration_block),
        ("Compliance review with warnings", test_compliance_review_runs_with_moderate_warning),
        ("Pending transaction lookup", test_pending_transaction_lookup_returns_latest),
        ("Trade approval streaming", test_stream_trade_approval_executes_successfully),
    ]

    results = []
    for name, test_func in tests:
        try:
            outcome = test_func()
            results.append((name, bool(outcome)))
        except Exception as exc:
            results.append((name, False))
            print(f"💥 {name} crashed: {exc}")

    print("\n" + "=" * 80)
    print("🏁 TRADE EXECUTION & COMPLIANCE TEST RESULTS")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:.<55} {status}")

    score_pct = (passed / total * 100) if total else 0.0
    print(f"\nScore: {passed}/{total} ({score_pct:.1f}%)")

    if passed == total:
        print("🎉 Trade execution and compliance workflows are healthy.")
    elif passed >= total * 0.75:
        print("👍 Core workflow is mostly working; review failing cases above.")
    else:
        print("⚠️ Critical issues detected in trade execution or compliance flow.")


if __name__ == "__main__":
    main()
