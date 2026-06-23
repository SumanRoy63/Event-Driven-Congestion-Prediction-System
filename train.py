import os
import pandas as pd

from src.data.load_data import load_dataset
from src.data.preprocess import clean_data
from src.data.feature_engineering import feature_pipeline
from src.data.models import road_closure_model, severity_model

# Create required folders
os.makedirs("data/processed", exist_ok=True)
os.makedirs("models", exist_ok=True)

print("="*50)
print("STARTING FULL TRAINING PIPELINE")
print("="*50)

# 1. Load dataset (Make sure this path is correct for your system)
# If your CSV is in the root directory, use just the filename.
file_path = "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
if not os.path.exists(file_path):
    # Fallback to data/raw if it's there
    file_path = "data/raw/Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"

df = load_dataset(file_path)

if df is None:
    print("FATAL ERROR: Could not load the dataset. Check the file path.")
    exit(1)

# 2. Cleaning
df = clean_data(df)

# 3. Feature Engineering & Column Locking
datetime_column = "start_datetime"
df = feature_pipeline(df, datetime_column)

# Save processed dataset (optional, but good for debugging)
output_path = "data/processed/processed_events.csv"
df.to_csv(output_path, index=False)
print(f"Processed features saved to: {output_path}")

print("\n--- Training Road Closure Model ---")
# 4. Train Road Closure Model
X_road, y_road = road_closure_model.prepare_data(df)
X_train_r, X_test_r, y_train_r, y_test_r = road_closure_model.split_data(X_road, y_road)
trained_road_model = road_closure_model.train_xgboost(X_train_r, y_train_r)
road_closure_model.save_model(trained_road_model, "road_closure_xgb.pkl")
print("✅ Road Closure Model trained and saved.")

print("\n--- Training Severity Model ---")
# 5. Train Severity Model
X_sev, y_sev = severity_model.prepare_data(df)
X_train_s, X_test_s, y_train_s, y_test_s = severity_model.split_data(X_sev, y_sev)
trained_severity_model = severity_model.train_xgboost(X_train_s, y_train_s)
severity_model.save_model(trained_severity_model, "severity_xgb.pkl")
print("✅ Severity Model trained and saved.")

print("="*50)
print("PIPELINE COMPLETED SUCCESSFULLY! All .pkl files generated.")
print("="*50)