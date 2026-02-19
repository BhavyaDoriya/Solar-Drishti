# ☀️ SolarDrishti — Precision Solar Intelligence

Transforming atmospheric complexity into reliable clean energy foresight through end-to-end engineering.

🌐 Live Demo: https://solar-drishti.onrender.com/

---

## 📌 Overview

SolarDrishti is a machine learning-powered solar energy forecasting platform designed to predict next-two-days solar energy output using atmospheric and radiation data.

The system integrates:

- Structured solar-weather datasets
- Advanced feature engineering
- LightGBM model training & evaluation
- Production-grade Django backend
- Interactive dashboard interface
- Cloud deployment

This project represents a complete ML system lifecycle — from dataset structuring to production deployment.

---

## 🧠 Project Architecture Separation

SolarDrishti is built on a modular architecture:

### 📦 Dataset Construction (Separate Repository)

Dataset generation is handled in:

👉 https://github.com/BhavyaDoriya/solar_weather_data_prep

That repository is responsible for:

- NREL solar data sourcing
- Weather data aggregation
- Data cleaning & normalization
- Final structured dataset generation

It does **not** perform ML training.

---

### 🚀 SolarDrishti (Current Repository)

This repository handles:

- Feature augmentation
- Additional engineered columns
- ML model training
- Model evaluation
- Model serialization
- Backend integration
- Prediction serving
- Frontend visualization
- Deployment configuration

---

## ⚙️ Production Inference Design

The trained LightGBM model is serialized and loaded during application startup.
Predictions are performed through a lightweight inference layer, ensuring low latency and avoiding retraining during user requests.

## 🔬 Machine Learning Pipeline (SolarDrishti)

1. Load structured dataset from data prep pipeline
2. Perform feature expansion & transformation
3. Train LightGBM regression model
4. Evaluate model using validation metrics
5. Serialize trained model
6. Integrate model into Django backend for inference

The production system performs real-time inference using the pre-trained model.

---

## 🚀 Core Features

- 🔮 Next-two-day solar energy prediction
- 🌦️ Weather-aware inference
- 📊 Historical visualization dashboard
- 🧠 LightGBM-based regression engine
- 🔐 Secure Django architecture
- 🌍 Deployed production platform (Render)

---

## 🛠️ Tech Stack

### Backend
- Django
- PostgreSQL
- Gunicorn
- Whitenoise

### Machine Learning
- LightGBM
- Scikit-learn
- Pandas
- NumPy

### Data Sources

- NREL Solar Power Data for Integration Studies (Synthetic PV power output data, 2006)
- NREL CONUS 2006–2100 Hourly 4km Climate Dataset (RCP4.5 emissions scenario)
- OpenWeather API (real-time weather inputs)
- Open-Meteo API (supplementary real-time weather inputs)

### Frontend
- Bootstrap
- Custom UI/UX components
- JavaScript

### Deployment
- Render Cloud Platform

---

## 👥 Project Ownership & Work Division

SolarDrishti is collaboratively developed and jointly owned by:

### 👨‍💻 Bhavya Doriya — Data & ML Engineer

- GitHub: @BhavyaDoriya  
- Dataset integration
- Feature engineering & column expansion
- Machine learning model training
- Model evaluation & validation
- ML-backend integration
- System design architecture

### 🛡️ Pratham — Integrity Manager

- GitHub: @prathamshah1910
- Backend structural organization
- Security configuration
- Scalability oversight
- Deployment environment management

### 🎨 Jyoti — UI/UX Designer

- GitHub: @Shubhra-jyoti
- Visual interface design
- Dashboard experience layout
- Frontend interaction design
- Design system styling

This project is an original collaborative engineering effort.

---

## 🔐 Environment Variables

Create a `.env` file using the provided `.env.example` template:
Refer to .env.example for the complete variable list.

---

## 💻 Installation & Local Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/BhavyaDoriya/Solar-Drishti.git
cd Solar-Drishti
```
### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate # Mac/Linux
venv\Scripts\activate # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```
### 4️⃣ Apply Migrations

```bash
python manage.py migrate
```
### 5️⃣ Run Development Server

```bash
python manage.py runserver
```
Visit:
http://127.0.0.1:8000/

---
## 📊 Data Licensing

All raw dataset sourcing and licensing details are documented in:

👉 solar_weather_data_prep repository

Please review that repository for attribution and usage policies related to NREL and weather datasets.

---

## 📈 Project Status

- ✅ Dataset pipeline complete
- ✅ ML model trained & validated
- ✅ Production deployment live
- 🔄 Continuous performance refinement ongoing

## 📜 License

This project is licensed under the MIT License.

---

## 🌞 Vision

SolarDrishti bridges atmospheric intelligence and clean energy optimization through disciplined data engineering, applied machine learning, and production-grade deployment.