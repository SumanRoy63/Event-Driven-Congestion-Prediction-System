# =====================================================
# EVENT SEVERITY PREDICTION MODEL
# =====================================================

import warnings
warnings.filterwarnings("ignore")

import os
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    cross_val_score
)

from sklearn.preprocessing import LabelEncoder

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score
)

from sklearn.ensemble import RandomForestClassifier

from xgboost import XGBClassifier

import matplotlib.pyplot as plt
import seaborn as sns


# =====================================================
# LOAD DATA
# =====================================================

def load_data():

    df = pd.read_csv(
        "data/processed/processed_events.csv"
    )

    print("="*50)
    print("Dataset Loaded")
    print(df.shape)
    print("="*50)

    return df


# =====================================================
# PREPARE DATA
# =====================================================

def prepare_data(df):

    TARGET = "priority"

    if TARGET not in df.columns:
        raise ValueError(
            f"{TARGET} column not found!"
        )

    # Encode target

    le = LabelEncoder()

    y = le.fit_transform(
        df[TARGET]
    )

    joblib.dump(
        le,
        "models/priority_encoder.pkl"
    )

    X = df.drop(
        columns=[TARGET]
    )

    # Remove datetime columns

    datetime_cols = []

    for col in X.columns:

        if "date" in col.lower() \
           or "time" in col.lower():

            datetime_cols.append(col)

    print("\nRemoving Date Columns:")
    print(datetime_cols)

    X = X.drop(
        columns=datetime_cols,
        errors="ignore"
    )

    # Remove remaining object columns

    obj_cols = X.select_dtypes(
        include=["object"]
    ).columns

    print("\nRemoving Object Columns:")
    print(list(obj_cols))

    X = X.drop(
        columns=obj_cols,
        errors="ignore"
    )

    return X, y


# =====================================================
# SPLIT DATA
# =====================================================

def split_data(X, y):

    return train_test_split(

        X,

        y,

        test_size=0.2,

        random_state=42,

        stratify=y
    )


# =====================================================
# RANDOM FOREST
# =====================================================

def train_random_forest(
        X_train,
        y_train
):

    rf = RandomForestClassifier(

        n_estimators=400,

        max_depth=12,

        random_state=42,

        n_jobs=-1
    )

    rf.fit(
        X_train,
        y_train
    )

    return rf


# =====================================================
# XGBOOST
# =====================================================

def train_xgboost(
        X_train,
        y_train
):

    xgb = XGBClassifier(

        objective="multi:softprob",

        num_class=len(
            np.unique(y_train)
        ),

        n_estimators=500,

        learning_rate=0.05,

        max_depth=8,

        subsample=0.8,

        colsample_bytree=0.8,

        random_state=42,

        eval_metric="mlogloss"
    )

    xgb.fit(
        X_train,
        y_train
    )

    return xgb


# =====================================================
# EVALUATION
# =====================================================

def evaluate_model(
        model,
        X_test,
        y_test,
        model_name
):

    preds = model.predict(
        X_test
    )

    acc = accuracy_score(
        y_test,
        preds
    )

    f1 = f1_score(
        y_test,
        preds,
        average="weighted"
    )

    print("\n")
    print("="*50)
    print(model_name)
    print("="*50)

    print(
        f"Accuracy : {acc:.4f}"
    )

    print(
        f"Weighted F1 : {f1:.4f}"
    )

    print(
        classification_report(
            y_test,
            preds
        )
    )

    cm = confusion_matrix(
        y_test,
        preds
    )

    plt.figure(
        figsize=(8,6)
    )

    sns.heatmap(

        cm,

        annot=True,

        fmt="d"
    )

    plt.title(
        f"{model_name} Confusion Matrix"
    )

    plt.show()

    return acc


# =====================================================
# CROSS VALIDATION
# =====================================================

def cross_validate_model(
        model,
        X,
        y,
        model_name
):

    cv = StratifiedKFold(

        n_splits=5,

        shuffle=True,

        random_state=42
    )

    scores = cross_val_score(

        model,

        X,

        y,

        cv=cv,

        scoring="accuracy",

        n_jobs=-1
    )

    print("\n")
    print("="*50)

    print(
        f"{model_name} CV Accuracy"
    )

    print("="*50)

    print(scores)

    print(
        f"Mean Score : {scores.mean():.4f}"
    )

    return scores.mean()


# =====================================================
# FEATURE IMPORTANCE
# =====================================================

def plot_feature_importance(
        model,
        X,
        model_name
):

    importance = pd.DataFrame({

        "Feature": X.columns,

        "Importance":
        model.feature_importances_
    })

    importance = (
        importance
        .sort_values(
            by="Importance",
            ascending=False
        )
        .head(20)
    )

    plt.figure(
        figsize=(10,6)
    )

    sns.barplot(

        data=importance,

        x="Importance",

        y="Feature"
    )

    plt.title(
        f"{model_name} Feature Importance"
    )

    plt.show()


# =====================================================
# SAVE MODEL
# =====================================================

def save_model(
        model,
        filename
):

    os.makedirs(
        "models",
        exist_ok=True
    )

    path = f"models/{filename}"

    joblib.dump(
        model,
        path
    )

    print(
        f"Saved: {path}"
    )


# =====================================================
# MAIN
# =====================================================

def main():

    df = load_data()

    X, y = prepare_data(df)

    print("\nFeature Shape:")
    print(X.shape)

    X_train, X_test, y_train, y_test = (
        split_data(X, y)
    )

    # ---------------------------------
    # RANDOM FOREST
    # ---------------------------------

    print(
        "\nTraining Random Forest..."
    )

    rf = train_random_forest(
        X_train,
        y_train
    )

    rf_acc = evaluate_model(
        rf,
        X_test,
        y_test,
        "Random Forest"
    )

    cross_validate_model(
        rf,
        X,
        y,
        "Random Forest"
    )

    plot_feature_importance(
        rf,
        X,
        "Random Forest"
    )

    save_model(
        rf,
        "severity_rf.pkl"
    )

    # ---------------------------------
    # XGBOOST
    # ---------------------------------

    print(
        "\nTraining XGBoost..."
    )

    xgb = train_xgboost(
        X_train,
        y_train
    )

    xgb_acc = evaluate_model(
        xgb,
        X_test,
        y_test,
        "XGBoost"
    )

    cross_validate_model(
        xgb,
        X,
        y,
        "XGBoost"
    )

    plot_feature_importance(
        xgb,
        X,
        "XGBoost"
    )

    save_model(
        xgb,
        "severity_xgb.pkl"
    )

    # ---------------------------------

    print("\n")

    if xgb_acc > rf_acc:

        print(
            "Best Model: XGBoost"
        )

    else:

        print(
            "Best Model: Random Forest"
        )


if __name__ == "__main__":

    main()