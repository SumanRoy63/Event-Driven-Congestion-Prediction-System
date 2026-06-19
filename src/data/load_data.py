import pandas as pd


def load_dataset(path):
    """
    Load CSV dataset
    """

    try:
        df = pd.read_csv(path)

        print("=" * 50)
        print("Dataset Loaded Successfully")
        print("Shape:", df.shape)
        print("=" * 50)

        return df

    except Exception as e:
        print("Error Loading Dataset:", e)
        return None


if __name__ == "__main__":

    data_path = "data/raw/event_data.csv"

    df = load_dataset(data_path)

    print(df.head())