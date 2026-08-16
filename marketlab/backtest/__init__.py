"""Event-driven daily backtesting."""

from marketlab.backtest.engine import run_daily_backtest
from marketlab.backtest.trade_generation import generate_rebalance_trades

__all__ = ["generate_rebalance_trades", "run_daily_backtest"]
