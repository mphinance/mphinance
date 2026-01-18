"""
Strategies package - Each strategy is loaded on-demand when selected.
"""
from typing import List, Dict
from .base import BaseStrategy

# Lazy loading - strategies are only imported when accessed
_strategy_cache: Dict[str, BaseStrategy] = {}

STRATEGY_REGISTRY = {
    'Momentum with Pullback': 'strategies.momentum.MomentumStrategy',
    'Small Cap Multibaggers': 'strategies.small_cap_multibaggers.SmallCapMultibaggersStrategy',
    'Gamma Scan': 'strategies.gamma_scan.GammaScanStrategy',
    'Volatility Squeeze': 'strategies.volatility_squeeze.VolatilitySqueezeStrategy',
    'MEME Screen': 'strategies.meme_scanner.MemeScannerStrategy',
}


def get_strategy_names() -> List[str]:
    """Get list of strategy display names for dropdown."""
    return list(STRATEGY_REGISTRY.keys())


def get_strategy_by_display_name(display_name: str) -> BaseStrategy:
    """Get strategy by its display name. Lazy loads the strategy class."""
    if display_name in _strategy_cache:
        return _strategy_cache[display_name]
    
    if display_name not in STRATEGY_REGISTRY:
        # Default to Momentum if unknown
        display_name = 'Momentum with Pullback'
    
    module_path = STRATEGY_REGISTRY[display_name]
    module_name, class_name = module_path.rsplit('.', 1)
    
    # Dynamic import
    import importlib
    module = importlib.import_module(module_name)
    strategy_class = getattr(module, class_name)
    strategy = strategy_class()
    
    _strategy_cache[display_name] = strategy
    return strategy


def get_strategy(name: str) -> BaseStrategy:
    """Alias for get_strategy_by_display_name."""
    return get_strategy_by_display_name(name)
