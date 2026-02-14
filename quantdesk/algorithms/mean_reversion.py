"""
Mean Reversion Strategy
========================

Stratégie de retour à la moyenne basée sur:
- Bollinger Bands
- RSI
- Z-Score
- Support/Resistance levels
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class MeanReversionStrategy(BaseStrategy):
    """
    Stratégie de trading basée sur le retour à la moyenne.
    
    Principe: Acheter quand le prix est trop bas (oversold) et vendre
    quand il est trop haut (overbought), en pariant sur un retour à la moyenne.
    
    Paramètres:
        symbol: Symbole de trading
        lot_size: Taille de lot
        bb_period: Période des Bollinger Bands
        bb_std: Nombre d'écarts-types pour les bandes
        rsi_period: Période du RSI
        rsi_oversold: Niveau RSI de survente
        rsi_overbought: Niveau RSI de surachat
        zscore_period: Période pour le calcul du Z-Score
        zscore_threshold: Seuil du Z-Score pour entrée
        atr_period: Période de l'ATR
        atr_multiplier: Multiplicateur de l'ATR pour SL/TP
    """
    
    def __init__(
        self,
        symbol: str = "GBPUSD",
        lot_size: float = 0.01,
        bb_period: int = 20,
        bb_std: float = 2.0,
        rsi_period: int = 14,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70,
        zscore_period: int = 20,
        zscore_threshold: float = 2.0,
        atr_period: int = 14,
        atr_multiplier: float = 1.5,
        magic_number: int = 20260305
    ):
        super().__init__(symbol, lot_size, magic_number)
        
        # Paramètres de la stratégie
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.zscore_period = zscore_period
        self.zscore_threshold = zscore_threshold
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        
        # Indicateurs
        self.indicators = TechnicalIndicators()
        
        # État de la stratégie
        self.current_regime = 'neutral'  # 'oversold', 'overbought', 'neutral'
        self.mean_price = 0.0
    
    def generate_signal(self, data: pd.DataFrame) -> int:
        """
        Génère un signal basé sur:
        1. Position par rapport aux Bollinger Bands
        2. RSI oversold/overbought
        3. Z-Score
        
        Returns:
            1: Signal BUY (prix trop bas, retour à la hausse attendu)
            -1: Signal SELL (prix trop haut, retour à la baisse attendu)
            0: Pas de signal
        """
        min_length = max(self.bb_period, self.rsi_period, self.zscore_period) + 5
        if data is None or len(data) < min_length:
            return 0
        
        signal = 0
        current_price = data['close'].iloc[-1]
        
        # 1. Calculer les Bollinger Bands
        upper_band, middle_band, lower_band = self.indicators.calculate_bollinger_bands(
            data['close'],
            self.bb_period,
            self.bb_std
        )
        
        if upper_band is None:
            return 0
        
        # 2. Calculer le RSI
        rsi = self.indicators.calculate_rsi(data['close'], self.rsi_period)
        
        if rsi is None:
            return 0
        
        # 3. Calculer le Z-Score
        zscore = self._calculate_zscore(data['close'])
        
        # Valeurs actuelles
        current_upper = upper_band.iloc[-1]
        current_middle = middle_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_zscore = zscore.iloc[-1]
        
        self.mean_price = current_middle
        
        # Signal d'ACHAT: Prix près de la bande inférieure + RSI oversold
        if self._check_oversold_conditions(
            current_price,
            current_lower,
            current_rsi,
            current_zscore
        ):
            signal = 1
            self.current_regime = 'oversold'
        
        # Signal de VENTE: Prix près de la bande supérieure + RSI overbought
        elif self._check_overbought_conditions(
            current_price,
            current_upper,
            current_rsi,
            current_zscore
        ):
            signal = -1
            self.current_regime = 'overbought'
        else:
            self.current_regime = 'neutral'
        
        return signal
    
    def _calculate_zscore(self, prices: pd.Series) -> pd.Series:
        """Calcule le Z-Score des prix."""
        mean = prices.rolling(window=self.zscore_period).mean()
        std = prices.rolling(window=self.zscore_period).std()
        
        zscore = (prices - mean) / std
        return zscore
    
    def _check_oversold_conditions(
        self,
        price: float,
        lower_band: float,
        rsi: float,
        zscore: float
    ) -> bool:
        """Vérifie les conditions de survente."""
        
        # Le prix doit être proche ou en-dessous de la bande inférieure
        band_condition = price <= lower_band * 1.001
        
        # RSI doit être en survente
        rsi_condition = rsi < self.rsi_oversold
        
        # Z-Score doit être fortement négatif
        zscore_condition = zscore < -self.zscore_threshold
        
        # Au moins 2 conditions sur 3 doivent être remplies
        conditions_met = sum([band_condition, rsi_condition, zscore_condition])
        
        return conditions_met >= 2
    
    def _check_overbought_conditions(
        self,
        price: float,
        upper_band: float,
        rsi: float,
        zscore: float
    ) -> bool:
        """Vérifie les conditions de surachat."""
        
        # Le prix doit être proche ou au-dessus de la bande supérieure
        band_condition = price >= upper_band * 0.999
        
        # RSI doit être en surachat
        rsi_condition = rsi > self.rsi_overbought
        
        # Z-Score doit être fortement positif
        zscore_condition = zscore > self.zscore_threshold
        
        # Au moins 2 conditions sur 3 doivent être remplies
        conditions_met = sum([band_condition, rsi_condition, zscore_condition])
        
        return conditions_met >= 2
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        """Détermine si une position doit être fermée."""
        
        # Fermeture classique: SL ou TP atteint
        if position.position_type == 'BUY':
            if current_price >= position.take_profit or current_price <= position.stop_loss:
                return True
            
            # Fermeture si le prix revient à la moyenne
            if current_price >= self.mean_price * 0.999:
                return True
        
        else:  # SELL
            if current_price <= position.take_profit or current_price >= position.stop_loss:
                return True
            
            # Fermeture si le prix revient à la moyenne
            if current_price <= self.mean_price * 1.001:
                return True
        
        return False
    
    def calculate_sl_tp(
        self,
        entry_price: float,
        position_type: str,
        atr_value: float
    ) -> Tuple[float, float]:
        """
        Calcule les niveaux de Stop Loss et Take Profit.
        
        Pour le mean reversion:
        - SL: ATR * multiplier (au-delà de la bande)
        - TP: Retour vers la moyenne mobile
        """
        
        # Stop Loss basé sur l'ATR
        sl_distance = atr_value * self.atr_multiplier
        
        # Take Profit: distance vers la moyenne
        if self.mean_price > 0:
            tp_distance = abs(entry_price - self.mean_price)
        else:
            tp_distance = sl_distance * 1.5
        
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
        
        # Calculer l'ATR
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
    
    def get_distance_from_mean(self, current_price: float) -> float:
        """Retourne la distance du prix actuel par rapport à la moyenne."""
        if self.mean_price == 0:
            return 0.0
        
        return ((current_price - self.mean_price) / self.mean_price) * 100
    
    def get_strategy_info(self) -> Dict:
        """Retourne les informations de la stratégie."""
        info = self.get_statistics()
        
        distance_from_mean = 0.0
        if self.current_price > 0 and self.mean_price > 0:
            distance_from_mean = self.get_distance_from_mean(self.current_price)
        
        info.update({
            'strategy_name': 'Mean Reversion',
            'symbol': self.symbol,
            'lot_size': self.lot_size,
            'current_regime': self.current_regime,
            'mean_price': self.mean_price,
            'distance_from_mean_%': distance_from_mean
        })
        return info
