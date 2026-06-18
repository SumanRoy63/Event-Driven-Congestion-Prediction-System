# =====================================================
# ROAD CLOSURE PREDICTION MODEL
# =====================================================

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    cross_val_score
)

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix
)

from sklearn.ensemble import RandomForestClassifier

from xgboost import XGBClassifier

import matplotlib.pyplot as plt
import seaborn as sns

import joblib
import os


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

    TARGET = "requires_road_closure"

    # Drop target
    X = df.drop(columns=[TARGET])

    y = df[TARGET]

    # Remove datetime columns
    datetime_cols = X.select_dtypes(
        include=["datetime64[ns]", "datetime64[ns, UTC]"]
    ).columns

    X = X.drop(columns=datetime_cols)

    # Remove remaining string/object columns
    object_cols = X.select_dtypes(
        include=["object"]
    ).columns

    print("\nDropping String Columns:")
    print(list(object_cols))

    X = X.drop(columns=object_cols)

    return X, y


# =====================================================
# TRAIN TEST SPLIT
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
        n_estimators=300,
        max_depth=12,
        min_samples_split=5,
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

        n_estimators=500,

        max_depth=8,

        learning_rate=0.05,

        subsample=0.8,

        colsample_bytree=0.8,

        random_state=42,

        eval_metric="logloss"
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

    probs = model.predict_proba(
        X_test
    )[:,1]

    acc = accuracy_score(
        y_test,
        preds
    )

    prec = precision_score(
        y_test,
        preds
    )

    rec = recall_score(
        y_test,
        preds
    )

    f1 = f1_score(
        y_test,
        preds
    )

    auc = roc_auc_score(
        y_test,
        probs
    )

    print("\n")
    print("="*50)
    print(model_name)
    print("="*50)

    print(
        f"Accuracy : {acc:.4f}"
    )

    print(
        f"Precision : {prec:.4f}"
    )

    print(
        f"Recall : {rec:.4f}"
    )

    print(
        f"F1 Score : {f1:.4f}"
    )

    print(
        f"ROC AUC : {auc:.4f}"
    )

    print("\nClassification Report\n")

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

    plt.figure(figsize=(6,4))

    sns.heatmap(
        cm,
        annot=True,
        fmt="d"
    )

    plt.title(
        f"{model_name} Confusion Matrix"
    )

    plt.show()

    return auc


# =====================================================
# CROSS VALIDATION
# =====================================================

def cross_validation(
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

        scoring="roc_auc",

        n_jobs=-1
    )

    print("\n")
    print("="*50)

    print(
        f"{model_name} CV ROC-AUC"
    )

    print("="*50)

    print(scores)

    print(
        f"Mean CV Score = {scores.mean():.4f}"
    )

    return scores.mean()


# =====================================================
# FEATURE IMPORTANCE
# =====================================================

def feature_importance(
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
            "Importance",
            ascending=False
        )
        .head(20)
    )

    plt.figure(figsize=(10,6))

    sns.barplot(

        data=importance,

        x="Importance",

        y="Feature"
    )

    plt.title(
        f"{model_name} Feature Importance"
    )

    plt.show()

    return importance


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
# MAIN PIPELINE
# =====================================================

def main():

    df = load_data()

    X, y = prepare_data(df)

    X_train, X_test, y_train, y_test = (
        split_data(X, y)
    )

    # ---------------------------------

    print(
        "\nTraining Random Forest..."
    )

    rf = train_random_forest(
        X_train,
        y_train
    )

    rf_auc = evaluate_model(
        rf,
        X_test,
        y_test,
        "Random Forest"
    )

    cross_validation(
        rf,
        X,
        y,
        "Random Forest"
    )

    feature_importance(
        rf,
        X,
        "Random Forest"
    )

    save_model(
        rf,
        "road_closure_rf.pkl"
    )

    # ---------------------------------

    print(
        "\nTraining XGBoost..."
    )

    xgb = train_xgboost(
        X_train,
        y_train
    )

    xgb_auc = evaluate_model(
        xgb,
        X_test,
        y_test,
        "XGBoost"
    )

    cross_validation(
        xgb,
        X,
        y,
        "XGBoost"
    )

    feature_importance(
        xgb,
        X,
        "XGBoost"
    )

    save_model(
        xgb,
        "road_closure_xgb.pkl"
    )

    # ---------------------------------

    print("\n")

    if xgb_auc > rf_auc:

        print(
            "Best Model : XGBoost"
        )

    else:

        print(
            "Best Model : Random Forest"
        )


if __name__ == "__main__":

    main()








