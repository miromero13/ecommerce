"""Reenvía los webhooks de Stripe (modo prueba) al backend local, usando la clave de backend/.env.

Uso (desde backend/, con el backend corriendo en el puerto 8000):
    python -m scripts.stripe_listen
"""
import os
import shutil
import subprocess
import sys

from app.core.config import settings

WINGET_EXE = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Stripe.StripeCli_Microsoft.Winget.Source_8wekyb3d8bbwe\stripe.exe")


def main() -> int:
    stripe = shutil.which("stripe") or (WINGET_EXE if os.path.isfile(WINGET_EXE) else None)
    if not stripe:
        print("Falta Stripe CLI. Instálalo con: winget install Stripe.StripeCli")
        return 1
    key = settings.stripe_secret_key or ""
    if not key.startswith("sk_test_"):
        print("STRIPE_SECRET_KEY de backend/.env debe ser una clave de prueba (sk_test_...)")
        return 1
    env = {**os.environ, "STRIPE_API_KEY": key}
    secret = subprocess.run([stripe, "listen", "--print-secret"], env=env, capture_output=True, text=True).stdout.strip()
    if secret and secret != settings.stripe_webhook_secret:
        print(f"AVISO: pon STRIPE_WEBHOOK_SECRET={secret} en backend/.env y reinicia el backend.")
    return subprocess.run([stripe, "listen", "--forward-to", "localhost:8000/api/payments/stripe/webhook",
                           "--events", "payment_intent.succeeded,payment_intent.payment_failed,payment_intent.canceled"],
                          env=env).returncode


if __name__ == "__main__":
    sys.exit(main())
