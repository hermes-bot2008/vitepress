"""
Momentum Strategy
=================

Stratégie basée sur le momentum des prix avec:
- MACD (Moving Average Convergence Divergence)
- RSI (Relative Strength Index)
- Volume analysis
- Trend following
"""

import pandas as pd
import numpy as np
from typing import Dict
from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class MomentumStrategy(BaseStrategy):
    """
    Stratégie de trading basée sur le momentum.
    
    Paramètres:
        symbol: Symbole de trading
        lot_size: Taille de lot
        macd_fast: Période rapide du MACD
        macd_slow: Période lente du MACD
        macd_signal: Période du signal du MACD
        rsi_period: Période du RSI
        rsi_threshold: Seuil du RSI pour confirmation
        atr_period: Période de l'ATR pour le stop loss
        atr_multiplier: Multiplicateur de l'ATR pour le SL
        risk_reward_ratio: Ratio risque/récompense pour le TP
    """
    
    def __init__(
        self,
        symbol: str = "EURUSD",
        lot_size: float = 0.01,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        rsi_period: int = 14,
        rsi_threshold: int = 50,
        atr_period: int = 14,
        atr_multiplier: float = 2.0,
        risk_reward_ratio: float = 2.0,
        magic_number: int = 20260304
    ):
        super().__init__(symbol, lot_size, magic_number)
        
        # Paramètres de la stratégie
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.rsi_period = rsi_period
        self.rsi_threshold = rsi_threshold
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.risk_reward_ratio = risk_reward_ratio
        
        # Indicateurs
        self.indicators = TechnicalIndicators()
        
        # État de la stratégie
        self.trend = 0  # 1: uptrend, -1: downtrend, 0: neutral
        self.last_macd_cross = None
    
    def generate_signal(self, data: pd.DataFrame) -> int:
        """
        Génère un signal basé sur:
        1. Croisement MACD
        2. Confirmation RSI
        3. Direction de la tendance
        4. Volume (si disponible)
        
        Returns:
            1: Signal BUY
            -1: Signal SELL
            0: Pas de signal
        """
        min_length = max(self.macd_slow, self.rsi_period, self.atr_period) + 10
        if data is None or len(data) < min_length:
            return 0
        
        signal = 0
        
        # 1. Calculer le MACD
        macd_line, signal_line, histogram = self.indicators.calculate_macd(
            data['close'],
            self.macd_fast,
            self.macd_slow,
            self.macd_signal
        )
        
        if macd_line is None or len(macd_line) < 2:
            return 0
        
        # 2. Calculer le RSI
        rsi = self.indicators.calculate_rsi(data['close'], self.rsi_period)
        
        if rsi is None:
            return 0
        
        # 3. Détecter le croisement MACD
        macd_cross = self._detect_macd_crossover(macd_line, signal_line)
        
        # 4. Confirmer avec RSI
        current_rsi = rsi.iloc[-1]
        
        # Signal d'achat
        if macd_cross == 1:
            if current_rsi > self.rsi_threshold and current_rsi < 70:
                signal = 1
                self.trend = 1
                self.last_macd_cross = 'bullish'
        
        # Signal de vente
        elif macd_cross == -1:
            if current_rsi < self.rsi_threshold and current_rsi > 30:
                signal = -1
                self.trend = -1
                self.last_macd_cross = 'bearish'
        
        # 5. Vérifier la force du momentum
        if signal != 0:
            histogram_val = histogram.iloc[-1]
            if abs(histogram_val) < 0.0001:  # Momentum trop faible
                signal = 0
        
        return signal
    
    def _detect_macd_crossover(
        self,
        macd_line: pd.Series,
        signal_line: pd.Series
    ) -> int:
        """
        Détecte les croisements du MACD.
        
        Returns:
            1: Croisement haussier (MACD croise signal à la hausse)
            -1: Croisement baissier (MACD croise signal à la baisse)
            0: Pas de croisement
        """
        if len(macd_line) < 2 or len(signal_line) < 2:
            return 0
        
        # Valeurs actuelles et précédentes
        macd_curr = macd_line.iloc[-1]
        macd_prev = macd_line.iloc[-2]
        signal_curr = signal_line.iloc[-1]
        signal_prev = signal_line.iloc[-2]
        
        # Croisement haussier
        if macd_prev < signal_prev and macd_curr > signal_curr:
            return 1
        
        # Croisement baissier
        if macd_prev > signal_prev and macd_curr < signal_curr:
            return -1
        
        return 0
    
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
        
        # Fermeture sur signal inversé (optionnel)
        if self.market_data is not None:
            signal = self.generate_signal(self.market_data)
            if signal != 0:
                if position.position_type == 'BUY' and signal == -1:
                    return True
                if position.position_type == 'SELL' and signal == 1:
                    return True
        
        return False
    
    def calculate_sl_tp(
        self,
        entry_price: float,
        position_type: str,
        atr_value: float
    ) -> tuple:
        """
        Calcule les niveaux de Stop Loss et Take Profit basés sur l'ATR.
        """
        
        # Stop Loss basé sur l'ATR
        sl_distance = atr_value * self.atr_multiplier
        
        # Take Profit basé sur le ratio risque/récompense
        tp_distance = sl_distance * self.risk_reward_ratio
        
        if position_type == 'BUY':
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        else:  # SELL
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance
        
        return stop_loss, take_profit
    
    def execute_trade(self, signal: int, data: pd.DataFrame):
        """Execute un trade basé sur le signal."""
        if signal == 0:
            return
        
        current_price = data['close'].iloc[-1]
        position_type = 'BUY' if signal > 0 else 'SELL'
        
        # Calculer l'ATR pour le stop loss
        atr = self.indicators.calculate_atr(
            data['high'],
            data['low'],
            data['close'],
            self.atr_period
        )
        
        if atr is None or pd.isna(atr.iloc[-1]):
            return
        
        atr_value = atr.iloc[-1]
        
        # Calculer SL et TP
        stop_loss, take_profit = self.calculate_sl_tp(
            current_price,
            position_type,
            atr_value
        )
        
        # Ouvrir la position
        position = self.open_position(
            position_type=position_type,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        return position
    
    def get_strategy_info(self) -> Dict:
        """Retourne les informations de la stratégie."""
        info = self.get_statistics()
        info.update({
            'strategy_name': 'Momentum Strategy',
            'symbol': self.symbol,
            'lot_size': self.lot_size,
            'trend': 'Uptrend' if self.trend == 1 else 'Downtrend' if self.trend == -1 else 'Neutral',
            'last_macd_cross': self.last_macd_cross
        })
        return info
