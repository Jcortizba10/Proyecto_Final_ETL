
import numpy as np
import pandas as pd
from typing import Dict
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

def build_ml_tables(fact: pd.DataFrame) -> pd.DataFrame:
    if "periodo" not in fact.columns:
        fact = fact.copy()
        fact["year"] = pd.to_numeric(fact["year"], errors="coerce")
        fact["month"] = pd.to_numeric(fact["month"], errors="coerce")
        fact = fact.dropna(subset=["year","month"])
        fact["year"] = fact["year"].astype(int)
        fact["month"] = fact["month"].astype(int)
        fact["periodo"] = pd.to_datetime(dict(year=fact["year"], month=fact["month"], day=1))

    model_df = fact.copy()
    model_df["y_pmm1"] = (model_df["om_pmm1"] > 0).astype(int)
    model_df = model_df.sort_values(["equipo","periodo"])

    def add_lag(group: pd.DataFrame, cols, lag: int = 1) -> pd.DataFrame:
        g = group.copy()
        for c in cols:
            g[f"{c}_lag{lag}"] = g[c].shift(lag)
        return g

    lag_cols = ["toneladas_total","om_total","om_pmm1","om_pmm2","dias_om_prom"]
    model_df = (model_df.groupby("equipo", group_keys=False)
                        .apply(lambda g: add_lag(g, lag_cols, lag=1)))
    for c in [f"{c}_lag1" for c in lag_cols]:
        if c in model_df.columns:
            model_df[c] = model_df[c].fillna(0.0)
    return model_df

def train_eval_rf(model_df: pd.DataFrame) -> Dict[str, object]:
    feature_cols = [c for c in model_df.columns if c.endswith("_lag1")] + ["toneladas_total"]
    X = model_df[feature_cols].fillna(0.0)
    y = model_df["y_pmm1"]

    unique_periods = sorted(model_df["periodo"].dropna().unique())
    if len(unique_periods) >= 10:
        cutoff = unique_periods[int(len(unique_periods)*0.9)]
        train_idx = model_df["periodo"] < cutoff
        test_idx = model_df["periodo"] >= cutoff
    else:
        import numpy as np
        train_idx = np.arange(len(model_df)) < int(0.8*len(model_df))
        test_idx = ~train_idx

    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    clf = Pipeline(steps=[
        ("scaler", StandardScaler(with_mean=False)),
        ("rf", RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            random_state=42,
            class_weight="balanced_subsample"
        ))
    ])

    report, cm, importances = None, None, None

    import numpy as np
    if len(np.unique(y_train)) >= 2:
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        report = classification_report(y_test, y_pred, digits=3)
        cm = confusion_matrix(y_test, y_pred)
        importances = pd.DataFrame({
            "feature": X.columns,
            "importance": clf.named_steps["rf"].feature_importances_
        }).sort_values("importance", ascending=False)

    return {"clf": clf, "features": feature_cols, "report": report, "cm": cm, "importances": importances}
