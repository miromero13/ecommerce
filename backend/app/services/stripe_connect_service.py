"""D2 Stripe Connect: every company is paid into its own Express account (destination charges)."""
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.tenant import Tenant


def _stripe():
    import stripe

    if not settings.stripe_secret_key:
        raise ValueError("Stripe no está configurado")
    stripe.api_key = settings.stripe_secret_key
    return stripe


def _tenant(db: Session, tenant_id: UUID) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise ValueError("Empresa no encontrada")
    return tenant


def create_onboarding_link(db: Session, tenant_id: UUID, return_url: str) -> str:
    stripe = _stripe()
    tenant = _tenant(db, tenant_id)
    if not tenant.stripe_account_id:
        account = stripe.Account.create(type="express", email=tenant.contact_email,
                                        metadata={"tenant_id": str(tenant.id)})
        tenant.stripe_account_id = account.id
        db.commit()
    link = stripe.AccountLink.create(account=tenant.stripe_account_id, refresh_url=return_url,
                                     return_url=return_url, type="account_onboarding")
    return link.url


def get_status(db: Session, tenant_id: UUID) -> dict:
    tenant = _tenant(db, tenant_id)
    if tenant.stripe_account_id:
        account = _stripe().Account.retrieve(tenant.stripe_account_id)
        set_charges_enabled(db, tenant.stripe_account_id, bool(account.charges_enabled))
        db.refresh(tenant)
    return {"connected": bool(tenant.stripe_account_id), "charges_enabled": tenant.stripe_charges_enabled,
            "account_id": tenant.stripe_account_id}


def set_charges_enabled(db: Session, account_id: str, enabled: bool) -> None:
    db.query(Tenant).filter(Tenant.stripe_account_id == account_id).update({"stripe_charges_enabled": enabled})
    db.commit()


def require_online_payments(db: Session, tenant_id: UUID) -> Tenant:
    tenant = _tenant(db, tenant_id)
    if not (tenant.stripe_account_id and tenant.stripe_charges_enabled):
        raise ValueError("La empresa aún no habilitó pagos en línea")
    return tenant


def destination_params(tenant: Tenant, amount_cents: int) -> dict:
    fee = Decimal(amount_cents) * Decimal(tenant.platform_fee_percent or 0) / 100
    return {"transfer_data": {"destination": tenant.stripe_account_id},
            "application_fee_amount": int(fee.quantize(Decimal("1"), rounding=ROUND_HALF_UP))}
