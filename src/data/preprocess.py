import pandas as pd
import numpy as np


def clean_data(df):

    print("\nStarting Data Cleaning...")

    # Remove duplicate rows
    before = len(df)

    df = df.drop_duplicates()

    after = len(df)

    print(f"Removed {before-after} duplicate rows")


    # Remove columns having more than 70% missing values
    missing_percent = df.isnull().mean() * 100

    remove_cols = missing_percent[
        missing_percent > 70
    ].index

    df.drop(
        columns=remove_cols,
        inplace=True
    )

    print("Dropped Columns:")
    print(list(remove_cols))


    # Fill categorical missing values
    cat_cols = df.select_dtypes(
        include="object"
    ).columns


    for col in cat_cols:
        df[col] = df[col].fillna("Unknown")


    # Fill numerical values with median
    num_cols = df.select_dtypes(
        include=np.number
    ).columns


    for col in num_cols:
        df[col] = df[col].fillna(
            df[col].median()
        )


    print("Missing values handled successfully")

    return df