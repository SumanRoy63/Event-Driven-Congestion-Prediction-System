# ====================================================
# TRAFFIC HOTSPOT DETECTION
# ====================================================

import warnings
warnings.filterwarnings("ignore")

import os
import joblib

import pandas as pd
import numpy as np

from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

import folium

from folium.plugins import HeatMap

import matplotlib.pyplot as plt
import seaborn as sns


# ====================================================
# LOAD DATA
# ====================================================

def load_data():

    df = pd.read_csv(
        "data/processed/processed_events.csv"
    )

    print("="*50)
    print("Dataset Loaded")
    print(df.shape)
    print("="*50)

    return df


# ====================================================
# FIND LAT LONG COLUMNS
# ====================================================

def get_coordinates(df):

    lat_col = None
    lon_col = None

    for col in df.columns:

        if "lat" in col.lower():
            lat_col = col

        if "lon" in col.lower():
            lon_col = col

    if lat_col is None or lon_col is None:

        raise Exception(
            "Latitude / Longitude column not found"
        )

    print(f"Latitude : {lat_col}")
    print(f"Longitude : {lon_col}")

    return lat_col, lon_col


# ====================================================
# PREPARE DATA
# ====================================================

def prepare_data(df, lat_col, lon_col):

    geo_df = df[
        [lat_col, lon_col]
    ].copy()

    geo_df = geo_df.dropna()

    scaler = StandardScaler()

    coords_scaled = scaler.fit_transform(
        geo_df
    )

    return geo_df, coords_scaled


# ====================================================
# DBSCAN
# ====================================================

def run_dbscan(coords_scaled):

    dbscan = DBSCAN(

        eps=0.15,

        min_samples=15
    )

    clusters = dbscan.fit_predict(
        coords_scaled
    )

    return dbscan, clusters


# ====================================================
# KMEANS
# ====================================================

def run_kmeans(coords_scaled):

    kmeans = KMeans(

        n_clusters=10,

        random_state=42,

        n_init=10
    )

    clusters = kmeans.fit_predict(
        coords_scaled
    )

    return kmeans, clusters


# ====================================================
# VISUALIZE CLUSTERS
# ====================================================

def visualize_clusters(
        geo_df,
        clusters,
        title
):

    plt.figure(
        figsize=(10,6)
    )

    plt.scatter(

        geo_df.iloc[:,1],

        geo_df.iloc[:,0],

        c=clusters,

        cmap="tab20",

        alpha=0.7
    )

    plt.title(title)

    plt.xlabel("Longitude")

    plt.ylabel("Latitude")

    # Instead of plt.show(), save the figure so it doesn't block server threads
    os.makedirs("models", exist_ok=True)
    filename = title.replace(' ', '_').lower() + ".png"
    plt.savefig(f"models/{filename}", bbox_inches="tight")
    plt.close()


# ====================================================
# HOTSPOT RANKING
# ====================================================

def hotspot_ranking(
        geo_df,
        clusters
):

    geo_df["cluster"] = clusters

    ranking = (

        geo_df

        .groupby("cluster")

        .size()

        .reset_index(
            name="event_count"
        )

        .sort_values(
            by="event_count",
            ascending=False
        )
    )

    print("\n")
    print("="*50)
    print("HOTSPOT RANKING")
    print("="*50)

    print(ranking.head(10))

    return ranking


# ====================================================
# CREATE HEATMAP
# ====================================================

def create_heatmap(
        geo_df,
        lat_col,
        lon_col
):

    center_lat = (
        geo_df[lat_col]
        .mean()
    )

    center_lon = (
        geo_df[lon_col]
        .mean()
    )

    traffic_map = folium.Map(

        location=[
            center_lat,
            center_lon
        ],

        zoom_start=11
    )

    heat_data = [

        [
            row[lat_col],
            row[lon_col]
        ]

        for index, row
        in geo_df.iterrows()
    ]

    HeatMap(
        heat_data
    ).add_to(
        traffic_map
    )

    os.makedirs(
        "outputs",
        exist_ok=True
    )

    traffic_map.save(
        "outputs/hotspot_heatmap.html"
    )

    print(
        "\nHeatmap Saved:"
    )

    print(
        "outputs/hotspot_heatmap.html"
    )


# ====================================================
# CLUSTER MAP
# ====================================================

def create_cluster_map(
        geo_df,
        lat_col,
        lon_col,
        clusters
):

    geo_df["cluster"] = clusters

    center_lat = (
        geo_df[lat_col]
        .mean()
    )

    center_lon = (
        geo_df[lon_col]
        .mean()
    )

    fmap = folium.Map(

        location=[
            center_lat,
            center_lon
        ],

        zoom_start=11
    )

    for _, row in geo_df.iterrows():

        folium.CircleMarker(

            location=[
                row[lat_col],
                row[lon_col]
            ],

            radius=4,

            popup=f"Cluster {row['cluster']}",

            fill=True

        ).add_to(
            fmap
        )

    fmap.save(
        "outputs/hotspot_map.html"
    )

    print(
        "Cluster Map Saved"
    )


# ====================================================
# SAVE MODELS
# ====================================================

def save_models(
        dbscan,
        kmeans
):

    os.makedirs(
        "models",
        exist_ok=True
    )

    joblib.dump(

        dbscan,

        "models/dbscan_model.pkl"
    )

    joblib.dump(

        kmeans,

        "models/kmeans_model.pkl"
    )

    print(
        "\nModels Saved"
    )


# ====================================================
# MAIN
# ====================================================

def main():

    df = load_data()

    lat_col, lon_col = (
        get_coordinates(df)
    )

    geo_df, coords_scaled = (
        prepare_data(
            df,
            lat_col,
            lon_col
        )
    )

    # ------------------------------
    # DBSCAN
    # ------------------------------

    print(
        "\nRunning DBSCAN..."
    )

    dbscan, dbscan_clusters = (
        run_dbscan(
            coords_scaled
        )
    )

    visualize_clusters(

        geo_df,

        dbscan_clusters,

        "DBSCAN Hotspots"
    )

    # ------------------------------
    # KMEANS
    # ------------------------------

    print(
        "\nRunning KMeans..."
    )

    kmeans, kmeans_clusters = (
        run_kmeans(
            coords_scaled
        )
    )

    visualize_clusters(

        geo_df,

        kmeans_clusters,

        "KMeans Hotspots"
    )

    # ------------------------------
    # HOTSPOT RANKING
    # ------------------------------

    ranking = hotspot_ranking(

        geo_df.copy(),

        kmeans_clusters
    )

    os.makedirs(
        "outputs",
        exist_ok=True
    )

    ranking.to_csv(

        "outputs/hotspot_clusters.csv",

        index=False
    )

    # ------------------------------
    # MAPS
    # ------------------------------

    create_heatmap(

        geo_df,

        lat_col,

        lon_col
    )

    create_cluster_map(

        geo_df,

        lat_col,

        lon_col,

        kmeans_clusters
    )

    # ------------------------------
    # SAVE MODELS
    # ------------------------------

    save_models(

        dbscan,

        kmeans
    )

    print("\n")
    print("="*50)
    print("HOTSPOT DETECTION COMPLETE")
    print("="*50)


if __name__ == "__main__":

    main()
    
