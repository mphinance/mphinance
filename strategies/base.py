"""
Base strategy class and utilities for stock screening strategies.
"""
from tradingview_screener import Query, col
from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any
import pandas as pd


class BaseStrategy(ABC):
    """Base class for all screening strategies."""
    
    name: str = "Base Strategy"
    description: str = "Override this description"
    
    # Columns to select from TradingView API
    select_columns: List[str] = [
        'name', 'description', 'close', 'change', 'market_cap_basic'
    ]
    
    @abstractmethod
    def build_query(self, params: Dict[str, Any]) -> Query:
        """Build the TradingView query with strategy-specific filters."""
        pass
    
    def post_process(self, df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
        """Optional post-processing after fetching data."""
        return df
    
    def get_default_params(self) -> Dict[str, Any]:
        """Return default parameter values for the sidebar inputs."""
        return {}
    
    def get_param_config(self) -> List[Dict[str, Any]]:
        """Return UI configuration for strategy parameters."""
        return []
