import pandas as pd
from sklearn.preprocessing import LabelEncoder
import joblib


def create_time_features(df, datetime_column):

    df[datetime_column] = pd.to_datetime(
        df[datetime_column],
        errors="coerce"
    )


    df["hour"] = (
        df[datetime_column].dt.hour
    )

    df["day"] = (
        df[datetime_column].dt.day
    )


    df["day_of_week"] = (
        df[datetime_column].dt.day_name()
    )


    df["month"] = (
        df[datetime_column].dt.month
    )


    df["weekend"] = (
        df[datetime_column]
        .dt.dayofweek
        .isin([5,6])
        .astype(int)
    )


    return df


def encode_categories(df):

    encoders = {}

    categorical_cols = (
        df.select_dtypes(
            include="object"
        ).columns
    )


    for col in categorical_cols:

        encoder = LabelEncoder()

        df[col] = encoder.fit_transform(
            df[col].astype(str)
        )

        encoders[col] = encoder


    joblib.dump(
        encoders,
        "models/encoders.pkl"
    )


    print("Encoders saved")

    return df


def feature_pipeline(df, datetime_column):

    df = create_time_features(
        df,
        datetime_column
    )

    df = encode_categories(df)

    return df

    