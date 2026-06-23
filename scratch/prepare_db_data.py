import pandas as pd
import numpy as np
import joblib
import json
import math
import os

def main():
    print("Loading CSV...")
    csv_path = "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
    df = pd.read_csv(csv_path)
    
    print("Initial shape:", df.shape)
    
    # 1. Clean data and handle string NULLs
    df = df.replace("NULL", np.nan)
    df = df.replace("null", np.nan)
    
    # Convert timestamps to datetime in UTC, then convert to IST
    df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
    df['closed_datetime'] = pd.to_datetime(df['closed_datetime'], errors='coerce')
    
    # Drop rows with missing start_datetime or lat/lng
    df = df.dropna(subset=['start_datetime', 'latitude', 'longitude'])
    print("After dropping missing start/coords:", df.shape)
    
    # Convert to Asia/Kolkata timezone
    if df['start_datetime'].dt.tz is None:
        df['start_ist'] = df['start_datetime'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
    else:
        df['start_ist'] = df['start_datetime'].dt.tz_convert('Asia/Kolkata')
    df['hour'] = df['start_ist'].dt.hour
    df['dow'] = df['start_ist'].dt.dayofweek
    df['month'] = df['start_ist'].dt.month
    
    # Deduplicate: same latitude, longitude, and day
    df['date_str'] = df['start_ist'].dt.date.astype(str)
    df = df.drop_duplicates(subset=['latitude', 'longitude', 'date_str', 'event_cause'])
    print("After deduplication:", df.shape)
    
    # Compute duration_hrs
    df['duration_hrs'] = (df['closed_datetime'] - df['start_datetime']).dt.total_seconds() / 3600
    
    # Impute missing duration_hrs using event_cause x priority median
    df['priority'] = df['priority'].fillna('Medium').astype(str)
    df['event_cause'] = df['event_cause'].fillna('Unknown').astype(str)
    
    median_durations = df.groupby(['event_cause', 'priority'])['duration_hrs'].median()
    overall_median = df['duration_hrs'].median()
    if pd.isna(overall_median) or overall_median <= 0:
        overall_median = 4.0 # default fallback
        
    def get_imputed_duration(row):
        val = row['duration_hrs']
        if not pd.isna(val) and val >= 0:
            return min(48.0, val)
        # lookup median
        key = (row['event_cause'], row['priority'])
        if key in median_durations:
            med = median_durations[key]
            if not pd.isna(med) and med >= 0:
                return min(48.0, med)
        return overall_median

    df['duration_hrs_clean'] = df.apply(get_imputed_duration, axis=1)
    
    # Mappings
    df['requires_road_closure_val'] = df['requires_road_closure'].astype(str).str.upper().map(
        {'TRUE': 1, 'FALSE': 0, '1': 1, '0': 0}
    ).fillna(0).astype(int)
    
    # Compute impact_raw
    df['impact_raw'] = (
        0.50 * df['duration_hrs_clean'].clip(0, 24) / 24 +
        0.30 * df['requires_road_closure_val'] +
        0.20 * (df['priority'] == 'High').astype(int)
    )
    
    # Cut to impact_class
    df['impact_class'] = pd.cut(
        df['impact_raw'],
        bins=[-0.01, 0.25, 0.55, 1.05],
        labels=['Low', 'Medium', 'High']
    )
    df['impact_class'] = df['impact_class'].astype(str)
    
    # Load frozen KMeans to assign geo_cluster and extract centroids
    print("Loading KMeans model...")
    kmeans = joblib.load("models/kmeans_spatial_clusterer.pkl")
    
    # Assign geo_cluster
    df['geo_cluster'] = kmeans.predict(df[['latitude', 'longitude']])
    
    # Export cluster centroids
    centroids = []
    for cid, center in enumerate(kmeans.cluster_centers_):
        centroids.append({
            'cluster_id': cid,
            'centroid_lat': float(center[0]),
            'centroid_lng': float(center[1])
        })
        
    # Calculate corridor rolling 24h count in historical events
    df = df.sort_values('start_datetime')
    # Pre-calculate rolling events 24H
    df['corridor_events_24h'] = 0.0
    for corr in df['corridor'].unique():
        corr_df = df[df['corridor'] == corr]
        # Calculate how many events in the past 24 hours for each event
        times = corr_df['start_datetime']
        counts = []
        for t in times:
            # count elements in [t - 24H, t)
            prev_events = corr_df[(corr_df['start_datetime'] >= t - pd.Timedelta('24h')) & (corr_df['start_datetime'] < t)]
            counts.append(float(len(prev_events)))
        df.loc[df['corridor'] == corr, 'corridor_events_24h'] = counts
        
    # Precompute corridor_hour_baseline
    baseline_df = df.groupby(['corridor', 'zone', 'dow', 'hour'])['corridor_events_24h'].mean().reset_index()
    baseline_df.rename(columns={'dow': 'day_of_week', 'corridor_events_24h': 'avg_events_24h'}, inplace=True)
    
    # Convert dataframes to dictionaries for SQL output
    historical_events_records = []
    for _, row in df.iterrows():
        historical_events_records.append({
            'lat': float(row['latitude']),
            'lng': float(row['longitude']),
            'corridor': str(row['corridor']) if not pd.isna(row['corridor']) else 'Non-corridor',
            'zone': str(row['zone']) if not pd.isna(row['zone']) else 'Unknown',
            'police_station': str(row['police_station']) if not pd.isna(row['police_station']) else 'Unknown',
            'junction': str(row['junction']) if not pd.isna(row['junction']) else 'Unknown',
            'event_cause': str(row['event_cause']) if not pd.isna(row['event_cause']) else 'Unknown',
            'start_datetime': row['start_datetime'].isoformat(),
            'impact_class': str(row['impact_class'])
        })
        
    baseline_records = []
    for _, row in baseline_df.iterrows():
        baseline_records.append({
            'corridor': str(row['corridor']) if not pd.isna(row['corridor']) else 'Non-corridor',
            'zone': str(row['zone']) if not pd.isna(row['zone']) else 'Unknown',
            'day_of_week': int(row['day_of_week']),
            'hour': int(row['hour']),
            'avg_events_24h': float(row['avg_events_24h'])
        })
        
    print(f"Generated {len(historical_events_records)} historical events.")
    print(f"Generated {len(centroids)} cluster centroids.")
    print(f"Generated {len(baseline_records)} baseline records.")
    
    # Save to json file for the seeding script
    os.makedirs("scratch", exist_ok=True)
    with open("scratch/db_seed_data.json", "w") as f:
        json.dump({
            'historical_events': historical_events_records,
            'cluster_centroids': centroids,
            'corridor_hour_baseline': baseline_records
        }, f)
    print("Done! Data written to scratch/db_seed_data.json")

if __name__ == "__main__":
    main()
