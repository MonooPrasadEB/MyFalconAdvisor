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
from myfalconadvisor.tools.alpaca_trading_service import alpaca_trading_service


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
        # Note: 'approved' status removed in 5-status model
        # Handle both direct SQL strings and text() objects
        sql_lower = sql.lower()
        if "status = 'executed'" in sql_lower or "status='executed'" in sql_lower:
            self._log_store.append(("executed", params))
        elif "status = 'rejected'" in sql_lower or "status='rejected'" in sql_lower:
            self._log_store.append(("rejected", params))
        else:
            self._log_store.append(("other", params))
        # Return a mock result object that has the expected interface
        return _FakeResult()

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

    if not chunks:
        print("❌ Trade approval stream failed: No chunks returned")
        return False
    
    first_chunk = chunks[0]
    success_chunk = next((c for c in chunks if c["type"] == "content" and "Trade Executed Successfully" in c["content"]), None)
    final_chunk = chunks[-1]

    # Note: 'approved' status removed in 5-status model - transactions go directly from pending to executed
    executed_updates = [entry for entry in call_log if entry[0] == "executed"]

    # Debug: Print chunk types and content previews
    chunk_types = [c.get("type") for c in chunks]
    content_chunks = [c.get("content", "")[:50] for c in chunks if c.get("type") == "content"]
    
    # Debug output
    checks = {
        "first_chunk_type": first_chunk.get("type") == "content",
        "trade_approved_text": "Trade Approved" in first_chunk.get("content", ""),
        "success_chunk_found": success_chunk is not None,
        "final_chunk_type": final_chunk.get("type") == "final",
        "workflow_complete": final_chunk.get("result", {}).get("workflow_complete") is True,
        "executed_updates": len(executed_updates) == 1,
        "exec_mock_called": exec_mock.called
    }
    
    passed = all(checks.values())
    
    if not passed:
        failed_checks = [k for k, v in checks.items() if not v]
        print(f"❌ Trade approval stream failed: {', '.join(failed_checks)}")
        print(f"   Chunk types: {chunk_types}")
        print(f"   Content previews: {content_chunks}")
        print(f"   Call log entries: {[e[0] for e in call_log]}")
        print(f"   Exec mock called: {exec_mock.called}")
    else:
        print("✅ Trade approval stream completed")
    
    return passed


def test_stream_trade_approval_rejected_status():
    """Ensure rejected executions update transactions and return rejection message."""
    print("\n🧪 Test: Trade approval rejection path")
    supervisor = investment_advisor_supervisor

    pending_trade = {
        "transaction_id": "txn-999",
        "symbol": "QQQ",
        "action": "buy",
        "quantity": 100,
        "price": 500.00
    }

    call_log: List[Tuple[str, dict]] = []

    def fake_get_session():
        return _UpdateSession(call_log)

    mock_execution_result = {
        "status": "rejected",
        "message": "Insufficient cash balance"
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

    rejection_chunk = next((c for c in chunks if c["type"] == "content" and "Trade Rejected" in c["content"]), None)
    final_chunk = chunks[-1]

    rejected_updates = [entry for entry in call_log if entry[0] == "rejected"]

    passed = (
        rejection_chunk is not None
        and len(rejected_updates) == 1
        and rejected_updates[0][1].get("transaction_id") == "txn-999"
        and "Insufficient cash balance" in rejected_updates[0][1].get("notes", "")
        and final_chunk["type"] == "final"
        and exec_mock.called
    )

    print("✅ Trade rejection handled" if passed else "❌ Trade rejection handling failed")
    return passed


def test_symbol_normalization_for_compliance_review():
    """Verify companies resolve to tickers before logging transactions."""
    print("\n🧪 Test: Symbol normalization in compliance review")
    supervisor = investment_advisor_supervisor

    trade = {
        "symbol": "Nutanix",
        "action": "buy",
        "quantity": 10,
        "price": 70.25,
        "order_type": "market"
    }

    client_profile = {"risk_tolerance": "moderate", "user_id": "user-abc"}
    portfolio_data = {"total_value": 100000, "holdings": []}

    original_review = supervisor.compliance_reviewer.review_investment_recommendation

    with patch.object(
        supervisor.compliance_reviewer,
        "review_investment_recommendation",
        wraps=original_review
    ) as review_mock, patch.object(
        alpaca_trading_service,
        "resolve_symbol",
        return_value="NTNX"
    ) as resolve_mock, patch.object(
        alpaca_trading_service,
        "_get_current_price",
        return_value=70.25
    ), patch.object(
        database_service,
        "insert_compliance_check",
        return_value=True
    ), patch.object(
        database_service,
        "create_pending_transaction",
        return_value="txn-mock"
    ) as create_txn_mock:
        result = supervisor._execute_real_compliance_review(
            trade_recommendations=[trade],
            client_profile=client_profile,
            portfolio_data=portfolio_data,
            user_id="user-abc",
            context="Buy Nutanix shares"
        )

    if create_txn_mock.called:
        print("create_pending_transaction call args:", create_txn_mock.call_args)

    resolved_called = resolve_mock.called
    txn_called = create_txn_mock.called
    normalized_symbol = create_txn_mock.call_args.kwargs.get("symbol") if txn_called else None
    response_has_ntnx = "NTNX" in result
    review_called = review_mock.called

    print(f"resolve_mock.called={resolved_called}")
    print(f"create_pending_transaction.called={txn_called}")
    print(f"normalized symbol passed={normalized_symbol}")
    print(f"response contains NTNX={response_has_ntnx}")
    print(f"review_mock.called={review_called}")

    passed = resolved_called and txn_called and normalized_symbol == "NTNX" and response_has_ntnx and review_called

    print("✅ Symbol normalization works" if passed else "❌ Symbol normalization failed")
    return passed


def main():
    """Run trade execution & compliance tests and report score."""
    tests = [
        ("Extreme concentration guardrail", test_extreme_concentration_block),
        ("Compliance review with warnings", test_compliance_review_runs_with_moderate_warning),
        ("Pending transaction lookup", test_pending_transaction_lookup_returns_latest),
        ("Trade approval streaming", test_stream_trade_approval_executes_successfully),
        ("Trade approval rejection handling", test_stream_trade_approval_rejected_status),
        ("Symbol normalization", test_symbol_normalization_for_compliance_review),
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
