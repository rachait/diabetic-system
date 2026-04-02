# AI Diabetes Prediction System

Full-stack healthcare application with a modern React frontend and Flask ML backend for diabetes risk prediction.

## Features
- AI-based diabetes risk prediction from medical parameters
- Multi-step animated input form with progress indicator
- Result page with risk level, confidence gauge, and recommendations
- Login/Signup with session support
- Prediction history dashboard with trend chart
- AI chatbot endpoint for health guidance
- Voice input support for predictor fields and chatbot prompts

## Project Structure
- `backend/`: Flask API, auth, wellness, store, SQLite data layer
- `frontend/`: React + Vite + Tailwind UI
- `models/`: trained model/scaler artifacts and ML scripts

## Backend Setup
1. `cd backend`
2. `python -m venv .venv`
3. Activate environment:
   - Windows PowerShell: `.\.venv\Scripts\Activate.ps1`
4. `pip install -r requirements.txt`
5. `python run.py`

Backend runs at `http://localhost:5000`.

## Frontend Setup
1. `cd frontend`
2. Copy env file:
   - `copy .env.example .env`
3. `npm install`
4. `npm run dev`

Frontend runs at `http://localhost:5173`.

## One-Command Docker Deployment
1. From project root: `docker compose up --build`
2. Open app at `http://localhost:8080`
3. Backend API remains available at `http://localhost:5000`

Services and files:
- `backend/Dockerfile` for Flask API container
- `frontend/Dockerfile` for React build + Nginx serve
- `frontend/nginx.conf` for SPA routing and `/api` proxy
- `docker-compose.yml` to run both services together

## API Endpoints Used by Frontend
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/check`
- `POST /api/predict`
- `POST /api/wellness/risk-assessment`
- `GET /api/wellness/risk-assessment/history`
- `POST /api/wellness/chatbot`

## Notes
- Prediction confidence and recommendations are model-dependent.
- This app provides decision support only and is not a medical diagnosis.
- For cross-origin authenticated sessions, backend CORS is configured for localhost frontend ports.
