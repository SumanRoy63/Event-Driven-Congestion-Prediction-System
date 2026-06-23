import os
import joblib
import pandas as pd
import json

csv_path = "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
print("CSV Exists:", os.path.exists(csv_path))

if os.path.exists(csv_path):
    df = pd.read_csv(csv_path, nrows=5)
    print("CSV Columns:")
    print(df.columns.tolist())
    print("\nSample Row:")
    print(df.iloc[0].to_dict())

kmeans_path = "models/kmeans_spatial_clusterer.pkl"
if os.path.exists(kmeans_path):
    kmeans = joblib.load(kmeans_path)
    print("\nKMeans Type:", type(kmeans))
    if hasattr(kmeans, "cluster_centers_"):
        print("Centroids shape:", kmeans.cluster_centers_.shape)
        print("Centroids:")
        for idx, center in enumerate(kmeans.cluster_centers_):
            print(f"Cluster {idx}: Lat {center[0]}, Lng {center[1]}")

features_path = "models/model_features.pkl"
if os.path.exists(features_path):
    features = joblib.load(features_path)
    print("\nModel Features:", features)
