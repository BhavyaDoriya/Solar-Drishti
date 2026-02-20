# 📊 SolarDrishti — Model Performance & Runtime Inference Design

This document describes the machine learning model, feature engineering strategy, target construction, evaluation methodology, and real-time inference pipeline used in SolarDrishti.

The objective of the model is to predict short-term solar energy output using atmospheric and temporal features.

---

# 1️⃣ Problem Formulation

SolarDrishti models the task as a supervised regression problem.

## Objective

Predict **capacity-normalized solar energy output**, defined during training as:

specific_energy = energy_mwh / capacity_mw

The dataset generated from the external pipeline does NOT contain `specific_energy`.  
It is created inside the training pipeline (`train.py`) before model fitting.

Why normalize?

- Removes dependency on plant capacity
- Improves generalization across systems
- Enables scalable inference for different system sizes

Target variable:
- `specific_energy`

---

# 2️⃣ Dataset Overview (Training Data)

Dataset generated from:

👉 https://github.com/BhavyaDoriya/solar_weather_data_prep

Final structured dataset contains:

- timestamp
- lat
- lon
- capacity_mw
- energy_mwh
- ghi
- dni
- dhi
- air_temp
- wind_speed
- solar_zenith

There is **no `specific_energy` column initially**.  
It is computed during training.

The dataset file (`pv_weather_hourly.csv`) is not included in this repository.

---

# 3️⃣ Feature Engineering

Implemented in:

`forecasting/ml/py_files/features.py`

## Temporal Extraction

From `timestamp`, the following features are derived:

- date
- hour
- day
- month

## Cyclic Encoding

To preserve periodic time structure:

Hour encoding:
- hour_sin = sin(2π * hour / 24)
- hour_cos = cos(2π * hour / 24)

Month encoding:
- month_sin = sin(2π * (month − 1) / 12)
- month_cos = cos(2π * (month − 1) / 12)

Day encoding:
- day_sin = sin(2π * (day − 1) / 31)
- day_cos = cos(2π * (day − 1) / 31)

This allows the model to capture:

- Daily solar cycles
- Seasonal periodicity
- Nonlinear time interactions

---

# 4️⃣ Model Selection

SolarDrishti uses:

## 🌳 LightGBM Regressor

Reasons:

- High performance on structured tabular data
- Efficient gradient boosting implementation
- Strong nonlinear feature interaction capability
- Fast inference suitable for web deployment

---

# 5️⃣ Training Configuration

Hyperparameters used:

- n_estimators = 1000
- learning_rate = 0.05
- num_leaves = 64
- subsample = 0.8
- colsample_bytree = 0.8
- random_state = 42
- n_jobs = -1

These balance:

- Bias vs variance
- Stability vs performance
- Training efficiency

---

# 6️⃣ Training Pipeline

Located under:

`forecasting/ml/py_files/`

### Flow

1. Load dataset
2. Apply temporal & cyclic feature engineering
3. Create target:

   specific_energy = energy_mwh / capacity_mw

4. Define feature matrix (X) and target (y)
5. Perform grouped day-based temporal train–validation–test split:
   - Identify 365 unique dates (year 2006)
   - Shuffle the list of dates
   - Assign 70% of days to training
   - Assign 15% to validation
   - Assign 15% to testing
   - All hourly records belonging to a selected day are kept within the same split

   This prevents intraday leakage while preserving full hourly solar production patterns.

6. Train LightGBM regressor
7. Evaluate performance
8. Serialize model → `forecasting/ml/models/lgb_model.pkl`

The serialized model is used during runtime inference.

---

# 7️⃣ Evaluation Metrics

Model performance is evaluated using:

- MAE (Mean Absolute Error)
- RMSE (Root Mean Squared Error)
- R² Score

Evaluation plots stored in:

`forecasting/ml/plots/`

These metrics measure:

- Absolute deviation
- Large error sensitivity
- Variance explained by model

---

# 8️⃣ Runtime Inference Architecture

Runtime prediction is separate from training.

Real-time data sources:

- **OpenWeather API** → 3-hour interval forecast data
- **Open-Meteo API** → Hourly forecast data

### Data Resolution Handling

OpenWeather returns:
- Forecast values in 3-hour intervals

Open-Meteo returns:
- Hourly atmospheric and radiation variables

To standardize input resolution:

- Data is aligned into hourly structure
- 3-hour values are mapped appropriately across their interval
- A unified hourly DataFrame is constructed

---

# 9️⃣ Hour-by-Hour Model Inference

The inference pipeline works as follows:

1. Fetch forecast data (hourly + 3-hour sources).
2. Construct hourly DataFrame for next 48 hours.
3. Apply feature engineering (`features.py`).
4. For each hour:
   - Pass engineered features into LightGBM model.
   - Predict `specific_energy` for that hour.

This produces 48 hourly predictions.

---

# 🔟 Daily Aggregation Logic

After hourly predictions are generated:

1. Predictions are grouped by date.
2. Hourly specific_energy values are aggregated.
3. Aggregated value is multiplied by:

   system_size

Final calculation:

daily_energy_prediction = sum(hourly_specific_energy) × system_size

This produces the final 24-hour forecast returned to the user.

---

# 1️⃣1️⃣ Production Properties

- Model is NOT retrained during inference.
- Only serialized model is loaded.
- Hour-level predictions ensure temporal accuracy.
- Daily aggregation ensures meaningful user-facing output.

This design ensures:

- Low latency
- Deterministic behavior
- Scalable inference
- Clean separation between training and runtime

---

# 1️⃣2️⃣ Model Strengths

- Learns nonlinear irradiance–temperature–time interactions
- Captures daily production cycles
- Normalized target improves generalization
- Hour-level granularity improves forecast resolution

---

# 1️⃣3️⃣ Model Limitations

- Dependent on external API reliability
- Trained primarily on 2006 PV data
- Single grouped temporal split (no cross-validation yet)
- No advanced sequence modeling (e.g., LSTM)

---

# 1️⃣4️⃣ Summary

SolarDrishti’s predictive engine:

- Uses LightGBM regression
- Trains on normalized energy output
- Applies cyclic temporal encoding
- Uses grouped day-based temporal splitting
- Performs hour-level inference
- Aggregates predictions into daily forecasts
- Deploys serialized model for production use

The system is modular, scalable, and production-ready for web deployment.