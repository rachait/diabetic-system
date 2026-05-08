# Backend — Full Explanation

This document explains every part of the backend so you can study and present it confidently.

---

## What Is the Backend?

The backend is the **server-side** of the application. It:
- Receives requests from the frontend (React app)
- Runs the machine learning model to predict diabetes
- Manages users, login, and sessions
- Stores and retrieves data from the database
- Serves wellness, store, and admin features through a REST API

---

## Technology Stack

| Technology | What It Does |
|---|---|
| **Python** | The programming language the entire backend is written in |
| **Flask** | A lightweight web framework to build the API |
| **flask-cors** | Allows the frontend (on a different port) to talk to the backend |
| **SQLite** | A file-based database — stores users, orders, assessments |
| **scikit-learn** | The machine learning library used to train and run the prediction model |
| **NumPy** | Handles numerical arrays for ML feature processing |
| **Pandas** | Used in model training and data loading |
| **joblib** | Saves and loads the trained model and scaler from `.pkl` files |
| **hashlib + secrets** | Used for secure password hashing (no plain-text passwords) |
| **stripe** | Payment processing library (optional, for store checkout) |

---

## Folder Structure

```
backend/
├── run.py                  # Entry point — starts the Flask server
├── config.py               # All configuration (paths, keys, settings)
├── database.py             # All database tables and initialization
├── requirements.txt        # List of Python packages to install
├── Dockerfile              # Instructions to run backend in Docker
└── app/
    ├── __init__.py         # App factory — creates and configures Flask app
    ├── routes.py           # Main prediction API (/api/predict, /api/health)
    ├── auth_routes.py      # Login, register, logout (/api/auth/...)
    ├── wellness_routes.py  # Risk assessment, meal plans, chatbot, doctors
    ├── store_routes.py     # Products, cart, checkout (/api/store/...)
    ├── admin_routes.py     # Admin-only dashboard stats (/api/wellness/admin/...)
    ├── user_routes.py      # User profile management
    └── utils.py            # Input validation helpers
```

---

## How Flask Works

Flask is a **micro web framework**. You define routes (URLs) and attach Python functions to them.

```python
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})
```

When the frontend calls `GET /api/health`, Flask runs the `health()` function and returns the JSON response.

### Application Factory Pattern (`__init__.py`)

Instead of creating `app = Flask(__name__)` directly, this project uses a **factory function**:

```python
def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    # register blueprints, CORS, DB...
    return app
```

**Why?** It allows different configs (dev, production, testing) and makes the app easier to test.

---

## Blueprints

A **Blueprint** is a way to split routes into separate files/modules.

```python
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    ...
```

All routes in `auth_bp` automatically start with `/api/auth`. The blueprint is registered in `__init__.py`:

```python
app.register_blueprint(auth_bp)
```

**Blueprints in this project:**

| Blueprint | File | URL Prefix |
|---|---|---|
| `main_bp` | `routes.py` | `/api` |
| `auth_bp` | `auth_routes.py` | `/api/auth` |
| `wellness_bp` | `wellness_routes.py` | `/api/wellness` |
| `store_bp` | `store_routes.py` | `/api/store` |
| `admin_bp` | `admin_routes.py` | `/api/wellness/admin` |
| `user_bp` | `user_routes.py` | `/api/user` |

---

## Configuration (`config.py`)

All settings are stored in classes. Different environments (dev/prod) inherit from a base `Config`:

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key')
    MODEL_DIR = os.path.join(ROOT_DIR, 'models')
    BEST_MODEL_PATH = os.path.join(MODEL_DIR, 'best_model.pkl')
    SCALER_PATH = os.path.join(MODEL_DIR, 'scaler.pkl')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
```

**Key settings:**
- `SECRET_KEY` — used to sign session cookies (keep this secret in production)
- `MODEL_DIR` — path to the trained `.pkl` files
- `UPLOAD_FOLDER` — where uploaded files are saved
- `DEBUG` — shows detailed errors in development, disabled in production

---

## Database (`database.py`)

The project uses **SQLite** — a lightweight database stored as a single file (`data/app.db`).

### How to Connect

```python
import sqlite3

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets you access columns by name: row['username']
    return conn
```

### Tables

| Table | Purpose |
|---|---|
| `users` | Stores user accounts (id, username, email, password_hash, is_admin) |
| `risk_assessments` | Every diabetes prediction result linked to a user |
| `doctors` | Doctor profiles for appointment booking |
| `appointments` | Booked appointments between users and doctors |
| `products` | Health store product catalogue |
| `cart_items` | User's current shopping cart |
| `orders` | Placed orders |
| `order_items` | Individual items inside each order |
| `nutritionist_bookings` | Nutritionist booking records |
| `meal_plans` | Meal plan data per user |
| `auth_activity_logs` | Login/logout audit trail |

### How Data Is Inserted

```python
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute(
    'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
    (username, email, hashed_password)   # parameterized — prevents SQL injection
)
conn.commit()
conn.close()
```

> **Security note:** Always use `?` placeholders, never string concatenation in SQL queries.

---

## Authentication (`auth_routes.py`)

### Password Hashing

Passwords are **never stored in plain text**. They are hashed using `PBKDF2-HMAC-SHA256`:

```python
import hashlib, secrets

