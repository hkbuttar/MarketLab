"""Tests for factor-return parsing and OLS attribution."""

import io
import zipfile

import pytest

from marketlab.attribution.factor_regression import ols_factor_regression
from marketlab.data.downloaders.french import parse_factor_zip


def test_ols_recovers_known_alpha_and_factor_loadings() -> None:
    factors = [[value, value**2] for value in (-0.03, -0.02, -0.01, 0.01, 0.02, 0.03)]
    returns = [0.001 + 1.5 * market - 0.75 * value for market, value in factors]

    result = ols_factor_regression(returns, factors, ["market", "value"])

    assert result["coefficients"]["alpha"] == pytest.approx(0.001)
    assert result["coefficients"]["market"] == pytest.approx(1.5)
    assert result["coefficients"]["value"] == pytest.approx(-0.75)
    assert result["r_squared"] == pytest.approx(1.0)


def test_parse_factor_zip_ignores_descriptions_and_annual_rows() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "factors.csv",
            "Description\n,Mkt-RF,SMB,HML,RMW,CMA,RF\n"
            "20240102,1.0,2.0,3.0,4.0,5.0,0.1\n"
            " Annual Factors: January-December\n2024,1,2,3,4,5,6\n",
        )

    result = parse_factor_zip(buffer.getvalue())

    assert result == {
        "20240102": {
            "Mkt-RF": 1.0,
            "SMB": 2.0,
            "HML": 3.0,
            "RMW": 4.0,
            "CMA": 5.0,
            "RF": 0.1,
        }
    }
