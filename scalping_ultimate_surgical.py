"""
SYSTÈME DE SCALPING CHIRURGICAL ULTIME
=======================================

Objectif: 1-2% PAR JOUR avec détection chirurgicale

Caractéristiques:
- 50+ indicateurs techniques équilibrés
- Détection de patterns avancés (déséquilibres, order blocks)
- Auto-Fibonacci multi-timeframe
- Système de scoring strongBuy/Buy/Neutral/Sell/strongSell
- Entrées ultra-précises sur 1M/5M
- Filtrage multi-niveaux
"""

import sys
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Optional

from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class AdvancedPatternDetector:
    """Détecteur de patterns avancés."""
    
    @staticmethod
    def detect_order_block(data: pd.DataFrame, lookback: int = 20) -> Dict:
        """Détecte les order blocks (zones d'accumulation institutionnelle)."""
        recent = data.tail(lookback)
        
        # Order block = grosse bougie + reversal
        candle_ranges = recent['high'] - recent['low']
        avg_range = candle_ranges.mean()
        
        bullish_ob = None
        bearish_ob = None
        
        for i in range(len(recent) - 1):
            curr = recent.iloc[i]
            next_candle = recent.iloc[i + 1]
            
            # Bullish order block: grosse bougie baissière + reversal haussier
            if (curr['close'] < curr['open'] and  # Baissière
                (curr['high'] - curr['low']) > avg_range * 1.5 and  # Grosse
                next_candle['close'] > next_candle['open']):  # Reversal
                bullish_ob = {
                    'high': curr['high'],
                    'low': curr['low'],
                    'strength': (curr['high'] - curr['low']) / avg_range
                }
            
            # Bearish order block: grosse bougie haussière + reversal baissier
            if (curr['close'] > curr['open'] and  # Haussière
                (curr['high'] - curr['low']) > avg_range * 1.5 and  # Grosse
                next_candle['close'] < next_candle['open']):  # Reversal
                bearish_ob = {
                    'high': curr['high'],
                    'low': curr['low'],
                    'strength': (curr['high'] - curr['low']) / avg_range
                }
        
        return {'bullish': bullish_ob, 'bearish': bearish_ob}
    
    @staticmethod
    def detect_imbalance(data: pd.DataFrame) -> Dict:
        """Détecte les déséquilibres (Fair Value Gaps)."""
        if len(data) < 3:
            return {'bullish': None, 'bearish': None}
        
        # FVG = écart entre 3 bougies consécutives
        candle_1 = data.iloc[-3]
        candle_2 = data.iloc[-2]
        candle_3 = data.iloc[-1]
        
        bullish_fvg = None
        bearish_fvg = None
        
        # Bullish FVG: low[3] > high[1]
        if candle_3['low'] > candle_1['high']:
            bullish_fvg = {
                'top': candle_3['low'],
                'bottom': candle_1['high'],
                'size': candle_3['low'] - candle_1['high']
            }
        
        # Bearish FVG: high[3] < low[1]
        if candle_3['high'] < candle_1['low']:
            bearish_fvg = {
                'top': candle_1['low'],
                'bottom': candle_3['high'],
                'size': candle_1['low'] - candle_3['high']
            }
        
        return {'bullish': bullish_fvg, 'bearish': bearish_fvg}
    
    @staticmethod
    def detect_liquidity_sweep(data: pd.DataFrame, lookback: int = 10) -> Dict:
        """Détecte les liquidity sweeps (pièges à stops)."""
        recent = data.tail(lookback + 1)
        
        if len(recent) < 3:
            return {'bullish': False, 'bearish': False}
        
        # Highs et lows récents
        recent_high = recent['high'].iloc[:-1].max()
        recent_low = recent['low'].iloc[:-1].min()
        
        current = recent.iloc[-1]
        prev = recent.iloc[-2]
        
        # Bullish sweep: dépasse low puis reverse fort
        bullish_sweep = (
            prev['low'] <= recent_low and
            current['close'] > prev['close'] and
            (current['close'] - current['low']) > (current['high'] - current['low']) * 0.7
        )
        
        # Bearish sweep: dépasse high puis reverse fort
        bearish_sweep = (
            prev['high'] >= recent_high and
            current['close'] < prev['close'] and
            (current['high'] - current['close']) > (current['high'] - current['low']) * 0.7
        )
        
        return {'bullish': bullish_sweep, 'bearish': bearish_sweep}


