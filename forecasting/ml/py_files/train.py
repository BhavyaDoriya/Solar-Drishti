import lightgbm as lgb
import joblib
from load_data import load_and_split_data
from config import INPUT_COLS, TARGET_COL, MODEL_PATH
from metrics import regression_metrics


def train_and_save_model():
    train_df, val_df, test_df = load_and_split_data()

    model = lgb.LGBMRegressor(
        n_estimators=1000,
        learning_rate=0.05,
        num_leaves=64,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        train_df[INPUT_COLS],
        train_df[TARGET_COL],
        eval_set=[(val_df[INPUT_COLS], val_df[TARGET_COL])],
        eval_metric="rmse",
        callbacks=[
        lgb.early_stopping(stopping_rounds=50),
        lgb.log_evaluation(50)
    ]
    )
    y_test = test_df[TARGET_COL]
    y_pred = model.predict(test_df[INPUT_COLS])
    metrics = regression_metrics(y_test, y_pred)
    print("Test Metrics:")
    for k, v in metrics.items():
        print(f"{k.upper()}: {v:.4f}")

    joblib.dump(model, MODEL_PATH)
