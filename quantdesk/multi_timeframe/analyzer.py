"""
Multi-Timeframe Analyzer
=========================

Analyse simultanée de plusieurs timeframes pour trading chirurgical.

Hiérarchie:
- 1H: Trend principal (macro direction)
- 15M: Structure de marché (swing structure)
- 5M: Setup de trading (order blocks, FVG)
- 1M: Entry précis (point d'entrée exact)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class MultiTimeframeAnalyzer:
    """
    Analyseur Multi-Timeframe pour entrées chirurgicales.
    
    Usage:
        analyzer = MultiTimeframeAnalyzer()
        analyzer.load_data(data_1m, data_5m, data_15m, data_1h)
        
        signal = analyzer.get_surgical_signal()
        # Returns: {'type': 'BUY', 'confidence': 85, 'entry': 2000.50, ...}
    """
    
    def __init__(self):
        self.data_1m: Optional[pd.DataFrame] = None
        self.data_5m: Optional[pd.DataFrame] = None
        self.data_15m: Optional[pd.DataFrame] = None
        self.data_1h: Optional[pd.DataFrame] = None
        
        self.indicators = TechnicalIndicators()
        
        # Cache des analyses
        self.trend_1h = None
        self.structure_15m = None
        self.setup_5m = None
        self.entry_1m = None
    
    def load_data(
        self,
        data_1m: pd.DataFrame,
        data_5m: pd.DataFrame,
        data_15m: pd.DataFrame,
        data_1h: pd.DataFrame
    ):
        """Charge les données de tous les timeframes."""
        self.data_1m = data_1m
        self.data_5m = data_5m
        self.data_15m = data_15m
        self.data_1h = data_1h
    
    def resample_to_timeframe(self, data: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Ré-échantillonne les données vers un timeframe."""
        resampled = data.resample(timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        return resampled
    
    # ═══════════════════════════════════════════════════════════════
    # LAYER 1: TREND ANALYSIS (1H)
    # ═══════════════════════════════════════════════════════════════
    
    def analyze_trend_1h(self) -> Dict:
        """
        Analyse la tendance sur 1H.
        
        Returns:
            {
                'direction': 1 (up), -1 (down), 0 (neutral),
                'strength': 0-100,
                'emas': {...},
                'adx': float
            }
        """
        if self.data_1h is None or len(self.data_1h) < 200:
            return {'direction': 0, 'strength': 0}
        
        data = self.data_1h
        current_price = data['close'].iloc[-1]
        
        # EMAs pour tendance
        ema50 = self.indicators.calculate_ema(data['close'], 50)
        ema100 = self.indicators.calculate_ema(data['close'], 100)
        ema200 = self.indicators.calculate_ema(data['close'], 200)
        
        if ema50 is None:
            return {'direction': 0, 'strength': 0}
        
        e50 = ema50.iloc[-1]
        e100 = ema100.iloc[-1]
        e200 = ema200.iloc[-1]
        
        # Déterminer direction
        direction = 0
        strength = 0
        
        # Uptrend fort: Prix > EMA50 > EMA100 > EMA200
        if current_price > e50 > e100 > e200:
            direction = 1
            strength = 90
        # Uptrend modéré
        elif current_price > e50 > e100:
            direction = 1
            strength = 70
        elif current_price > e50:
            direction = 1
            strength = 50
        
        # Downtrend fort
        elif current_price < e50 < e100 < e200:
            direction = -1
            strength = 90
        # Downtrend modéré
        elif current_price < e50 < e100:
            direction = -1
            strength = 70
        elif current_price < e50:
            direction = -1
            strength = 50
        
        # ADX pour confirmation
        adx = self.indicators.calculate_adx(
            data['high'], data['low'], data['close'], 14
        )
        
        adx_val = 0
        if adx is not None and not pd.isna(adx.iloc[-1]):
            adx_val = adx.iloc[-1]
            
            # Ajuster strength selon ADX
            if adx_val > 25:
                strength = min(100, strength + 10)
            elif adx_val < 15:
                strength = max(0, strength - 20)
        
        self.trend_1h = {
            'direction': direction,
            'strength': strength,
            'ema50': e50,
            'ema100': e100,
            'ema200': e200,
            'adx': adx_val
        }
        
        return self.trend_1h
    
    # ═══════════════════════════════════════════════════════════════
    # LAYER 2: MARKET STRUCTURE (15M)
    # ═══════════════════════════════════════════════════════════════
    
    def analyze_structure_15m(self) -> Dict:
        """
        Analyse la structure de marché sur 15M.
        
        Détecte:
        - Higher Highs / Higher Lows (HH, HL)
        - Lower Highs / Lower Lows (LH, LL)
        - Structure breaks
        - Key levels
        """
        if self.data_15m is None or len(self.data_15m) < 50:
            return {'structure': 'UNCLEAR', 'quality': 0}
        
        data = self.data_15m.tail(50)
        
        # Trouver les swings
        highs = []
        lows = []
        
        for i in range(2, len(data) - 2):
            # Swing high
            if (data['high'].iloc[i] > data['high'].iloc[i-1] and
                data['high'].iloc[i] > data['high'].iloc[i-2] and
                data['high'].iloc[i] > data['high'].iloc[i+1] and
                data['high'].iloc[i] > data['high'].iloc[i+2]):
                highs.append(data['high'].iloc[i])
            
            # Swing low
            if (data['low'].iloc[i] < data['low'].iloc[i-1] and
                data['low'].iloc[i] < data['low'].iloc[i-2] and
                data['low'].iloc[i] < data['low'].iloc[i+1] and
                data['low'].iloc[i] < data['low'].iloc[i+2]):
                lows.append(data['low'].iloc[i])
        
        structure = 'UNCLEAR'
        quality = 0
        
        if len(highs) >= 2 and len(lows) >= 2:
            # HH et HL = uptrend
            if highs[-1] > highs[-2] and lows[-1] > lows[-2]:
                structure = 'UPTREND_HH_HL'
                quality = 80
            
            # LH et LL = downtrend
            elif highs[-1] < highs[-2] and lows[-1] < lows[-2]:
                structure = 'DOWNTREND_LH_LL'
                quality = 80
            
            # Structure mixte
            else:
                structure = 'RANGING'
                quality = 40
        
        self.structure_15m = {
            'structure': structure,
            'quality': quality,
            'swing_highs': highs[-3:] if len(highs) >= 3 else highs,
            'swing_lows': lows[-3:] if len(lows) >= 3 else lows
        }
        
        return self.structure_15m
    
    # ═══════════════════════════════════════════════════════════════
    # LAYER 3: SETUP DETECTION (5M)
    # ═══════════════════════════════════════════════════════════════
    
    def detect_setup_5m(self) -> Dict:
        """
        Détecte les setups de trading sur 5M.
        
        Types de setup:
        - ORDER_BLOCK: Zone d'accumulation/distribution
        - FVG: Fair Value Gap (imbalance)
        - LIQUIDITY_SWEEP: Piège à stops
        - BREAKOUT: Cassure de niveau
        """
        if self.data_5m is None or len(self.data_5m) < 30:
            return {'type': None, 'quality': 0}
        
        data = self.data_5m
        
        # Order Block Detection
        ob = self._detect_order_block_5m(data)
        if ob['detected']:
            self.setup_5m = {
                'type': 'ORDER_BLOCK',
                'quality': ob['quality'],
                'zone': ob['zone'],
                'direction': ob['direction']
            }
            return self.setup_5m
        
        # Fair Value Gap
        fvg = self._detect_fvg_5m(data)
        if fvg['detected']:
            self.setup_5m = {
                'type': 'FVG',
                'quality': fvg['quality'],
                'zone': fvg['zone'],
                'direction': fvg['direction']
            }
            return self.setup_5m
        
        # Liquidity Sweep
        sweep = self._detect_sweep_5m(data)
        if sweep['detected']:
            self.setup_5m = {
                'type': 'LIQUIDITY_SWEEP',
                'quality': sweep['quality'],
                'direction': sweep['direction']
            }
            return self.setup_5m
        
        self.setup_5m = {'type': None, 'quality': 0}
        return self.setup_5m
    
    def _detect_order_block_5m(self, data: pd.DataFrame) -> Dict:
        """Détecte les order blocks sur 5M."""
        recent = data.tail(20)
        
        for i in range(len(recent) - 2):
            candle = recent.iloc[i]
            next_candle = recent.iloc[i+1]
            
            candle_size = candle['high'] - candle['low']
            avg_size = (recent['high'] - recent['low']).mean()
            
            # Bullish OB: Grosse bougie baissière + reversal haussier
            if (candle['close'] < candle['open'] and
                candle_size > avg_size * 1.5 and
                next_candle['close'] > next_candle['open'] and
                next_candle['close'] > candle['high']):
                
                return {
                    'detected': True,
                    'quality': 75,
                    'zone': {'high': candle['high'], 'low': candle['low']},
                    'direction': 'BULLISH'
                }
            
            # Bearish OB
            if (candle['close'] > candle['open'] and
                candle_size > avg_size * 1.5 and
                next_candle['close'] < next_candle['open'] and
                next_candle['close'] < candle['low']):
                
                return {
                    'detected': True,
                    'quality': 75,
                    'zone': {'high': candle['high'], 'low': candle['low']},
                    'direction': 'BEARISH'
                }
        
        return {'detected': False}
    
    def _detect_fvg_5m(self, data: pd.DataFrame) -> Dict:
        """Détecte les Fair Value Gaps."""
        if len(data) < 3:
            return {'detected': False}
        
        c1 = data.iloc[-3]
        c2 = data.iloc[-2]
        c3 = data.iloc[-1]
        
        # Bullish FVG: c3.low > c1.high
        if c3['low'] > c1['high']:
            gap_size = c3['low'] - c1['high']
            return {
                'detected': True,
                'quality': 70,
                'zone': {'top': c3['low'], 'bottom': c1['high'], 'size': gap_size},
                'direction': 'BULLISH'
            }
        
        # Bearish FVG: c3.high < c1.low
        if c3['high'] < c1['low']:
            gap_size = c1['low'] - c3['high']
            return {
                'detected': True,
                'quality': 70,
                'zone': {'top': c1['low'], 'bottom': c3['high'], 'size': gap_size},
                'direction': 'BEARISH'
            }
        
        return {'detected': False}
    
    def _detect_sweep_5m(self, data: pd.DataFrame) -> Dict:
        """Détecte les liquidity sweeps."""
        recent = data.tail(15)
        
        if len(recent) < 3:
            return {'detected': False}
        
        prev_high = recent['high'].iloc[:-1].max()
        prev_low = recent['low'].iloc[:-1].min()
        
        current = recent.iloc[-1]
        prev = recent.iloc[-2]
        
        # Bullish sweep: Balaye low puis reverse
        if (prev['low'] <= prev_low and
            current['close'] > prev['close'] and
            current['close'] > current['open']):
            
            return {
                'detected': True,
                'quality': 80,
                'direction': 'BULLISH'
            }
        
        # Bearish sweep: Balaye high puis reverse
        if (prev['high'] >= prev_high and
            current['close'] < prev['close'] and
            current['close'] < current['open']):
            
            return {
                'detected': True,
                'quality': 80,
                'direction': 'BEARISH'
            }
        
        return {'detected': False}
    
    # ═══════════════════════════════════════════════════════════════
    # LAYER 4: ENTRY PRECISION (1M)
    # ═══════════════════════════════════════════════════════════════
    
    def find_entry_1m(self) -> Dict:
        """
        Trouve le point d'entrée précis sur 1M.
        
        Confluence factors:
        1. RSI position
        2. Price vs EMA
        3. Volume
        4. Candle pattern
        5. Momentum
        """
        if self.data_1m is None or len(self.data_1m) < 50:
            return {'confluence': 0, 'price': 0}
        
        data = self.data_1m
        current_price = data['close'].iloc[-1]
        
        confluence = 0
        
        # 1. RSI
        rsi = self.indicators.calculate_rsi(data['close'], 14)
        if rsi is not None and not pd.isna(rsi.iloc[-1]):
            rsi_val = rsi.iloc[-1]
            if 30 < rsi_val < 70:  # Zone neutre = bon
                confluence += 1
        
        # 2. EMA position
        ema8 = self.indicators.calculate_ema(data['close'], 8)
        if ema8 is not None and not pd.isna(ema8.iloc[-1]):
            # Prix près de l'EMA = bon point d'entrée
            distance = abs(current_price - ema8.iloc[-1]) / current_price
            if distance < 0.001:  # < 0.1%
                confluence += 1
        
        # 3. Volume
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].rolling(20).mean().iloc[-1]
        if current_volume > avg_volume * 1.2:
            confluence += 1
        
        # 4. Candle pattern
        current = data.iloc[-1]
        if current['close'] > current['open']:  # Bullish candle
            body_size = current['close'] - current['open']
            total_size = current['high'] - current['low']
            if body_size / total_size > 0.6:  # Body dominant
                confluence += 1
        
        # 5. Momentum
        momentum = data['close'].diff(3).iloc[-1]
        if abs(momentum) > 0:  # Momentum présent
            confluence += 1
        
        self.entry_1m = {
            'confluence': confluence,
            'price': current_price,
            'quality': (confluence / 5) * 100
        }
        
        return self.entry_1m
    
    # ═══════════════════════════════════════════════════════════════
    # SIGNAL FINAL
    # ═══════════════════════════════════════════════════════════════
    
    def get_surgical_signal(self) -> Optional[Dict]:
        """
        Génère un signal chirurgical basé sur tous les timeframes.
        
        Returns:
            {
                'type': 'BUY' ou 'SELL',
                'confidence': 0-100,
                'entry_price': float,
                'stop_loss': float,
                'take_profit': float,
                'reasoning': {...}
            }
        """
        # Layer 1: Trend 1H
        trend = self.analyze_trend_1h()
        if trend['direction'] == 0 or trend['strength'] < 50:
            return None  # Pas de tendance claire
        
        # Layer 2: Structure 15M
        structure = self.analyze_structure_15m()
        if structure['quality'] < 40:
            return None  # Structure pas claire
        
        # Layer 3: Setup 5M
        setup = self.detect_setup_5m()
        if setup['type'] is None:
            return None  # Pas de setup valide
        
        # Layer 4: Entry 1M
        entry = self.find_entry_1m()
        if entry['confluence'] < 3:  # Besoin 3/5 minimum
            return None  # Confluence insuffisante
        
        # Vérifier alignement
        # Setup doit être dans même direction que trend
        if trend['direction'] == 1 and setup.get('direction') != 'BULLISH':
            return None
        
        if trend['direction'] == -1 and setup.get('direction') != 'BEARISH':
            return None
        
        # SIGNAL VALIDÉ!
        signal_type = 'BUY' if trend['direction'] == 1 else 'SELL'
        
        # Calculer confidence
        confidence = (
            trend['strength'] * 0.3 +
            structure['quality'] * 0.2 +
            setup['quality'] * 0.3 +
            entry['quality'] * 0.2
        )
        
        # TP/SL basés sur ATR 5M
        atr_5m = self.indicators.calculate_atr(
            self.data_5m['high'],
            self.data_5m['low'],
            self.data_5m['close'],
            14
        )
        
        if atr_5m is None or pd.isna(atr_5m.iloc[-1]):
            atr_value = entry['price'] * 0.01
        else:
            atr_value = atr_5m.iloc[-1]
        
        if signal_type == 'BUY':
            stop_loss = entry['price'] - (2.5 * atr_value)
            take_profit = entry['price'] + (4.0 * atr_value)
        else:
            stop_loss = entry['price'] + (2.5 * atr_value)
            take_profit = entry['price'] - (4.0 * atr_value)
        
        return {
            'type': signal_type,
            'confidence': confidence,
            'entry_price': entry['price'],
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reasoning': {
                'trend_1h': trend,
                'structure_15m': structure,
                'setup_5m': setup,
                'entry_1m': entry
            }
        }
    
    def get_current_market_state(self) -> Dict:
        """Retourne l'état actuel du marché sur tous les TF."""
        return {
            'trend_1h': self.trend_1h,
            'structure_15m': self.structure_15m,
            'setup_5m': self.setup_5m,
            'entry_1m': self.entry_1m
        }
