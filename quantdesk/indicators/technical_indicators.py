"""
Technical Indicators
====================

Collection d'indicateurs techniques pour l'analyse de marché.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple


class TechnicalIndicators:
    """Classe contenant tous les indicateurs techniques."""
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> Optional[pd.Series]:
        """
        Calcule la Simple Moving Average (SMA).
        
        Args:
            prices: Série de prix
            period: Période de la moyenne
            
        Returns:
            Série contenant la SMA
        """
        if len(prices) < period:
            return None
        
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> Optional[pd.Series]:
        """
        Calcule l'Exponential Moving Average (EMA).
        
        Args:
            prices: Série de prix
            period: Période de la moyenne
            
        Returns:
            Série contenant l'EMA
        """
        if len(prices) < period:
            return None
        
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> Optional[pd.Series]:
        """
        Calcule le Relative Strength Index (RSI).
        
        Args:
            prices: Série de prix
            period: Période du RSI (défaut: 14)
            
        Returns:
            Série contenant le RSI (0-100)
        """
        if len(prices) < period + 1:
            return None
        
        # Calculer les variations de prix
        delta = prices.diff()
        
        # Séparer les gains et les pertes
        gains = delta.where(delta > 0, 0.0)
        losses = -delta.where(delta < 0, 0.0)
        
        # Calculer les moyennes
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()
        
        # Éviter la division par zéro
        rs = avg_gains / avg_losses.replace(0, np.finfo(float).eps)
        
        # Calculer le RSI
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[Optional[pd.Series], Optional[pd.Series], Optional[pd.Series]]:
        """
        Calcule le MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Série de prix
            fast_period: Période rapide (défaut: 12)
            slow_period: Période lente (défaut: 26)
            signal_period: Période du signal (défaut: 9)
            
        Returns:
            Tuple (MACD line, Signal line, Histogram)
        """
        if len(prices) < slow_period + signal_period:
            return None, None, None
        
        # Calculer les EMAs
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
        
        # Ligne MACD
        macd_line = ema_fast - ema_slow
        
        # Ligne de signal
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # Histogramme
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[Optional[pd.Series], Optional[pd.Series], Optional[pd.Series]]:
        """
        Calcule les Bollinger Bands.
        
        Args:
            prices: Série de prix
            period: Période de la moyenne (défaut: 20)
            std_dev: Nombre d'écarts-types (défaut: 2.0)
            
        Returns:
            Tuple (Upper band, Middle band, Lower band)
        """
        if len(prices) < period:
            return None, None, None
        
        # Bande du milieu (SMA)
        middle_band = prices.rolling(window=period).mean()
        
        # Écart-type
        std = prices.rolling(window=period).std()
        
        # Bandes supérieure et inférieure
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def calculate_atr(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> Optional[pd.Series]:
        """
        Calcule l'Average True Range (ATR).
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            period: Période de l'ATR (défaut: 14)
            
        Returns:
            Série contenant l'ATR
        """
        if len(high) < period + 1:
            return None
        
        # Calculer le True Range
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Calculer l'ATR (moyenne mobile du TR)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3
    ) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
        """
        Calcule le Stochastic Oscillator.
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            k_period: Période de %K (défaut: 14)
            d_period: Période de %D (défaut: 3)
            
        Returns:
            Tuple (%K, %D)
        """
        if len(high) < k_period:
            return None, None
        
        # Plus haut et plus bas sur la période
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        # %K
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        
        # %D (SMA de %K)
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return k_percent, d_percent
    
    @staticmethod
    def calculate_adx(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> Optional[pd.Series]:
        """
        Calcule l'Average Directional Index (ADX).
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            period: Période de l'ADX (défaut: 14)
            
        Returns:
            Série contenant l'ADX
        """
        if len(high) < period + 1:
            return None
        
        # Calculer les mouvements directionnels
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        # Calculer le True Range
        tr1 = high - low
        tr2 = np.abs(high - close.shift())
        tr3 = np.abs(low - close.shift())
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Lisser les valeurs
        atr = true_range.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # Calculer l'ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx
    
    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        Calcule l'On-Balance Volume (OBV).
        
        Args:
            close: Série des prix de clôture
            volume: Série des volumes
            
        Returns:
            Série contenant l'OBV
        """
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    @staticmethod
    def calculate_vwap(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series
    ) -> pd.Series:
        """
        Calcule le Volume Weighted Average Price (VWAP).
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            volume: Série des volumes
            
        Returns:
            Série contenant le VWAP
        """
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        
        return vwap
    
    @staticmethod
    def calculate_pivot_points(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series
    ) -> dict:
        """
        Calcule les points pivots et niveaux de support/résistance.
        
        Args:
            high: Prix haut de la période précédente
            low: Prix bas de la période précédente
            close: Prix de clôture de la période précédente
            
        Returns:
            Dictionnaire avec pivot, supports (S1, S2, S3) et résistances (R1, R2, R3)
        """
        pivot = (high + low + close) / 3
        
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)
        
        return {
            'pivot': pivot,
            'r1': r1, 'r2': r2, 'r3': r3,
            's1': s1, 's2': s2, 's3': s3
        }
    
    @staticmethod
    def calculate_ichimoku(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_b_period: int = 52,
        displacement: int = 26
    ) -> dict:
        """
        Calcule l'Ichimoku Cloud.
        
        Returns:
            Dictionnaire avec Tenkan-sen, Kijun-sen, Senkou Span A, Senkou Span B, Chikou Span
        """
        # Tenkan-sen (Conversion Line)
        tenkan_sen = (high.rolling(window=tenkan_period).max() + 
                     low.rolling(window=tenkan_period).min()) / 2
        
        # Kijun-sen (Base Line)
        kijun_sen = (high.rolling(window=kijun_period).max() + 
                    low.rolling(window=kijun_period).min()) / 2
        
        # Senkou Span A (Leading Span A)
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
        
        # Senkou Span B (Leading Span B)
        senkou_span_b = ((high.rolling(window=senkou_b_period).max() + 
                         low.rolling(window=senkou_b_period).min()) / 2).shift(displacement)
        
        # Chikou Span (Lagging Span)
        chikou_span = close.shift(-displacement)
        
        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span
        }