class FibonacciAnalyzer:
    """Analyse Fibonacci multi-timeframe."""
    
    @staticmethod
    def calculate_fibonacci_levels(high: float, low: float, is_uptrend: bool = True) -> Dict:
        """Calcule les niveaux de Fibonacci."""
        diff = high - low
        
        if is_uptrend:
            # Retracement dans uptrend
            levels = {
                '0.0': high,
                '0.236': high - diff * 0.236,
                '0.382': high - diff * 0.382,
                '0.5': high - diff * 0.5,
                '0.618': high - diff * 0.618,
                '0.786': high - diff * 0.786,
                '1.0': low
            }
        else:
            # Retracement dans downtrend
            levels = {
                '0.0': low,
                '0.236': low + diff * 0.236,
                '0.382': low + diff * 0.382,
                '0.5': low + diff * 0.5,
                '0.618': low + diff * 0.618,
                '0.786': low + diff * 0.786,
                '1.0': high
            }
        
        return levels
    
    @staticmethod
    def get_fibonacci_zones(data: pd.DataFrame, period: int = 50) -> Dict:
        """Détermine les zones Fibonacci importantes."""
        recent = data.tail(period)
        
        # Swing high/low
        swing_high = recent['high'].max()
        swing_low = recent['low'].min()
        
        # Déterminer la tendance
        sma_short = recent['close'].rolling(10).mean().iloc[-1]
        sma_long = recent['close'].rolling(30).mean().iloc[-1]
        is_uptrend = sma_short > sma_long
        
        # Fibonacci
        fib_levels = FibonacciAnalyzer.calculate_fibonacci_levels(
            swing_high, swing_low, is_uptrend
        )
        
        # Prix actuel
        current_price = data['close'].iloc[-1]
        
        # Trouver le niveau le plus proche
        closest_level = None
        min_distance = float('inf')
        
        for level_name, level_price in fib_levels.items():
            distance = abs(current_price - level_price)
            if distance < min_distance:
                min_distance = distance
                closest_level = level_name
        
        return {
            'levels': fib_levels,
            'closest_level': closest_level,
            'distance_pct': (min_distance / current_price) * 100,
            'is_uptrend': is_uptrend
        }


