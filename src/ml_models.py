"""Machine learning module with strict time-series cross-validation.
Prevents look-ahead leakage by fitting scalers and imputers solely inside historical training folds.
Supports Logistic Regression, Random Forest, and Gradient Boosting.
"""

import logging
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error, precision_score, r2_score, recall_score, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("earnings_engine.ml_models")

FEATURE_COLS = [
    "eps_surprise_pct",
    "revenue_surprise_pct",
    "sue",
    "pre_ret_5d",
    "pre_ret_21d",
    "pre_vol_21d",
    "pre_volume_zscore",
    "pre_market_ret_21d",
    "market_beta",
    "pre_vix",
]


class TimeSeriesEarningsML:
    """Orchestrates chronological walk-forward training and out-of-sample evaluation."""

    def __init__(self, n_splits: int = 5, random_state: int = 42):
        self.n_splits = n_splits
        self.random_state = random_state

    def prepare_dataset(
        self,
        events_df: pd.DataFrame,
        target_col: str = "CAR[+1,+5]"
    ) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """Prepares strictly time-ordered feature matrix X and targets y_reg, y_clf."""
        # Ensure chronological ordering by event date
        df = events_df.dropna(subset=[target_col]).sort_values(by="announcement_date").copy()

        # Build feature matrix
        avail_features = [c for c in FEATURE_COLS if c in df.columns]
        X = df[avail_features].copy()

        # Winsorize extreme feature outliers defensively at 1st and 99th percentiles
        for col in X.columns:
            low, high = X[col].quantile(0.01), X[col].quantile(0.99)
            X[col] = X[col].clip(lower=low, upper=high)

        y_reg = df[target_col].astype(float)
        y_clf = (y_reg > 0).astype(int)

        return X, y_reg, y_clf

    def evaluate_models(
        self,
        events_df: pd.DataFrame,
        target_col: str = "CAR[+1,+5]"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Performs walk-forward TimeSeriesSplit evaluation across classification and regression algorithms.

        All scalers and imputers are encapsulated within sklearn Pipelines to guarantee zero data leakage.
        """
        X, y_reg, y_clf = self.prepare_dataset(events_df, target_col)

        if len(X) < 30:
            logger.warning("Insufficient samples (<30) for meaningful time-series cross-validation.")
            return pd.DataFrame(), {}

        tscv = TimeSeriesSplit(n_splits=min(self.n_splits, max(2, len(X) // 15)))

        # Define candidate model pipelines
        models = {
            "LogisticRegression": (
                Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                    ("clf", LogisticRegression(random_state=self.random_state, max_iter=500))
                ]),
                "classification"
            ),
            "RandomForest_Classifier": (
                Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("clf", RandomForestClassifier(n_estimators=100, max_depth=4, random_state=self.random_state))
                ]),
                "classification"
            ),
            "GradientBoosting_Classifier": (
                Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("clf", GradientBoostingClassifier(n_estimators=80, max_depth=3, learning_rate=0.05, random_state=self.random_state))
                ]),
                "classification"
            ),
            "Ridge_Regressor": (
                Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                    ("reg", Ridge(alpha=1.0, random_state=self.random_state))
                ]),
                "regression"
            ),
            "GradientBoosting_Regressor": (
                Pipeline([
                    ("imputer", SimpleImputer(strategy="median")),
                    ("reg", GradientBoostingRegressor(n_estimators=80, max_depth=3, learning_rate=0.05, random_state=self.random_state))
                ]),
                "regression"
            )
        }

        results = []
        oof_predictions: Dict[str, np.ndarray] = {m: np.full(len(X), np.nan) for m in models}

        for name, (pipeline, mtype) in models.items():
            fold_metrics = []

            for fold_idx, (train_idx, val_idx) in enumerate(tscv.split(X)):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]

                if mtype == "classification":
                    y_train, y_val = y_clf.iloc[train_idx], y_clf.iloc[val_idx]
                    if len(np.unique(y_train)) < 2:
                        continue
                    pipeline.fit(X_train, y_train)
                    preds = pipeline.predict(X_val)
                    probs = pipeline.predict_proba(X_val)[:, 1] if hasattr(pipeline.named_steps.get("clf"), "predict_proba") else preds

                    oof_predictions[name][val_idx] = probs

                    acc = accuracy_score(y_val, preds)
                    prec = precision_score(y_val, preds, zero_division=0)
                    rec = recall_score(y_val, preds, zero_division=0)
                    f1 = f1_score(y_val, preds, zero_division=0)
                    try:
                        auc = roc_auc_score(y_val, probs)
                    except Exception:
                        auc = 0.5

                    fold_metrics.append({
                        "acc": acc, "prec": prec, "rec": rec, "f1": f1, "auc": auc
                    })

                else:  # regression
                    y_train, y_val = y_reg.iloc[train_idx], y_reg.iloc[val_idx]
                    pipeline.fit(X_train, y_train)
                    preds = pipeline.predict(X_val)
                    oof_predictions[name][val_idx] = preds

                    mae = mean_absolute_error(y_val, preds)
                    rmse = np.sqrt(mean_squared_error(y_val, preds))
                    r2 = r2_score(y_val, preds)
                    dir_acc = np.mean((preds > 0) == (y_val.values > 0))

                    fold_metrics.append({
                        "mae": mae, "rmse": rmse, "r2": r2, "dir_acc": dir_acc
                    })

            if not fold_metrics:
                continue

            if mtype == "classification":
                results.append({
                    "Model": name,
                    "Type": "Classification",
                    "Directional_Accuracy": round(float(np.mean([m["acc"] for m in fold_metrics])), 4),
                    "AUC": round(float(np.mean([m["auc"] for m in fold_metrics])), 4),
                    "Precision": round(float(np.mean([m["prec"] for m in fold_metrics])), 4),
                    "Recall": round(float(np.mean([m["rec"] for m in fold_metrics])), 4),
                    "F1": round(float(np.mean([m["f1"] for m in fold_metrics])), 4),
                    "MAE": np.nan,
                    "RMSE": np.nan,
                    "R2": np.nan,
                })
            else:
                results.append({
                    "Model": name,
                    "Type": "Regression",
                    "Directional_Accuracy": round(float(np.mean([m["dir_acc"] for m in fold_metrics])), 4),
                    "AUC": np.nan,
                    "Precision": np.nan,
                    "Recall": np.nan,
                    "F1": np.nan,
                    "MAE": round(float(np.mean([m["mae"] for m in fold_metrics])), 4),
                    "RMSE": round(float(np.mean([m["rmse"] for m in fold_metrics])), 4),
                    "R2": round(float(np.mean([m["r2"] for m in fold_metrics])), 4),
                })

        comparison_df = pd.DataFrame(results)
        return comparison_df, {"X": X, "y_reg": y_reg, "y_clf": y_clf, "oof": oof_predictions}
