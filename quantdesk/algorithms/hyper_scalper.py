"""
Hyper Scalper Strategy
======================

Stratégie de scalping ultra haute fréquence basée sur:
- Micro RSI
- Tick Moving Average
- Price Action patterns
- Volatilité dynamique

Inspiré de GOLD_AI_Pro_Hyper_Scalper.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class HyperScalper(BaseStrategy):
    """
    Stratégie de scalping ultra haute fréquence.
    
    Paramètres:
        symbol: Symbole de trading (ex: XAUUSD, EURUSD)
        lot_size: Taille de lot (0.01 = micro lot)
        tp_pips: Take Profit en pips
        sl_pips: Stop Loss en pips
        max_positions: Nombre maximum de positions simultanées
        max_spread: Spread maximum autorisé (pips)
        rsi_period: Période du RSI
        rsi_upper: Niveau supérieur du RSI (overbought)
        rsi_lower: Niveau inférieur du RSI (oversold)
        tick_ma_period: Période de la moyenne mobile des ticks
        min_volatility: Volatilité minimum requise (pips)
        max_volatility: Volatilité maximum autorisée (pips)
    """
    
    def __init__(
        self,
        symbol: str = "XAUUSD",
        lot_size: float = 0.01,
        tp_pips: float = 1.5,
        sl_pips: float = 2.0,
        max_positions: int = 50,
        max_spread: float = 3.0,
        rsi_period: int = 3,
        rsi_upper: int = 80,
        rsi_lower: int = 20,
        tick_ma_period: int = 5,
        min_volatility: float = 0.3,
        max_volatility: float = 5.0,
        magic_number: int = 20260303
    ):
        super().__init__(symbol, lot_size, magic_number)
        
        # Paramètres de scalping
        self.tp_pips = tp_pips
        self.sl_pips = sl_pips
        self.max_positions = max_positions
        self.max_spread = max_spread
        
        # Paramètres des indicateurs
        self.rsi_period = rsi_period
        self.rsi_upper = rsi_upper
        self.rsi_lower = rsi_lower
        self.tick_ma_period = tick_ma_period
        self.min_volatility = min_volatility
        self.max_volatility = max_volatility
        
        # Indicateurs
        self.indicators = TechnicalIndicators()
        
        # Buffer de ticks
        self.tick_buffer = []
        self.max_tick_buffer = 100
        
        # Statistiques journalières
        self.daily_trades = 0
        self.daily_profit = 0.0
        self.max_daily_trades = 20000
    
    def generate_signal(self, data: pd.DataFrame) -> int:
        """
        Génère un signal de trading basé sur:
        1. Micro RSI
        2. Tick Moving Average
        3. Price Action
        4. Volatilité
        
        Returns:
            1: Signal BUY
            -1: Signal SELL
            0: Pas de signal
        """
        if data is None or len(data) < self.rsi_period + 1:
            return 0
        
        # Vérifier les conditions préalables
        if not self._check_entry_conditions(data):
            return 0
        
        signal = 0
        current_price = data['close'].iloc[-1]
        
        # 1. Signal RSI
        rsi_signal = self._get_rsi_signal(data)
        
        # 2. Signal Tick MA
        tick_ma_signal = self._get_tick_ma_signal(data)
        
        # 3. Signal Momentum
        momentum_signal = self._get_momentum_signal(data)
        
        # Combinaison des signaux
        total_signal = rsi_signal + tick_ma_signal + momentum_signal
        
        if total_signal >= 2:
            signal = 1  # BUY
        elif total_signal <= -2:
            signal = -1  # SELL
        
        return signal
    
    def _check_entry_conditions(self, data: pd.DataFrame) -> bool:
        """Vérifie les conditions d'entrée."""
        
        # 1. Vérifier le nombre de positions
        if len(self.open_positions) >= self.max_positions:
            return False
        
        # 2. Vérifier le nombre de trades journaliers
        if self.daily_trades >= self.max_daily_trades:
            return False
        
        # 3. Vérifier la volatilité
        volatility = self._calculate_volatility(data)
        if volatility < self.min_volatility or volatility > self.max_volatility:
            return False
        
        # 4. Vérifier le spread (simulé)
        spread = self._calculate_spread(data)
        if spread > self.max_spread:
            return False
        
        return True
    
    def _get_rsi_signal(self, data: pd.DataFrame) -> int:
        """Signal basé sur le RSI."""
        rsi = self.indicators.calculate_rsi(data['close'], self.rsi_period)
        
        if rsi is None or pd.isna(rsi.iloc[-1]):
            return 0
        
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < self.rsi_lower:
            return 1  # Oversold -> BUY
        elif current_rsi > self.rsi_upper:
            return -1  # Overbought -> SELL
        
        return 0
    
    def _get_tick_ma_signal(self, data: pd.DataFrame) -> int:
        """Signal basé sur la moyenne mobile des prix."""
        if len(data) < self.tick_ma_period:
            return 0
        
        ma = data['close'].rolling(window=self.tick_ma_period).mean()
        current_price = data['close'].iloc[-1]
        current_ma = ma.iloc[-1]
        
        if pd.isna(current_ma):
            return 0
        
        # Prix au-dessus de la MA
        if current_price > current_ma * 1.0001:
            return 1  # BUY
        # Prix en-dessous de la MA
        elif current_price < current_ma * 0.9999:
            return -1  # SELL
        
        return 0
    
    def _get_momentum_signal(self, data: pd.DataFrame) -> int:
        """Signal basé sur le momentum."""
        if len(data) < 3:
            return 0
        
        # Calculer le momentum sur les 3 dernières bougies
        momentum = data['close'].diff(3).iloc[-1]
        
        if pd.isna(momentum):
            return 0
        
        # Momentum positif
        if momentum > 0:
            return 1  # BUY
        # Momentum négatif
        elif momentum < 0:
            return -1  # SELL
        
        return 0
    
    def _calculate_volatility(self, data: pd.DataFrame) -> float:
        """Calcule la volatilité en pips."""
        if len(data) < 10:
            return 0.0
        
        # Utiliser les 10 dernières bougies
        recent_data = data.tail(10)
        high = recent_data['high'].max()
        low = recent_data['low'].min()
        
        # Convertir en pips (pour l'or, 1 pip = 0.01)
        volatility = (high - low) * 100
        
        return volatility
    
    def _calculate_spread(self, data: pd.DataFrame) -> float:
        """Calcule le spread simulé."""
        # Pour la simulation, on utilise un spread fixe ou basé sur la volatilité
        current_price = data['close'].iloc[-1]
        spread = current_price * 0.0002  # 0.02% spread simulé
        
        return spread * 100  # Convertir en pips
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        """Détermine si une position doit être fermée."""
        
        # Vérifier le Take Profit
        if position.position_type == 'BUY':
            if current_price >= position.take_profit:
                return True
            if current_price <= position.stop_loss:
                return True
        else:  # SELL
            if current_price <= position.take_profit:
                return True
            if current_price >= position.stop_loss:
                return True
        
        # Fermeture anticipée sur petit profit (scalping agressif)
        current_profit = position.get_current_profit(current_price)
        if current_profit >= 0.10:  # $0.10
            # 30% de chance de fermer tôt
            if np.random.random() < 0.30:
                return True
        
        return False
    
    def calculate_sl_tp(self, entry_price: float, position_type: str) -> tuple:
        """Calcule les niveaux de Stop Loss et Take Profit."""
        
        # Convertir pips en prix (pour l'or, 1 pip = 0.01)
        pip_value = 0.01
        
        if position_type == 'BUY':
            stop_loss = entry_price - (self.sl_pips * pip_value)
            take_profit = entry_price + (self.tp_pips * pip_value)
        else:  # SELL
            stop_loss = entry_price + (self.sl_pips * pip_value)
            take_profit = entry_price - (self.tp_pips * pip_value)
        
        return stop_loss, take_profit
    
    def execute_trade(self, signal: int, current_price: float):
        """Execute un trade basé sur le signal."""
        if signal == 0:
            return
        
        position_type = 'BUY' if signal > 0 else 'SELL'
        entry_price = current_price
        
        # Calculer SL et TP
        stop_loss, take_profit = self.calculate_sl_tp(entry_price, position_type)
        
        # Ouvrir la position
        position = self.open_position(
            position_type=position_type,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.daily_trades += 1
        
        return position
    
    def on_new_day(self):
        """Réinitialise les compteurs journaliers."""
        self.daily_trades = 0
        self.daily_profit = 0.0
    
    def get_strategy_info(self) -> Dict:
        """Retourne les informations de la stratégie."""
        info = self.get_statistics()
        info.update({
            'strategy_name': 'Hyper Scalper',
            'symbol': self.symbol,
            'lot_size': self.lot_size,
            'tp_pips': self.tp_pips,
            'sl_pips': self.sl_pips,
            'max_positions': self.max_positions,
            'daily_trades': self.daily_trades,
            'daily_profit': self.daily_profit
        })
        return info
