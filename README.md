# 🚀 Promptly Backend

🌐 **Deployed Application**: _Will be done soon_

---

# 📑 Table of Contents
- [🎯 Project Overview](#-project-overview)
- [🧱 System Highlights](#-system-highlights)
- [🗂️ Project Architecture](#-project-architecture)
- [🛠️ Tech Stack](#-tech-stack)
- [⚙️ Environment Variables](#️-environment-variables)
- [🧪 Getting Started](#-getting-started)
- [🔗 Project References](#-project-references)
- [📄 Credits](#-credits)
- [🚀 Future Enhancements](#-future-enhancements)

---

## 🎯 Project Overview

Promptly Backend is a Django REST API built using HackSoft-style architecture principles.
It powers both Learner Mode and Developer Mode with clear separation between Selectors (reads), Services (writes), Serializers (validation), and Views (orchestration).

---


## 🧱 System Highlights

- HackSoft-inspired layered backend
- StreamingHttpResponse AI pipeline
- Multi-stream JSON protocol (coder/explainer)
- Stateless JWT auth
- Scalable database schema

---

## 🗂️ Project Architecture

```
Promptly/
├── apps/
│   ├── learning/
│   ├── development/
│   ├── authentication/
├── core/
├── manage.py
└── requirements.txt
```

---

## 🛠️ Tech Stack

- Python 3.x
- Django
- Django REST Framework
- SimpleJWT
- PostgreSQL
- LangChain + Ollama (AI Service Layer)

---

## ⚙️ Environment Variables

```
DATABASE_NAME=your_db
DATABASE_USER=your_user
DATABASE_PASSWORD=your_password
DATABASE_PORT=5432
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 🧪 Getting Started

```bash
git clone https://github.com/BAlshowaikh/Promptly.git
cd Promptly
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

---

## 🔗 Project References

- https://github.com/BAlshowaikh/Promptly
- Django REST Framework
- LangChain

---

## 📄 Credits

Developed by **BAlshowaikh**

---

## 🚀 Future Enhancements

- WebSocket streaming instead of HTTP streaming
- Automated test coverage
- AI performance optimization
