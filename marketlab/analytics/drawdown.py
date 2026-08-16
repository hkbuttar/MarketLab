"""Drawdown analytics."""


def drawdown_statistics(
    nav: list[float], dates: list[str]
) -> dict[str, float | int | str]:
    """Return maximum peak-to-trough drawdown and recovery duration."""

    if not nav:
        return {
            "maximum_drawdown": 0.0,
            "peak_date": "",
            "trough_date": "",
            "recovery_date": "",
            "duration_days": 0,
        }
    peak = nav[0]
    peak_index = 0
    maximum = 0.0
    maximum_peak = 0
    trough = 0
    for index, value in enumerate(nav):
        if value > peak:
            peak = value
            peak_index = index
        drawdown = value / peak - 1.0 if peak else 0.0
        if drawdown < maximum:
            maximum = drawdown
            maximum_peak = peak_index
            trough = index
    recovery = ""
    duration = len(nav) - 1 - maximum_peak
    peak_value = nav[maximum_peak]
    for index in range(trough + 1, len(nav)):
        if nav[index] >= peak_value:
            recovery = dates[index]
            duration = index - maximum_peak
            break
    return {
        "maximum_drawdown": maximum,
        "peak_date": dates[maximum_peak],
        "trough_date": dates[trough],
        "recovery_date": recovery,
        "duration_days": duration,
    }
