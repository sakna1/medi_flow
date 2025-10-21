import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np
import joblib

# 1. Load data
df = pd.read_csv("patient_log.csv")

# 2. Preprocess columns
df["treatment_status"] = df["treatment_status"].map({"Active": 1, "Follow-up": 0})

if "scan_time" in df.columns:
    df["scan_time"] = pd.to_datetime(df["scan_time"])
    df["scan_hour"] = df["scan_time"].dt.hour
    df["day_of_week"] = df["scan_time"].dt.dayofweek

if "available_doctors" in df.columns:
    df["available_doctors"] = df["available_doctors"].fillna(df["available_doctors"].median())
else:
    df["available_doctors"] = 1


# 3. Derived features
df['queue_per_doctor'] = df['queue_length'] / df['available_doctors']
df['weighted_est_time'] = df['disease_est_time'] * (df['treatment_status'] + 1)

# 4. Define features
feature_cols = [
    "age", "disease_id", "queue_length", "disease_est_time",
    "treatment_status", "available_doctors",
    "queue_per_doctor", "weighted_est_time"
]

if "scan_hour" in df.columns and "day_of_week" in df.columns:
    feature_cols += ["scan_hour", "day_of_week"]

X = df[feature_cols]
y = df["actual_wait_time"]

# 5. Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 6. Train model
model = RandomForestRegressor(
    n_estimators=1329,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    max_features='sqrt',
    bootstrap=True,
    n_jobs=-1,
    random_state=42
)

model.fit(X_train, y_train)

# 7. Evaluate model
y_pred = model.predict(X_test)

r2 = model.score(X_test, y_test)
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)

print(f"Model R² score on test set: {r2:.4f}")
print(f"Mean Absolute Error (MAE): {mae:.4f}")
print(f"Mean Squared Error (MSE): {mse:.4f}")
print(f"Root Mean Squared Error (RMSE): {rmse:.4f}")

# 8. Save model
joblib.dump(model, "wait_time_model.pkl")
print("✅ Model saved as wait_time_model.pkl")
