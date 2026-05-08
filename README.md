# AI Diabetes Prediction System

[![GitHub Repository](https://img.shields.io/badge/GitHub-diabetic--system-blue?logo=github)](https://github.com/rachait/diabetic-system)

> **Repository:** https://github.com/rachait/diabetic-system

A full-stack healthcare web app for diabetes risk prediction using a trained machine learning model, with user authentication, risk history tracking, wellness recommendations, and a product/store workflow.

## Tech Stack

- Backend: Flask, NumPy, Pandas, scikit-learn, SQLite
- Frontend: React, Vite, Tailwind CSS, Framer Motion
- ML Artifacts: `models/best_model.pkl`, `models/scaler.pkl`
- Deployment: Docker + Docker Compose

## Core Features

- Diabetes risk prediction from clinical inputs
- Prediction confidence, risk bands, and action suggestions
- User signup/login with session-based authentication
- Persisted risk assessment history
- Wellness endpoints (meal plans, doctor availability, chatbot)
- Basic e-commerce flow (products, cart, checkout)

## Repository Structure

```text
.
|- backend/        Flask app, API routes, DB layer, backend Dockerfile
|- frontend/       React app (Vite), Nginx config, frontend Dockerfile
|- app/            Shared HTML templates/static assets used by backend
|- models/         Trained model/scaler + ML training scripts
|- data/           SQLite DB, dataset, uploads, misc runtime data
|- docker-compose.yml
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm
- Docker Desktop (optional, for containerized run)

## Option 1: Run With Docker (Recommended)

From project root:

```bash
docker compose up --build
```

Open:

- App (frontend via Nginx): `http://localhost:8080`
- Backend API: `http://localhost:5000`

Container details:

- `backend/Dockerfile` runs Flask on port 5000
- `frontend/Dockerfile` builds React app and serves it with Nginx
- `frontend/nginx.conf` proxies `/api` to backend

## Option 2: Run Locally (Backend + Frontend)

### Quick Start (Single Command)

From project root:

```powershell
npm install
npm run dev
```

This starts both:

- Backend: `http://localhost:5000`
- Frontend: `http://localhost:5173`

### 1) Start Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Backend URL: `http://localhost:5000`

### 2) Start Frontend (new terminal)

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## Environment Notes

- Backend supports these environment variables:
   - `SECRET_KEY`
   - `FRONTEND_ORIGINS`
   - `SESSION_COOKIE_SECURE`
   - `MODEL_VERSION`
- Frontend uses `VITE_API_BASE` (defaults to `/api` in code).

## Main API Endpoints

Auth:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/check`

Prediction:

- `POST /api/predict`
- `GET /api/health`

Wellness:

- `POST /api/wellness/risk-assessment`
- `GET /api/wellness/risk-assessment/history`
- `GET /api/wellness/meal-plans`
- `GET /api/wellness/doctors/available`
- `POST /api/wellness/chatbot`
- `GET /api/wellness/admin/overview` (admin only)

Store:

- `GET /api/store/products`
- `GET /api/store/cart`
- `POST /api/store/cart/add`
- `POST /api/store/checkout`

## Admin Dashboard Overview

The frontend includes an Admin Dashboard section for operational monitoring.

It shows:

- Total users
- Total risk assessments
- Diabetic vs non-diabetic assessment counts
- Nutritionist booking count
- Recent assessments table
- 14-day assessment trend chart

Role-based access:

- The backend endpoint `GET /api/wellness/admin/overview` is admin-protected.
- If a logged-in user is not admin, admin metrics are not returned.
- The first registered account is auto-marked as admin to bootstrap access.

## Database Storage Overview

Current storage:

- Database type: SQLite
- Database file: `data/app.db`
- Core tables: `users`, `risk_assessments`, `products`, `cart_items`, `orders`, `order_items`, `nutritionist_bookings`, `meal_plans`

Production guidance:

- SQLite is good for local/small deployments.
- For higher concurrency and scaling, migrate to PostgreSQL or MySQL.
- Keep the same schema model and move credentials/connection settings to environment variables.

## Model and Data

- Trained model and scaler are loaded from:
   - `models/best_model.pkl`
   - `models/scaler.pkl`
- SQLite DB is stored at `data/app.db`.
- Default products and DB schema are created automatically on startup.

## Troubleshooting

- If frontend cannot reach backend in local dev, verify `VITE_API_BASE` and backend CORS `FRONTEND_ORIGINS`.
- If prediction fails, confirm model artifacts exist in `models/`.
- If PowerShell blocks script activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Disclaimer

This application provides decision-support insights only and is not a medical diagnosis tool. Always consult qualified healthcare professionals for medical advice.

## Getting This Repository

Clone from GitHub:

```bash
git clone https://github.com/rachait/diabetic-system.git
cd diabetic-system
```
