"""The three supported cross-sectional ranking regressors."""

from typing import Any

from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODEL_NAMES = ("elastic_net", "random_forest", "gradient_boosting")


def create_ranking_model(name: str, *, random_state: int = 1729) -> Pipeline:
    """Create a deterministic estimator with fold-local feature imputation."""

    if name == "elastic_net":
        estimator: Any = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "regressor",
                    ElasticNet(
                        alpha=0.001,
                        l1_ratio=0.5,
                        max_iter=5_000,
                        random_state=random_state,
                    ),
                ),
            ]
        )
    elif name == "random_forest":
        estimator = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "regressor",
                    RandomForestRegressor(
                        n_estimators=200,
                        max_depth=12,
                        min_samples_leaf=20,
                        max_features=0.7,
                        n_jobs=-1,
                        random_state=random_state,
                    ),
                ),
            ]
        )
    elif name == "gradient_boosting":
        estimator = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "regressor",
                    HistGradientBoostingRegressor(
                        learning_rate=0.05,
                        max_iter=200,
                        max_leaf_nodes=31,
                        min_samples_leaf=20,
                        l2_regularization=0.1,
                        early_stopping=False,
                        random_state=random_state,
                    ),
                ),
            ]
        )
    else:
        raise ValueError(f"unsupported ranking model: {name}")
    return estimator


def model_specifications() -> dict[str, dict[str, object]]:
    """Return auditable fixed model families and their research role."""

    return {
        "elastic_net": {
            "family": "regularized linear regression",
            "role": "linear baseline",
            "target": "future cross-sectional return rank",
        },
        "random_forest": {
            "family": "nonlinear bagging",
            "role": "interaction and nonlinear baseline",
            "target": "future cross-sectional return rank",
        },
        "gradient_boosting": {
            "family": "histogram gradient-boosted trees",
            "role": "sequential nonlinear model",
            "target": "future cross-sectional return rank",
        },
    }
