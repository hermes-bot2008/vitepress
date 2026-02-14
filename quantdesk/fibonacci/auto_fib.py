"""
Auto-Fibonacci Multi-Timeframe
================================

Calcul automatique des niveaux de Fibonacci sur plusieurs timeframes.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


class AutoFibonacci:
    """
    Analyse Fibonacci automatique multi-timeframe.
    
    Détecte automatiquement:
    - Swing highs/lows
    - Niveaux de Fibonacci
    - Confluences entre timeframes
    - Zones de réaction attendues
    """
    
    def __init__(self):
        self.fib_ratios = {
            '0.0': 0.0,
            '0.236': 0.236,
            '0.382': 0.382,
            '0.5': 0.5,
            '0.618': 0.618,  # Golden ratio
            '0.786': 0.786,
            '1.0': 1.0,
            '1.272': 1.272,  # Extension
            '1.618': 1.618,  # Extension
            '2.0': 2.0,
            '2.618': 2.618
        }
    
    def find_swing_high(self, data: pd.DataFrame, lookback: int = 20) -> Optional[float]:
        """Trouve le swing high sur une période."""
        if len(data) < lookback:
            return None
        
        recent = data.tail(lookback)
        swing_high = recent['high'].max()
        
        return swing_high
    
    def find_swing_low(self, data: pd.DataFrame, lookback: int = 20) -> Optional[float]:
        """Trouve le swing low sur une période."""
        if len(data) < lookback:
            return None
        
        recent = data.tail(lookback)
        swing_low = recent['low'].min()
        
        return swing_low
    
    def calculate_fibonacci_levels(
        self,
        swing_high: float,
        swing_low: float,
        is_uptrend: bool = True
    ) -> Dict[str, float]:
        """
        Calcule les niveaux de Fibonacci.
        
        Args:
            swing_high: Plus haut du swing
            swing_low: Plus bas du swing
            is_uptrend: True si retracement dans uptrend
            
        Returns:
            Dict des niveaux Fibonacci
        """
        diff = swing_high - swing_low
        levels = {}
        
        if is_uptrend:
            # Retracement dans uptrend (depuis high vers low)
            for name, ratio in self.fib_ratios.items():
                levels[name] = swing_high - (diff * ratio)
        else:
            # Retracement dans downtrend (depuis low vers high)
            for name, ratio in self.fib_ratios.items():
                levels[name] = swing_low + (diff * ratio)
        
        return levels
    
    def detect_trend_direction(self, data: pd.DataFrame) -> bool:
        """Détecte si uptrend (True) ou downtrend (False)."""
        if len(data) < 20:
            return True
        
        # Comparer premières et dernières bougies
        first_close = data['close'].iloc[:10].mean()
        last_close = data['close'].iloc[-10:].mean()
        
        return last_close > first_close
    
    def calculate_auto_fibonacci(
        self,
        data: pd.DataFrame,
        lookback: int = 50
    ) -> Dict:
        """
        Calcule automatiquement les Fibonacci sur un timeframe.
        
        Returns:
            {
                'swing_high': float,
                'swing_low': float,
                'levels': {...},
                'is_uptrend': bool,
                'current_level': str (niveau le plus proche)
            }
        """
        if len(data) < lookback:
            return None
        
        # Trouver swings
        swing_high = self.find_swing_high(data, lookback)
        swing_low = self.find_swing_low(data, lookback)
        
        if swing_high is None or swing_low is None:
            return None
        
        # Déterminer tendance
        is_uptrend = self.detect_trend_direction(data)
        
        # Calculer niveaux
        levels = self.calculate_fibonacci_levels(swing_high, swing_low, is_uptrend)
        
        # Prix actuel
        current_price = data['close'].iloc[-1]
        
        # Trouver niveau le plus proche
        closest_level = None
        min_distance = float('inf')
        
        for level_name, level_price in levels.items():
            distance = abs(current_price - level_price)
            if distance < min_distance:
                min_distance = distance
                closest_level = level_name
        
        distance_pct = (min_distance / current_price) * 100
        
        return {
            'swing_high': swing_high,
            'swing_low': swing_low,
            'levels': levels,
            'is_uptrend': is_uptrend,
            'current_price': current_price,
            'closest_level': closest_level,
            'distance_to_level': min_distance,
            'distance_pct': distance_pct
        }
    
    def calculate_multi_timeframe_fibonacci(
        self,
        data_5m: pd.DataFrame,
        data_15m: pd.DataFrame,
        data_1h: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Calcule Fibonacci sur plusieurs timeframes.
        
        Returns:
            {
                '5M': {...},
                '15M': {...},
                '1H': {...},
                'confluences': [...]
            }
        """
        result = {}
        
        # Fibonacci 5M
        fib_5m = self.calculate_auto_fibonacci(data_5m, lookback=30)
        if fib_5m:
            result['5M'] = fib_5m
        
        # Fibonacci 15M
        fib_15m = self.calculate_auto_fibonacci(data_15m, lookback=50)
        if fib_15m:
            result['15M'] = fib_15m
        
        # Fibonacci 1H (optionnel)
        if data_1h is not None:
            fib_1h = self.calculate_auto_fibonacci(data_1h, lookback=100)
            if fib_1h:
                result['1H'] = fib_1h
        
        # Détecter confluences
        confluences = self.find_confluences(result)
        result['confluences'] = confluences
        
        return result
    
    def find_confluences(self, multi_tf_fib: Dict) -> List[Dict]:
        """
        Trouve les confluences entre niveaux Fibonacci de différents TF.
        
        Confluence = Plusieurs niveaux Fib proches sur différents TF
        """
        confluences = []
        
        if '5M' not in multi_tf_fib or '15M' not in multi_tf_fib:
            return confluences
        
        fib_5m = multi_tf_fib['5M']['levels']
        fib_15m = multi_tf_fib['15M']['levels']
        
        # Comparer tous les niveaux
        for name_5m, level_5m in fib_5m.items():
            for name_15m, level_15m in fib_15m.items():
                # Distance entre niveaux
                distance_pct = abs(level_5m - level_15m) / level_5m * 100
                
                # Confluence si distance < 0.1%
                if distance_pct < 0.1:
                    confluences.append({
                        'level_5m': name_5m,
                        'level_15m': name_15m,
                        'price': (level_5m + level_15m) / 2,
                        'strength': 'STRONG',
                        'distance_pct': distance_pct
                    })
        
        return confluences
    
    def is_price_near_fibonacci(
        self,
        current_price: float,
        fib_analysis: Dict,
        threshold_pct: float = 0.1
    ) -> Dict:
        """
        Vérifie si le prix est près d'un niveau Fibonacci important.
        
        Args:
            current_price: Prix actuel
            fib_analysis: Résultat de calculate_auto_fibonacci
            threshold_pct: Seuil en pourcentage (0.1% par défaut)
            
        Returns:
            {
                'near_level': bool,
                'level_name': str,
                'level_price': float,
                'is_key_level': bool (0.382, 0.5, 0.618)
            }
        """
        if fib_analysis is None or 'levels' not in fib_analysis:
            return {'near_level': False}
        
        levels = fib_analysis['levels']
        
        # Niveaux clés
        key_levels = ['0.382', '0.5', '0.618']
        
        for level_name, level_price in levels.items():
            distance_pct = abs(current_price - level_price) / current_price * 100
            
            if distance_pct < threshold_pct:
                return {
                    'near_level': True,
                    'level_name': level_name,
                    'level_price': level_price,
                    'distance_pct': distance_pct,
                    'is_key_level': level_name in key_levels
                }
        
        return {'near_level': False}
    
    def get_fib_support_resistance(self, fib_analysis: Dict) -> Dict:
        """
        Identifie les niveaux de support et résistance Fibonacci.
        
        Returns:
            {
                'support': [level1, level2, ...],
                'resistance': [level1, level2, ...]
            }
        """
        if fib_analysis is None:
            return {'support': [], 'resistance': []}
        
        current_price = fib_analysis['current_price']
        levels = fib_analysis['levels']
        
        support_levels = []
        resistance_levels = []
        
        for name, price in levels.items():
            if price < current_price:
                support_levels.append({'name': name, 'price': price})
            elif price > current_price:
                resistance_levels.append({'name': name, 'price': price})
        
        # Trier
        support_levels.sort(key=lambda x: x['price'], reverse=True)
        resistance_levels.sort(key=lambda x: x['price'])
        
        return {
            'support': support_levels[:3],  # 3 plus proches
            'resistance': resistance_levels[:3]
        }
