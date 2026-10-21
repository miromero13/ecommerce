from __future__ import annotations

import logging
from typing import List, Union

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self) -> None:
        self.mailer_service = settings.mailer_service
        self.mailer_email = settings.mailer_email
        self.mailer_key = settings.mailer_secret_key
        self.app_name = settings.app_name

    @property
    def is_configured(self) -> bool:
        return bool(self.mailer_service and self.mailer_email and self.mailer_key)

    async def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        html: str | None = None,
        text: str | None = None,
        category: str = "application",
    ) -> bool:
        """
        Send an email via Mailtrap API or fallback to logging if unconfigured.
        """
        recipients = [to] if isinstance(to, str) else to
        if not recipients or not subject or (not html and not text):
            logger.warning("EmailService.send_email called with missing required fields")
            return False

        if not self.is_configured:
            logger.info(
                "📧 [EMAIL SIMULATED / MAILTRAP DISABLED]\n"
                "To: %s\nSubject: %s\nText:\n%s\nHTML:\n%s\n",
                ", ".join(recipients),
                subject,
                text or "",
                html or "",
            )
            return True

        payload = {
            "from": {
                "email": self.mailer_email,
                "name": self.app_name,
            },
            "to": [{"email": email} for email in recipients],
            "subject": subject,
            "category": category,
        }
        if html:
            payload["html"] = html
        if text:
            payload["text"] = text

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.mailer_key}",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self.mailer_service,
                    json=payload,
                    headers=headers,
                )
                if response.status_code in (200, 201, 202):
                    logger.info("Email sent successfully to %s", ", ".join(recipients))
                    return True
                else:
                    logger.error(
                        "Mailtrap error (%d): %s",
                        response.status_code,
                        response.text,
                    )
                    return False
        except Exception as exc:
            logger.error("Exception sending email via Mailtrap: %s", exc)
            return False

    async def send_welcome_credentials_email(
        self,
        to_email: str,
        admin_name: str,
        tenant_name: str,
        plan_name: str,
        password: str,
        login_url: str = "http://localhost:4200/login",
    ) -> bool:
        subject = f"¡Bienvenido a {self.app_name}! Tu cuenta para {tenant_name} está activa"

        text_content = (
            f"Hola {admin_name},\n\n"
            f"¡Felicitaciones! Tu suscripción al plan '{plan_name}' para '{tenant_name}' ha sido activada con éxito.\n\n"
            f"Tus credenciales de acceso inicial son:\n"
            f"• URL de ingreso: {login_url}\n"
            f"• Correo electrónico: {to_email}\n"
            f"• Contraseña temporal: {password}\n\n"
            f"Por motivos de seguridad, te sugerimos cambiar tu contraseña una vez que ingreses al sistema.\n\n"
            f"Atentamente,\nEl equipo de {self.app_name}"
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 24px; }}
            .container {{ max-width: 580px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }}
            .header {{ background-color: #0f172a; color: #ffffff; padding: 28px 24px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; }}
            .content {{ padding: 28px 24px; }}
            .badge {{ display: inline-block; background-color: #eff6ff; color: #1d4ed8; padding: 4px 12px; border-radius: 9999px; font-size: 13px; font-weight: 600; margin-bottom: 16px; }}
            .credentials-card {{ background-color: #f1f5f9; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #0f172a; }}
            .credentials-item {{ margin-bottom: 10px; font-size: 14px; }}
            .credentials-item:last-child {{ margin-bottom: 0; }}
            .credentials-label {{ font-weight: 600; color: #475569; }}
            .credentials-val {{ font-family: 'SFMono-Regular', Consolas, monospace; background: #e2e8f0; padding: 2px 6px; border-radius: 4px; font-weight: 700; color: #0f172a; }}
            .btn {{ display: inline-block; background-color: #0f172a; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; font-size: 14px; margin-top: 16px; }}
            .footer {{ border-top: 1px solid #e2e8f0; padding: 20px 24px; text-align: center; font-size: 12px; color: #64748b; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>{self.app_name}</h1>
            </div>
            <div class="content">
              <span class="badge">Suscripción Activa</span>
              <h2>¡Hola, {admin_name}!</h2>
              <p>Tu empresa <strong>{tenant_name}</strong> ha sido registrada con éxito en nuestra plataforma bajo el plan <strong>{plan_name}</strong>.</p>
              
              <div class="credentials-card">
                <div class="credentials-item">
                  <span class="credentials-label">Usuario / Email:</span>
                  <span class="credentials-val">{to_email}</span>
                </div>
                <div class="credentials-item">
                  <span class="credentials-label">Contraseña Temporal:</span>
                  <span class="credentials-val">{password}</span>
                </div>
                <div class="credentials-item">
                  <span class="credentials-label">Rol Asignado:</span>
                  <span>Administrador</span>
                </div>
              </div>

              <p>Accedé al panel administrativo para configurar tus sucursales, inventario y productos:</p>
              <div style="text-align: center;">
                <a href="{login_url}" class="btn" style="color: #ffffff;">Ingresar a la Plataforma</a>
              </div>
            </div>
            <div class="footer">
              <p>Este es un correo automático generado por {self.app_name}. Si no solicitaste este acceso, por favor desestimalo.</p>
            </div>
          </div>
        </body>
        </html>
        """

        return await self.send_email(
            to=to_email,
            subject=subject,
            html=html_content,
            text=text_content,
            category="onboarding_welcome",
        )


email_service = EmailService()
