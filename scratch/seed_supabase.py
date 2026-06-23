import json
import requests
import sys

def main():
    print("Loading seed data...")
    try:
        with open("scratch/db_seed_data.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: scratch/db_seed_data.json not found. Run prepare_db_data.py first.")
        sys.exit(1)
        
    from dotenv import load_dotenv
    import os
    load_dotenv()
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    # Modern publishable key
    API_KEY = os.environ.get("SUPABASE_KEY")
    
    headers = {
        "apikey": API_KEY,
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # 1. Seed cluster_centroids
    print("Seeding cluster_centroids...")
    centroids = data['cluster_centroids']
    url = f"{SUPABASE_URL}/rest/v1/cluster_centroids"
    # Delete existing centroids first
    requests.delete(url, headers=headers)
    
    res = requests.post(url, json=centroids, headers=headers)
    if res.status_code not in [200, 201, 204]:
        print(f"Failed to seed cluster_centroids: {res.text}")
        sys.exit(1)
    print("cluster_centroids seeded successfully!")
    
    # 2. Seed corridor_hour_baseline in batches of 500
    print("Seeding corridor_hour_baseline...")
    baseline = data['corridor_hour_baseline']
    url = f"{SUPABASE_URL}/rest/v1/corridor_hour_baseline"
    requests.delete(url, headers=headers)
    
    batch_size = 500
    for i in range(0, len(baseline), batch_size):
        batch = baseline[i:i+batch_size]
        res = requests.post(url, json=batch, headers=headers)
        if res.status_code not in [200, 201, 204]:
            print(f"Failed to seed corridor_hour_baseline batch starting at {i}: {res.text}")
            sys.exit(1)
    print("corridor_hour_baseline seeded successfully!")
    
    # 3. Seed historical_events in batches of 500
    print("Seeding historical_events...")
    events = data['historical_events']
    url = f"{SUPABASE_URL}/rest/v1/historical_events"
    requests.delete(url, headers=headers)
    
    for i in range(0, len(events), batch_size):
        batch = events[i:i+batch_size]
        res = requests.post(url, json=batch, headers=headers)
        if res.status_code not in [200, 201, 204]:
            print(f"Failed to seed historical_events batch starting at {i}: {res.text}")
            sys.exit(1)
    print("historical_events seeded successfully!")
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    main()
