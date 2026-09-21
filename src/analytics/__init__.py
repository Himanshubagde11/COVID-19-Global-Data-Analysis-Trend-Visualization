"""Analytics package for COVID-19 epidemiological statistics and time-series modeling."""
from .statistical_analysis import (
    calculate_correlation_matrix,
    calculate_descriptive_stats,
    explain_statistical_metrics,
)
from .time_series import (
    compare_country_trajectories,
    detect_pandemic_waves,
    get_rolling_averages,
)

__all__ = [
    "calculate_correlation_matrix",
    "calculate_descriptive_stats",
    "compare_country_trajectories",
    "detect_pandemic_waves",
    "explain_statistical_metrics",
    "get_rolling_averages",
]
