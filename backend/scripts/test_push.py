"""Send a test push to every device registered by a user and print what Firebase answers.

Uso (desde backend/):  python -m scripts.test_push correo@ejemplo.com
"""
import sys

from sqlalchemy import func

from app.core.database import SessionLocal
from app.models.notification import DeviceToken
from app.models.user import User
from app.services import notification_delivery


def main(email: str) -> int:
    db = SessionLocal()
    try:
        user = db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()
        if user is None:
            print(f"No existe un usuario con correo {email}")
            return 1
        if notification_delivery._firebase_app() is None:
            print("Firebase NO está configurado en el backend: define FIREBASE_SERVICE_ACCOUNT_PATH en backend/.env "
                  "con la ruta al JSON de la cuenta de servicio (Firebase > Configuración > Cuentas de servicio).")
            return 1
        devices = db.query(DeviceToken).filter(DeviceToken.user_id == user.id).all()
        if not devices:
            print("El usuario no tiene dispositivos registrados. Inicia sesión en la app móvil y acepta el permiso "
                  "de notificaciones. Si aun así no aparece, la app se compiló sin google-services.json.")
            return 1
        for device in devices:
            label = f"[{device.platform}{'' if device.is_active else ', inactivo'}] ...{device.token[-12:]}"
            try:
                notification_delivery._send_push(device.token, "Prueba FashionStore", "Si ves esto, las push funcionan.", {})
                print(f"OK    {label}")
            except Exception as error:  # show Firebase's exact reason
                print(f"ERROR {label}: {type(error).__name__}: {error}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
