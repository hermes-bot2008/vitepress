"""
Algorithmes de Trading
=======================

Ce module contient les différentes stratégies de trading:
- HyperScalper: Scalping ultra haute fréquence
- MomentumStrategy: Trading basé sur le momentum
- MeanReversionStrategy: Stratégie de retour à la moyenne
"""

from quantdesk.algorithms.hyper_scalper import HyperScalper
from quantdesk.algorithms.momentum import MomentumStrategy
from quantdesk.algorithms.mean_reversion import MeanReversionStrategy

__all__ = ["HyperScalper", "MomentumStrategy", "MeanReversionStrategy"]
