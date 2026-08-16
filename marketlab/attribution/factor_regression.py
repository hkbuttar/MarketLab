"""Ordinary least-squares factor regression attribution."""

import math


def ols_factor_regression(
    excess_returns: list[float],
    factors: list[list[float]],
    factor_names: list[str],
) -> dict[str, object]:
    """Fit an intercept and factor loadings with classical OLS standard errors."""

    if len(excess_returns) != len(factors):
        raise ValueError("return and factor observations must align")
    columns = len(factor_names) + 1
    if len(excess_returns) <= columns:
        raise ValueError("regression has insufficient observations")
    if any(len(row) != len(factor_names) for row in factors):
        raise ValueError("factor row width does not match factor names")
    design = [[1.0, *row] for row in factors]
    cross_product = [
        [sum(row[i] * row[j] for row in design) for j in range(columns)]
        for i in range(columns)
    ]
    inverse = _inverse(cross_product)
    cross_return = [
        sum(
            row[index] * value
            for row, value in zip(design, excess_returns, strict=True)
        )
        for index in range(columns)
    ]
    coefficients = [
        sum(row[j] * cross_return[j] for j in range(columns)) for row in inverse
    ]
    fitted = [
        sum(
            value * coefficient
            for value, coefficient in zip(row, coefficients, strict=True)
        )
        for row in design
    ]
    residuals = [
        value - estimate for value, estimate in zip(excess_returns, fitted, strict=True)
    ]
    residual_sum_squares = sum(value**2 for value in residuals)
    mean = sum(excess_returns) / len(excess_returns)
    total_sum_squares = sum((value - mean) ** 2 for value in excess_returns)
    variance = residual_sum_squares / (len(excess_returns) - columns)
    standard_errors = [
        math.sqrt(max(0.0, variance * inverse[i][i])) for i in range(columns)
    ]
    names = ["alpha", *factor_names]
    return {
        "observations": len(excess_returns),
        "daily_alpha": coefficients[0],
        "annualized_alpha": coefficients[0] * 252.0,
        "r_squared": (
            1.0 - residual_sum_squares / total_sum_squares if total_sum_squares else 0.0
        ),
        "coefficients": dict(zip(names, coefficients, strict=True)),
        "standard_errors": dict(zip(names, standard_errors, strict=True)),
    }


def _inverse(matrix: list[list[float]]) -> list[list[float]]:
    size = len(matrix)
    augmented = [
        [*row, *(1.0 if index == column else 0.0 for column in range(size))]
        for index, row in enumerate(matrix)
    ]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-14:
            raise ValueError("factor design matrix is singular")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            multiple = augmented[row][column]
            augmented[row] = [
                value - multiple * pivot_value
                for value, pivot_value in zip(
                    augmented[row], augmented[column], strict=True
                )
            ]
    return [row[size:] for row in augmented]
