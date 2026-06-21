import os
import joblib
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PROCESSED_CSV = os.path.join(ROOT, 'data', 'processed', 'processed_events.csv')
OUT_DIR = os.path.join(ROOT, 'models')
OUT_PATH = os.path.join(OUT_DIR, 'feature_columns.pkl')

os.makedirs(OUT_DIR, exist_ok=True)

try:
    df = pd.read_csv(PROCESSED_CSV)
except Exception as e:
    df = pd.DataFrame()

numeric_cols = df.select_dtypes(include=['number']).columns.tolist() if not df.empty else []
exclude = ['requires_road_closure', 'priority', 'latitude', 'longitude']
feature_columns = [c for c in numeric_cols if c not in exclude]

# Fallback: if no numeric columns found, try some common columns
if not feature_columns:
    possible = ['speed', 'volume', 'lane_count', 'duration']
    feature_columns = [c for c in possible if c in df.columns]

if not feature_columns:
    # Last fallback: create a placeholder feature list
    feature_columns = ['feature_1']

joblib.dump(feature_columns, OUT_PATH)
print(f'Wrote {OUT_PATH} with {len(feature_columns)} features')