def hash_password(password):
    salt = secrets.token_hex(16)   # random 16-byte salt
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"
```

- A **salt** is a random value added before hashing to make identical passwords produce different hashes.
- **100,000 iterations** makes brute-force attacks slow.

### Sessions

Flask sessions store user info in a **signed cookie** sent to the browser:

```python
from flask import session

session['user_id'] = user['id']     # login
session.clear()                      # logout
```

The session is signed with `SECRET_KEY` so it cannot be tampered with.

### Endpoints

| Method | URL | What It Does |
|---|---|---|
| `POST` | `/api/auth/register` | Create a new account |
| `POST` | `/api/auth/login` | Log in, set session |
| `POST` | `/api/auth/logout` | Clear session |
| `GET` | `/api/auth/check` | Returns current logged-in user info |

---

## Diabetes Prediction (`routes.py`)

This is the **core feature** of the application.

### Input Features

The model expects 8 clinical inputs:

| Feature | Description |
|---|---|
| `pregnancies` | Number of pregnancies |
| `glucose` | Plasma glucose concentration |
| `blood_pressure` | Diastolic blood pressure (mm Hg) |
| `skin_thickness` | Triceps skin fold thickness (mm) |
| `insulin` | 2-hour serum insulin (mu U/ml) |
| `bmi` | Body mass index |
| `diabetes_pedigree` | Diabetes pedigree function (family history score) |
| `age` | Age in years |

### Prediction Flow

```
Frontend sends POST /api/predict
        ↓
Validate input (utils.py)
        ↓
Load model (best_model.pkl) and scaler (scaler.pkl)
        ↓
Scale the input features using the scaler
        ↓
model.predict(scaled_features) → 0 (no diabetes) or 1 (diabetic)
model.predict_proba() → probability score (e.g. 0.78)
        ↓
Apply clinical rule-based risk floor (clinical override)
        ↓
Return: prediction, confidence, risk_band, explanations
```

### Scaler

The **scaler** (`StandardScaler` from scikit-learn) transforms raw numbers into standardized values:

$$z = \frac{x - \mu}{\sigma}$$

Where $\mu$ is the mean and $\sigma$ is the standard deviation learned during training. This ensures the model gets consistent input ranges.

### Risk Bands

| Band | Meaning |
|---|---|
| `low` | Confidence < 65% or prediction is non-diabetic |
| `moderate` | Confidence 65–84% |
| `high` | Confidence ≥ 85% |

A **clinical rule-based floor** also overrides the model if strong signals are present (e.g., glucose ≥ 200 always triggers high risk).

### Rate Limiting

To prevent abuse, predictions are rate-limited to **20 requests per minute per user** using an in-memory sliding window.

---

## Wellness Module (`wellness_routes.py`)

| Endpoint | What It Does |
|---|---|
| `POST /api/wellness/risk-assessment` | Run a full risk assessment and save to DB |
| `GET /api/wellness/risk-assessment/history` | Get a user's past assessments |
| `GET /api/wellness/meal-plans` | Return meal plan suggestions |
| `GET /api/wellness/doctors/available` | List available doctors |
| `POST /api/wellness/chatbot` | Rule-based wellness chatbot reply |

The **chatbot** does not use an external AI API — it uses keyword matching to reply to health questions about diabetes, diet, BMI, etc.

---

## Store Module (`store_routes.py`)

Handles a basic e-commerce flow for health products:

| Endpoint | What It Does |
|---|---|
| `GET /api/store/products` | List all products (supports search & category filter) |
| `GET /api/store/products/<id>` | Get one product |
| `GET /api/store/cart` | Get user's current cart |
| `POST /api/store/cart/add` | Add item to cart |
| `POST /api/store/checkout` | Place an order |

**Stripe** is imported as an optional dependency for real payment processing (currently uses a placeholder key).

---

## CORS (`flask-cors`)

CORS (Cross-Origin Resource Sharing) is a browser security rule. Since the frontend runs on `localhost:5173` and the backend on `localhost:5000`, the browser would normally **block** requests between them.

`flask-cors` adds the right HTTP headers to allow this:

```python
from flask_cors import CORS

CORS(app,
     resources={r"/api/*": {"origins": ["http://localhost:5173"]}},
     supports_credentials=True)   # needed for session cookies to work
```

---

## How the ML Model Was Built

1. **Data:** `diabetes_prediction_india.csv` — clinical records with 8 features + diabetes label
2. **Preprocessing:** Missing values handled, features scaled with `StandardScaler`
3. **Training:** Multiple classifiers compared (Logistic Regression, Random Forest, etc.)
4. **Best model saved:** `models/best_model.pkl` using `joblib.dump(model, path)`
5. **Scaler saved:** `models/scaler.pkl`

At runtime, the backend loads these files once on startup and reuses them for every prediction.

---

## Running the Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Server starts at: `http://localhost:5000`

---

## Security Summary

| Practice | How It's Done |
|---|---|
| Password hashing | PBKDF2-HMAC-SHA256 with random salt |
| SQL injection prevention | Parameterized queries (`?` placeholders) |
| Session security | Signed cookies with `SECRET_KEY`, HttpOnly flag |
| CORS restriction | Only whitelisted frontend origins allowed |
| Rate limiting | In-memory sliding window on prediction endpoint |
| Admin protection | `is_admin` flag checked server-side before admin endpoints |
