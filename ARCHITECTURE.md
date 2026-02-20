# 🏗️ SolarDrishti System Architecture

This document describes the structural, functional, and machine learning architecture of SolarDrishti.

SolarDrishti is designed as a modular production-oriented ML system that separates:

- Dataset construction (external repository)
- Model training pipeline
- Runtime inference engine
- Django application layer
- Frontend presentation layer

---

# 1️⃣ High-Level Architecture

SolarDrishti follows a layered architecture:

1. Presentation Layer (HTML Templates)
2. Application Layer (Django Backend)
3. Machine Learning Layer
   - Training Pipeline
   - Runtime Inference Engine
4. Data Layer (PostgreSQL & CSV)

---

# 2️⃣ Project Structure Overview

```text
Solar-Drishti/
│
├── Solar_Drishti/       # Django project configuration
├── forecasting/         # Main Django application
├── media/               # Dataset storage
├── staticfiles/         # Collected static files
├── .env                 # Environment variables (DB URL, API Keys)
├── manage.py
└── requirements.txt
```

---

# 3️⃣ Django Project Layer

## 📁 Solar_Drishti/

Contains global Django configuration:

- `settings.py` → Environment configuration, PostgreSQL database setup (via Render), API configuration
- `urls.py` → Root URL routing
- `wsgi.py` / `asgi.py` → Deployment entry points

This layer configures:

- Installed apps
- Environment variables (parsed via `python-decouple` or `os`)
- Email API integration (Brevo SMTP)
- Static file handling
- Production Database connection mapping

---

# 4️⃣ Main Application Layer

## 📁 forecasting/

This is the core Django application handling:

- User interaction
- Authentication
- Prediction requests
- History storage
- Template rendering

Key files:

- `views.py` → Handles HTTP requests and connects to ML inference
- `urls.py` → App-level routing
- `models.py` → Database models (SolarSystem, Prediction)
- `admin.py` → Admin configuration
- `templates/forecasting/` → All UI templates

---

# 5️⃣ Machine Learning Layer

Located under:
`forecasting/ml/`

This layer is divided into:

1. Training Pipeline
2. Runtime Inference Engine
3. Model Artifacts
4. Research & Evaluation

---

# 6️⃣ Model Storage

`forecasting/ml/models/lgb_model.pkl`

- LightGBM regression model
- Serialized after training
- Loaded during runtime inference
- Prevents retraining on each request

This follows production ML best practices.

---

# 7️⃣ ML Training Architecture

Training modules are organized under:
`forecasting/ml/py_files/`

### Components

- `load_data.py` → Loads structured dataset
- `features.py` → Feature engineering & column transformations
- `config.py` → Hyperparameters & configuration
- `train.py` → Model training logic
- `metrics.py` → Evaluation metric computation
- `run_train.py` → Orchestrates complete training pipeline

### Training Flow

1. Load dataset (from `/media/pv_weather_hourly.csv`) *(dataset is not uploaded on this repo, to create dataset visit: https://github.com/BhavyaDoriya/solar_weather_data_prep)*
2. Apply feature engineering
3. Split train/test
4. Train LightGBM regressor
5. Evaluate using metrics (MAE, RMSE, R²)
6. Serialize model → `/ml/models/lgb_model.pkl`
7. Save evaluation plots → `/ml/plots/`

---

# 8️⃣ Runtime Inference Architecture

Runtime prediction is separated from training.

Core files:

- `predict.py` → Central inference engine
- `weather.py` → OpenWeather API integration
- `solar.py` → Open-Meteo API integration

---

# 9️⃣ Inference Flow (Step-by-Step)

1. User submits prediction request via `predict.html`.
2. Django `views.py` receives request.
3. View calls ML inference module.
4. `weather.py` fetches real-time atmospheric data.
5. `solar.py` fetches supplementary forecast inputs.
6. `predict.py`:
   - Combines API responses
   - Constructs feature DataFrame matching training schema
   - Loads `lgb_model.pkl`
   - Performs prediction
7. Prediction result returned to view.
8. View renders response on dashboard.
9. Prediction stored in the PostgreSQL database.

This ensures:

- No retraining during runtime
- Low-latency inference
- Clear separation of concerns

---

# 🔟 Templates Layer

Located at:
`forecasting/templates/forecasting/`

Includes:

- `index.html`
- `predict.html`
- `history.html`
- `about.html`
- Authentication pages (`login.html`, `signup.html`, `update_profile.html`, `profile.html`)

This layer handles UI rendering and interacts with backend endpoints.

---

# 1️⃣1️⃣ Data Layer

### Dataset Storage
`media/pv_weather_hourly.csv`

This dataset:
- Is generated from the external data preparation repository
- Serves as training input
- Is **not** used during runtime inference

### Production Database
**PostgreSQL (Hosted on Render)**

Configured securely via the `DATABASE_URL` environment variable. 

Stores:
- User data & Authentication credentials
- Solar System configurations & geolocation coordinates
- Prediction history logs and verified actual power yields

---

# 1️⃣2️⃣ Evaluation & Research Artifacts

`forecasting/ml/plots/`
`forecasting/ml/notebook/`

- Contains evaluation graphs (MAE, RMSE, R²)
- Contains EDA and experimentation notebooks
- Used for development & research
- Not used in runtime inference

---

# 1️⃣3️⃣ Architectural Design Principles

SolarDrishti follows:

- Clear separation of training and inference
- Modular ML pipeline design
- Serialized model serving
- API-driven real-time feature acquisition
- Environment-variable-based configuration (12-Factor App methodology)
- Scalable Django application structure suitable for cloud deployment

---

# 1️⃣4️⃣ External Data Pipeline Separation

Dataset construction is handled separately in:
https://github.com/BhavyaDoriya/solar_weather_data_prep

That repository:

- Sources NREL datasets
- Cleans and structures data
- Produces ML-ready dataset

SolarDrishti handles:

- Feature augmentation
- Model training
- Inference serving
- Deployment

This modular separation improves maintainability and clarity.

---

# 1️⃣5️⃣ Summary

SolarDrishti is architected as a production-grade ML web application with:

- Dedicated ML training pipeline
- Separate runtime inference engine
- Clear application-layer integration
- Modular folder organization
- Proper model serialization
- Cloud-native database integration (PostgreSQL)
- Clean separation between data engineering and deployment

This design enables:

- Maintainability
- Scalability
- Reproducibility
- Clear team ownership boundaries