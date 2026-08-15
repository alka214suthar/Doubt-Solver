# 🤖 AI Doubt Solver

A full-stack AI-powered learning platform that allows students to ask academic doubts, receive AI-generated solutions, upload question images, bookmark important doubts, and track their learning activity.

## 🚀 Features

- 🔐 User Registration & JWT Authentication
- 🤖 AI-powered doubt solving using Google Gemini
- 🖼️ Upload images of questions
- 📚 Subject & Class-based doubt categorization
- 🕒 Doubt History with search and filters
- 🔖 Bookmark doubts for quick revision
- 👍 AI answer feedback (Helpful / Not Helpful)
- 👤 User Profile with usage tracking and learning milestones
- 🛡️ API rate limiting and response caching
- 🗄️ PostgreSQL database with Alembic migrations
- 🐳 Docker support

## 🖥️ Application Screenshots

### 🔐 Login
<img width="959" height="503" alt="Screenshot 2026-08-05 024504" src="https://github.com/user-attachments/assets/5068ac1a-7cc7-4b6a-a3b4-dc07219f59b0" />


### 📝 Registration
<img width="948" height="498" alt="Screenshot 2026-08-05 024543" src="https://github.com/user-attachments/assets/f8d61442-c500-4d7c-b2e4-132093171010" />


### 🤖 Ask Doubt
<img width="959" height="499" alt="Screenshot 2026-08-05 025405" src="https://github.com/user-attachments/assets/9bfb3bdb-8e7d-431e-a4e9-97c267495331" />
<img width="958" height="493" alt="Screenshot 2026-08-05 025435" src="https://github.com/user-attachments/assets/bc2e9c5c-4e9c-4f45-b6a7-8c911a15d4c3" />


### 📚 Doubt History
<img width="957" height="500" alt="Screenshot 2026-08-05 025508" src="https://github.com/user-attachments/assets/10d74f0f-21b6-4c16-b8f1-8309de381882" />


### 🔖 Bookmarked Doubts
<img width="959" height="500" alt="Screenshot 2026-08-05 025529" src="https://github.com/user-attachments/assets/19fc1669-539a-4eba-b6a1-39fde81d2e50" />


### 👤 User Profile & Learning Progress
<img width="959" height="501" alt="Screenshot 2026-08-05 025553" src="https://github.com/user-attachments/assets/a272077c-4fa8-417f-8cf1-8f1ffc6c9fe9" />
<img width="959" height="500" alt="Screenshot 2026-08-05 025609" src="https://github.com/user-attachments/assets/2ad1e328-4b16-4e0e-a609-fac03c615a35" />



## 🛠️ Tech Stack

### Frontend
- React
- Vite
- Tailwind CSS
- Axios

### Backend
- Python
- FastAPI
- SQLAlchemy
- Alembic
- JWT Authentication

### Database & AI
- PostgreSQL
- Google Gemini API

### DevOps
- Docker
- Nginx
- Git

## 🏗️ Architecture

React Frontend → FastAPI REST API → PostgreSQL
                              ↓
                       Google Gemini API

## ⭐ Key Engineering Highlights

- Designed REST APIs using FastAPI with layered service/repository architecture.
- Implemented JWT-based authentication and protected user-specific resources.
- Integrated Google Gemini API for AI-generated academic solutions.
- Implemented PostgreSQL persistence with Alembic database migrations.
- Built doubt history, bookmarking, feedback, and usage tracking features.
- Added per-user rate limiting and response caching to improve reliability and control API usage.
- Implemented image upload support for question-based doubts.
- Containerized the application using Docker for deployment.

## ⚙️ Run Locally

### Backend

```bash
cd backend
python -m venv venv
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
npm install
npm run dev
```

### Docker

```bash
docker compose up --build
```

## 🔐 Environment Variables

Create `.env` files locally and configure:

```text
DATABASE_URL
GEMINI_API_KEY
JWT_SECRET
CORS_ORIGINS
VITE_API_BASE_URL
```

`.env` files and secrets are never committed to the repository.

## 📌 Project Status

**Completed full-stack project** with authentication, AI integration, PostgreSQL persistence, image uploads, doubt history, bookmarks, feedback, rate limiting, caching, testing, and Docker support.
