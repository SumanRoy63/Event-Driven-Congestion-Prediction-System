import os

from src.data.load_data import load_dataset
from src.data.preprocess import clean_data
from src.data.feature_engineering import feature_pipeline


# Create required folders
os.makedirs(
    "data/processed",
    exist_ok=True
)

os.makedirs(
    "models",
    exist_ok=True
)


# Load dataset
df = load_dataset(
    "data/raw/event_data.csv"
)


# Cleaning
df = clean_data(df)


# IMPORTANT:
# Change this to your actual
# datetime column name
datetime_column = "start_datetime"


# Feature Engineering
df = feature_pipeline(
    df,
    datetime_column
)


# Save processed dataset

output_path = (
    "data/processed/processed_events.csv"
)


df.to_csv(
    output_path,
    index=False
)


print("="*50)
print("Data Pipeline Completed Successfully")
print(
    "Processed File Saved:",
    output_path
)
print("="*50)
