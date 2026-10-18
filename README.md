# Omnichannel eCommerce Platform | Web, Mobile & API

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Angular](https://img.shields.io/badge/Angular-Frontend-DD0031?style=flat&logo=angular&logoColor=white)](https://angular.dev)
[![Flutter](https://img.shields.io/badge/Flutter-Mobile_App-02569B?style=flat&logo=flutter&logoColor=white)](https://flutter.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Alembic-4169E1?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)

Modern eCommerce platform with decoupled product catalog, cart management, order checkout, administrative console, and cross-platform mobile shopping app.

---

## 🏛️ Multi-Platform Architecture

- **`backend/`**: Asynchronous REST API built with **FastAPI**, SQLModel/SQLAlchemy, and Alembic migrations.
- **`frontend/`**: Responsive web store built with **Angular** and modern UI components.
- **`mobile/`**: Mobile shopping application built with **Flutter** for iOS and Android.

---

## 🚀 Setup

```bash
# Backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm start

# Mobile
cd mobile && flutter pub get && flutter run
```

---

## 👤 Author

Developed by **María Ilse Romero Saavedra** ([@miromero13](https://github.com/miromero13)).