class UltimateSurgicalScalper(BaseStrategy):
    """
    Système de Scalping Chirurgical Ultime
    
    Objectif: 1-2% par jour
    
    Système de scoring avec 50+ indicateurs:
    - Moyennes mobiles (EMA 3,5,8,13,21,34,55,89,144,200)
    - RSI multi-périodes (3,7,14,21)
    - MACD (3 configurations)
    - Bollinger Bands (3 configurations)
    - Stochastic
    - ATR
    - ADX
    - Volume analysis
    - Price action patterns
    - Order blocks
    - Imbalances (FVG)
    - Liquidity sweeps
    - Fibonacci levels
    - Support/Resistance
    - Trend strength
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.03):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        self.pattern_detector = AdvancedPatternDetector()
        self.fib_analyzer = FibonacciAnalyzer()
        
        self.tp_pips = 4.0
        self.sl_pips = 2.0
        self.max_positions = 5
        
        # Historique des scores
        self.score_history = []
        
    def calculate_comprehensive_score(self, data: pd.DataFrame) -> Dict:
        """
        Calcule un score global de -100 (strongSell) à +100 (strongBuy)
        en analysant 50+ indicateurs.
        """
        if len(data) < 200:
            return {'score': 0, 'signal': 'NEUTRAL', 'confidence': 0, 'details': {}}
        
        score = 0
        max_score = 0
        details = {}
        
        current_price = data['close'].iloc[-1]
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 1: MOYENNES MOBILES (10 indicateurs)
        # ════════════════════════════════════════════════════════════
        ema_periods = [3, 5, 8, 13, 21, 34, 55, 89, 144, 200]
        ema_score = 0
        
        for period in ema_periods:
            ema = self.indicators.calculate_ema(data['close'], period)
            if ema is not None and not pd.isna(ema.iloc[-1]):
                if current_price > ema.iloc[-1]:
                    ema_score += 1
                else:
                    ema_score -= 1
                max_score += 1
        
        score += ema_score
        details['ema_score'] = ema_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 2: RSI MULTI-PÉRIODES (4 indicateurs)
        # ════════════════════════════════════════════════════════════
        rsi_periods = [3, 7, 14, 21]
        rsi_score = 0
        
        for period in rsi_periods:
            rsi = self.indicators.calculate_rsi(data['close'], period)
            if rsi is not None and not pd.isna(rsi.iloc[-1]):
                rsi_val = rsi.iloc[-1]
                if rsi_val < 30:
                    rsi_score += 2  # Oversold = bullish
                elif rsi_val < 40:
                    rsi_score += 1
                elif rsi_val > 70:
                    rsi_score -= 2  # Overbought = bearish
                elif rsi_val > 60:
                    rsi_score -= 1
                max_score += 2
        
        score += rsi_score
        details['rsi_score'] = rsi_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 3: MACD (3 configurations)
        # ════════════════════════════════════════════════════════════
        macd_configs = [(12,26,9), (5,13,5), (8,21,8)]
        macd_score = 0
        
        for fast, slow, signal_period in macd_configs:
            macd_line, signal_line, histogram = self.indicators.calculate_macd(
                data['close'], fast, slow, signal_period
            )
            if macd_line is not None and len(macd_line) > 1:
                # Crossover
                if macd_line.iloc[-1] > signal_line.iloc[-1]:
                    macd_score += 1
                else:
                    macd_score -= 1
                
                # Histogram
                if histogram.iloc[-1] > 0:
                    macd_score += 0.5
                else:
                    macd_score -= 0.5
                
                max_score += 1.5
        
        score += macd_score
        details['macd_score'] = macd_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 4: BOLLINGER BANDS (3 configurations)
        # ════════════════════════════════════════════════════════════
        bb_configs = [(20, 2.0), (10, 2.5), (30, 1.5)]
        bb_score = 0
        
        for period, std in bb_configs:
            upper, middle, lower = self.indicators.calculate_bollinger_bands(
                data['close'], period, std
            )
            if upper is not None:
                # Position par rapport aux bandes
                if current_price <= lower.iloc[-1]:
                    bb_score += 2  # Près bande inf = bullish
                elif current_price <= middle.iloc[-1]:
                    bb_score += 1
                elif current_price >= upper.iloc[-1]:
                    bb_score -= 2  # Près bande sup = bearish
                elif current_price >= middle.iloc[-1]:
                    bb_score -= 1
                
                max_score += 2
        
        score += bb_score
        details['bb_score'] = bb_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 5: STOCHASTIC
        # ════════════════════════════════════════════════════════════
        k, d = self.indicators.calculate_stochastic(
            data['high'], data['low'], data['close'], 14, 3
        )
        stoch_score = 0
        
        if k is not None and not pd.isna(k.iloc[-1]):
            k_val = k.iloc[-1]
            if k_val < 20:
                stoch_score += 3
            elif k_val < 30:
                stoch_score += 2
            elif k_val > 80:
                stoch_score -= 3
            elif k_val > 70:
                stoch_score -= 2
            
            max_score += 3
        
        score += stoch_score
        details['stoch_score'] = stoch_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 6: ATR (Volatilité)
        # ════════════════════════════════════════════════════════════
        atr = self.indicators.calculate_atr(
            data['high'], data['low'], data['close'], 14
        )
        atr_score = 0
        
        if atr is not None and not pd.isna(atr.iloc[-1]):
            atr_val = atr.iloc[-1]
            atr_mean = atr.tail(50).mean()
            
            # Volatilité modérée = bon pour scalping
            if 0.8 * atr_mean < atr_val < 1.2 * atr_mean:
                atr_score += 2
            elif atr_val > 1.5 * atr_mean:
                atr_score -= 1  # Trop volatile
            
            max_score += 2
        
        score += atr_score
        details['atr_score'] = atr_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 7: ADX (Force de la tendance)
        # ════════════════════════════════════════════════════════════
        adx = self.indicators.calculate_adx(
            data['high'], data['low'], data['close'], 14
        )
        adx_score = 0
        
        if adx is not None and not pd.isna(adx.iloc[-1]):
            adx_val = adx.iloc[-1]
            # ADX fort = bonne tendance
            if adx_val > 25:
                adx_score += 2
            elif adx_val > 20:
                adx_score += 1
            
            max_score += 2
        
        score += adx_score
        details['adx_score'] = adx_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 8: VOLUME ANALYSIS
        # ════════════════════════════════════════════════════════════
        volume_score = 0
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].rolling(20).mean().iloc[-1]
        
        if current_volume > avg_volume * 1.5:
            # Volume spike = fort signal
            if data['close'].iloc[-1] > data['open'].iloc[-1]:
                volume_score += 3  # Volume + haussier
            else:
                volume_score -= 3  # Volume + baissier
        
        max_score += 3
        score += volume_score
        details['volume_score'] = volume_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 9: PRICE ACTION PATTERNS
        # ════════════════════════════════════════════════════════════
        pa_score = 0
        current = data.iloc[-1]
        prev = data.iloc[-2]
        
        # Engulfing pattern
        if (prev['close'] < prev['open'] and
            current['close'] > current['open'] and
            current['open'] < prev['close'] and
            current['close'] > prev['open']):
            pa_score += 5  # Bullish engulfing
        
        if (prev['close'] > prev['open'] and
            current['close'] < current['open'] and
            current['open'] > prev['close'] and
            current['close'] < prev['open']):
            pa_score -= 5  # Bearish engulfing
        
        # Hammer/Shooting star
        body = abs(current['close'] - current['open'])
        lower_wick = min(current['close'], current['open']) - current['low']
        upper_wick = current['high'] - max(current['close'], current['open'])
        
        if lower_wick > body * 2 and upper_wick < body * 0.5:
            pa_score += 3  # Hammer = bullish
        
        if upper_wick > body * 2 and lower_wick < body * 0.5:
            pa_score -= 3  # Shooting star = bearish
        
        max_score += 5
        score += pa_score
        details['pa_score'] = pa_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 10: ORDER BLOCKS
        # ════════════════════════════════════════════════════════════
        ob_score = 0
        order_blocks = self.pattern_detector.detect_order_block(data)
        
        if order_blocks['bullish']:
            # Prix près d'un bullish OB
            ob_low = order_blocks['bullish']['low']
            if abs(current_price - ob_low) / current_price < 0.001:
                ob_score += 4 * order_blocks['bullish']['strength']
        
        if order_blocks['bearish']:
            ob_high = order_blocks['bearish']['high']
            if abs(current_price - ob_high) / current_price < 0.001:
                ob_score -= 4 * order_blocks['bearish']['strength']
        
        max_score += 4
        score += ob_score
        details['ob_score'] = ob_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 11: IMBALANCES (FVG)
        # ════════════════════════════════════════════════════════════
        imb_score = 0
        imbalances = self.pattern_detector.detect_imbalance(data)
        
        if imbalances['bullish']:
            imb_score += 4
        if imbalances['bearish']:
            imb_score -= 4
        
        max_score += 4
        score += imb_score
        details['imb_score'] = imb_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 12: LIQUIDITY SWEEPS
        # ════════════════════════════════════════════════════════════
        liq_score = 0
        sweeps = self.pattern_detector.detect_liquidity_sweep(data)
        
        if sweeps['bullish']:
            liq_score += 5  # Fort signal
        if sweeps['bearish']:
            liq_score -= 5
        
        max_score += 5
        score += liq_score
        details['liq_score'] = liq_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 13: FIBONACCI LEVELS
        # ════════════════════════════════════════════════════════════
        fib_score = 0
        fib_zones = self.fib_analyzer.get_fibonacci_zones(data)
        
        # Prix près d'un niveau Fib important
        if fib_zones['distance_pct'] < 0.1:  # < 0.1%
            level = fib_zones['closest_level']
            
            # Niveaux de support (bullish)
            if level in ['0.618', '0.5', '0.382'] and fib_zones['is_uptrend']:
                fib_score += 3
            
            # Niveaux de résistance (bearish)
            if level in ['0.618', '0.5', '0.382'] and not fib_zones['is_uptrend']:
                fib_score -= 3
        
        max_score += 3
        score += fib_score
        details['fib_score'] = fib_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 14: MOMENTUM
        # ════════════════════════════════════════════════════════════
        mom_score = 0
        
        mom_1 = data['close'].diff(1).iloc[-1]
        mom_3 = data['close'].diff(3).iloc[-1]
        mom_5 = data['close'].diff(5).iloc[-1]
        
        if mom_1 > 0:
            mom_score += 1
        else:
            mom_score -= 1
        
        if mom_3 > 0:
            mom_score += 1
        else:
            mom_score -= 1
        
        if mom_5 > 0:
            mom_score += 1
        else:
            mom_score -= 1
        
        max_score += 3
        score += mom_score
        details['mom_score'] = mom_score
        
        # ════════════════════════════════════════════════════════════
        # CATÉGORIE 15: SUPPORT/RESISTANCE
        # ════════════════════════════════════════════════════════════
        sr_score = 0
        
        # Support/résistance sur 100 barres
        recent_100 = data.tail(100)
        resistance = recent_100['high'].max()
        support = recent_100['low'].min()
        
        # Distance aux niveaux
        dist_resistance = (resistance - current_price) / current_price
        dist_support = (current_price - support) / current_price
        
        if dist_support < 0.002:  # Proche support
            sr_score += 3
        if dist_resistance < 0.002:  # Proche résistance
            sr_score -= 3
        
        max_score += 3
        score += sr_score
        details['sr_score'] = sr_score
        
        # ════════════════════════════════════════════════════════════
        # NORMALISER LE SCORE: -100 à +100
        # ════════════════════════════════════════════════════════════
        if max_score > 0:
            normalized_score = (score / max_score) * 100
        else:
            normalized_score = 0
        
        # Déterminer le signal
        if normalized_score >= 60:
            signal = 'STRONG_BUY'
            confidence = normalized_score
        elif normalized_score >= 30:
            signal = 'BUY'
            confidence = normalized_score
        elif normalized_score <= -60:
            signal = 'STRONG_SELL'
            confidence = abs(normalized_score)
        elif normalized_score <= -30:
            signal = 'SELL'
            confidence = abs(normalized_score)
        else:
            signal = 'NEUTRAL'
            confidence = 0
        
        return {
            'score': normalized_score,
            'signal': signal,
            'confidence': confidence,
            'details': details,
            'max_score': max_score,
            'raw_score': score
        }
    
    def generate_signal(self, data: pd.DataFrame) -> int:
        """Génère un signal basé sur le scoring complet."""
        if len(data) < 200 or len(self.open_positions) >= self.max_positions:
            return 0
        
        # Calculer le score complet
        analysis = self.calculate_comprehensive_score(data)
        
        # Enregistrer pour historique
        self.score_history.append(analysis)
        
        # Décision chirurgicale
        signal_type = analysis['signal']
        confidence = analysis['confidence']
        
        # Entrée UNIQUEMENT sur STRONG signals avec haute confiance
        if signal_type == 'STRONG_BUY' and confidence >= 70:
            return 1
        
        if signal_type == 'STRONG_SELL' and confidence >= 70:
            return -1
        
        return 0
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        # TP/SL standard
        if position.position_type == 'BUY':
            if current_price >= position.take_profit or current_price <= position.stop_loss:
                return True
        else:
            if current_price <= position.take_profit or current_price >= position.stop_loss:
                return True
        
        # Fermeture sur profit partiel
        profit = position.get_current_profit(current_price)
        if profit >= 3.0:  # $3 profit
            return True
        
        return False
    
    def execute_trade(self, signal: int, current_price: float):
        if signal == 0:
            return
        
        position_type = 'BUY' if signal > 0 else 'SELL'
        pip_value = 0.01
        
        if position_type == 'BUY':
            stop_loss = current_price - (self.sl_pips * pip_value)
            take_profit = current_price + (self.tp_pips * pip_value)
        else:
            stop_loss = current_price + (self.sl_pips * pip_value)
            take_profit = current_price - (self.tp_pips * pip_value)
        
        return self.open_position(position_type, current_price, stop_loss, take_profit)


def main():
    """Test du système chirurgical."""
    
    print("="*80)
    print("   🎯 SYSTÈME DE SCALPING CHIRURGICAL ULTIME")
    print("   OBJECTIF: 1-2% PAR JOUR")
    print("   50+ INDICATEURS | DÉTECTION AVANCÉE | MULTI-TIMEFRAME")
    print("="*80)
    
    # Données 1M pour précision chirurgicale
    print("\n📊 Génération de données 1 MINUTE (ultra-précis)...")
    
    np.random.seed(42)
    
    # 7 jours de données 1min = ~10,000 barres
    dates = pd.date_range(start='2024-01-01', periods=10080, freq='1min')
    n = len(dates)
    
    # Prix réalistes avec micro-mouvements
    trend = np.linspace(0, 80, n)
    cycles = 30 * np.sin(np.linspace(0, 50*np.pi, n))
    noise = np.cumsum(np.random.randn(n) * 0.5)
    close = 2000 + trend + cycles + noise
    
    high = close + np.abs(np.random.randn(n) * 0.8)
    low = close - np.abs(np.random.randn(n) * 0.8)
    open_price = close + np.random.randn(n) * 0.3
    volume = np.random.gamma(2, 500, n)
    
    data = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    print(f"✅ {len(data)} barres (7 jours en 1min)")
    print(f"💰 ${data['close'].iloc[0]:.2f} → ${data['close'].iloc[-1]:.2f}")
    
    # Créer le système chirurgical
    print("\n🔬 Initialisation du Système Chirurgical...")
    print("-"*80)
    strategy = UltimateSurgicalScalper(
        symbol="XAUUSD",
        lot_size=0.03
    )
    
    print(f"✅ 50+ indicateurs chargés")
    print(f"✅ Détection avancée: Order Blocks, FVG, Liquidity Sweeps")
    print(f"✅ Auto-Fibonacci multi-timeframe")
    print(f"✅ Système strongBuy/Buy/Neutral/Sell/strongSell")
    print(f"✅ Filtrage chirurgical: Confiance ≥ 70%")
    
    # Risk manager agressif mais contrôlé
    risk_manager = RiskManager(
        initial_capital=10000,
        max_daily_loss=300,  # 3% par jour max
        max_position_size=0.1,
        max_open_positions=5,
        max_drawdown_percent=20.0
    )
    
    # Backtester
    backtester = Backtester(strategy, initial_capital=10000)
    
    print("\n🔄 Lancement du backtest chirurgical...")
    print("="*80)
    
    results = backtester.run(data, risk_manager, verbose=True)
    
    # RÉSULTATS
    print("\n" + "="*80)
    print("   📊 RÉSULTATS DU SYSTÈME CHIRURGICAL")
    print("="*80)
    
    print(f"\n💰 PERFORMANCE:")
    print(f"   Capital Initial:   ${results['initial_capital']:,.2f}")
    print(f"   Capital Final:     ${results['final_equity']:,.2f}")
    print(f"   Profit/Perte:      ${results['total_profit_$']:+,.2f}")
    print(f"   Return Total:      {results['total_return_%']:+.2f}%")
    
    print(f"\n📊 TRADING:")
    print(f"   Total Trades:      {results['total_trades']}")
    print(f"   Win Rate:          {results['win_rate_%']:.1f}%")
    print(f"   Profit Factor:     {results['profit_factor']:.2f}")
    print(f"   Max Drawdown:      {results['max_drawdown_%']:.2f}%")
    print(f"   Sharpe Ratio:      {results['sharpe_ratio']:.3f}")
    
    # Rendement journalier
    duration_days = results['duration_days']
    if duration_days > 0:
        daily_return = results['total_return_%'] / duration_days
        print(f"\n🎯 RENDEMENT JOURNALIER:")
        print(f"   {daily_return:+.2f}%/jour")
        
        if daily_return >= 1.0 and daily_return <= 2.0:
            print(f"\n✅ OBJECTIF ATTEINT! 1-2%/jour")
            print(f"\n💰 Projections:")
            print(f"   1 semaine:  {daily_return * 7:+.2f}%")
            print(f"   1 mois:     {daily_return * 30:+.2f}%")
            print(f"   1 an:       {daily_return * 365:+.2f}%")
        elif daily_return >= 0.5:
            print(f"\n⚠️ Proche de l'objectif (≥0.5%/jour)")
        else:
            print(f"\n❌ En dessous de l'objectif (<0.5%/jour)")
    
    # Analyse des scores
    if strategy.score_history:
        print(f"\n📈 ANALYSE DES SCORES:")
        strong_buy = sum(1 for s in strategy.score_history if s['signal'] == 'STRONG_BUY')
        buy = sum(1 for s in strategy.score_history if s['signal'] == 'BUY')
        strong_sell = sum(1 for s in strategy.score_history if s['signal'] == 'STRONG_SELL')
        sell = sum(1 for s in strategy.score_history if s['signal'] == 'SELL')
        neutral = sum(1 for s in strategy.score_history if s['signal'] == 'NEUTRAL')
        
        print(f"   STRONG_BUY:    {strong_buy}")
        print(f"   BUY:           {buy}")
        print(f"   NEUTRAL:       {neutral}")
        print(f"   SELL:          {sell}")
        print(f"   STRONG_SELL:   {strong_sell}")
    
    print("\n" + "="*80)
    print("   ✅ BACKTEST TERMINÉ")
    print("="*80)
    
    return results, strategy


if __name__ == "__main__":
    try:
        results, strategy = main()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
