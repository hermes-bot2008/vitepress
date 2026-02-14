"""
Quantdesk Ultra AI - Trading Platform
======================================

Une plateforme de trading quantitatif avancée avec des algorithmes
de trading haute fréquence et gestion des risques professionnelle.
"""

__version__ = "1.0.0"
__author__ = "Quantdesk AI Team"

from quantdesk.algorithms.hyper_scalper import HyperScalper
from quantdesk.algorithms.momentum import MomentumStrategy
from quantdesk.algorithms.mean_reversion import MeanReversionStrategy
from quantdesk.risk.risk_manager import RiskManager
from quantdesk.backtesting.backtester import Backtester

__all__ = [
    "HyperScalper",
    "MomentumStrategy",
    "MeanReversionStrategy",
    "RiskManager",
    "Backtester",
]
