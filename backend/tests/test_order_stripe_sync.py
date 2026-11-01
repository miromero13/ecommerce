"""Orders paid by card are confirmed (and notified) even when the Stripe webhook never arrives."""
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.schemas.order_schema import PaymentMethodEnum, PaymentStatusEnum
from app.services import order_service


class _Intent(dict):
    def __init__(self, status, last_error=None):
        super().__init__(id="pi_123", status=status, last_payment_error=last_error)
        self.id, self.status = "pi_123", status

    def to_dict(self):
        return dict(self)


def _order(**overrides):
    values = dict(id=uuid4(), payment_method=PaymentMethodEnum.stripe, payment_status=PaymentStatusEnum.pending,
                  stripe_payment_intent_id="pi_123")
    return SimpleNamespace(**{**values, **overrides})


@pytest.fixture
def stripe_mock(monkeypatch):
    fake = SimpleNamespace(api_key=None, PaymentIntent=SimpleNamespace(retrieve=MagicMock()))
    monkeypatch.setitem(sys.modules, "stripe", fake)
    monkeypatch.setattr(order_service.settings, "stripe_secret_key", "sk_test_x")
    process = MagicMock()
    monkeypatch.setattr(order_service, "process_stripe_event", process)
    return fake.PaymentIntent.retrieve, process


@pytest.mark.parametrize("status, last_error, expected", [
    ("succeeded", None, "payment_intent.succeeded"),
    ("requires_payment_method", {"code": "card_declined"}, "payment_intent.payment_failed"),
    ("canceled", None, "payment_intent.payment_failed"),
    ("requires_payment_method", None, None),  # customer has not paid yet
    ("processing", None, None),
])
def test_sync_applies_the_webhook_transition(stripe_mock, status, last_error, expected):
    retrieve, process = stripe_mock
    retrieve.return_value = _Intent(status, last_error)

    order_service._sync_stripe_order(MagicMock(), _order())

    if expected is None:
        process.assert_not_called()
    else:
        event = process.call_args.args[1]
        assert event["type"] == expected and event["data"]["object"]["id"] == "pi_123"


def test_sync_skips_orders_that_are_not_pending_card_payments(stripe_mock):
    retrieve, process = stripe_mock
    for order in (_order(payment_status=PaymentStatusEnum.paid), _order(payment_method=PaymentMethodEnum.wallet),
                  _order(stripe_payment_intent_id=None)):
        order_service._sync_stripe_order(MagicMock(), order)
    retrieve.assert_not_called()
    process.assert_not_called()


def test_stripe_outage_does_not_break_reading_the_order(stripe_mock):
    retrieve, process = stripe_mock
    retrieve.side_effect = RuntimeError("Stripe down")
    db = MagicMock()
    order_service._sync_stripe_order(db, _order())
    db.rollback.assert_called_once()
