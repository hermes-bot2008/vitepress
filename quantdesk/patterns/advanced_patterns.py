"""
Advanced Pattern Detection
===========================

Détection de patterns institutionnels avancés:
- Order Blocks
- Fair Value Gaps (FVG)
- Liquidity Sweeps
- Breaker Blocks
- Mitigation Blocks
- Supply/Demand Zones
- Market Structure Shifts
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional


class AdvancedPatternDetector:
    """Détecteur de patterns institutionnels avancés."""
    
    def __init__(self):
        self.order_blocks = []
        self.fvg_zones = []
        self.supply_zones = []
        self.demand_zones = []
    
    # ═══════════════════════════════════════════════════════════════
    # ORDER BLOCKS
    # ═══════════════════════════════════════════════════════════════
    
    def detect_order_blocks(self, data: pd.DataFrame, lookback: int = 30) -> List[Dict]:
        """
        Détecte les Order Blocks (zones d'accumulation/distribution).
        
        Order Block = Dernière bougie opposée avant un fort mouvement
        """
        if len(data) < lookback:
            return []
        
        recent = data.tail(lookback)
        order_blocks = []
        
        for i in range(len(recent) - 5):
            candle = recent.iloc[i]
            
            # Analyser les 4 prochaines bougies
            next_4 = recent.iloc[i+1:i+5]
            
            # Bullish OB: Dernière bougie baissière avant rally
            if candle['close'] < candle['open']:  # Baissière
                # Rally ensuite?
                rally = (next_4['close'].iloc[-1] > next_4['close'].iloc[0] and
                        next_4['close'].iloc[-1] > candle['high'])
                
                if rally:
                    order_blocks.append({
                        'type': 'BULLISH',
                        'high': candle['high'],
                        'low': candle['low'],
                        'open': candle['open'],
                        'close': candle['close'],
                        'strength': (candle['high'] - candle['low']) / candle['close'],
                        'index': i
                    })
            
            # Bearish OB: Dernière bougie haussière avant chute
            if candle['close'] > candle['open']:  # Haussière
                # Chute ensuite?
                drop = (next_4['close'].iloc[-1] < next_4['close'].iloc[0] and
                       next_4['close'].iloc[-1] < candle['low'])
                
                if drop:
                    order_blocks.append({
                        'type': 'BEARISH',
                        'high': candle['high'],
                        'low': candle['low'],
                        'open': candle['open'],
                        'close': candle['close'],
                        'strength': (candle['high'] - candle['low']) / candle['close'],
                        'index': i
                    })
        
        self.order_blocks = order_blocks[-5:]  # Garder les 5 plus récents
        return self.order_blocks
    
    # ═══════════════════════════════════════════════════════════════
    # FAIR VALUE GAPS (FVG)
    # ═══════════════════════════════════════════════════════════════
    
    def detect_fair_value_gaps(self, data: pd.DataFrame, lookback: int = 20) -> List[Dict]:
        """
        Détecte les Fair Value Gaps (déséquilibres).
        
        FVG = Gap entre 3 bougies consécutives
        """
        if len(data) < lookback + 2:
            return []
        
        recent = data.tail(lookback)
        fvg_zones = []
        
        for i in range(len(recent) - 2):
            c1 = recent.iloc[i]
            c2 = recent.iloc[i+1]
            c3 = recent.iloc[i+2]
            
            # Bullish FVG: c3.low > c1.high (gap haussier)
            if c3['low'] > c1['high']:
                gap_size = c3['low'] - c1['high']
                fvg_zones.append({
                    'type': 'BULLISH',
                    'top': c3['low'],
                    'bottom': c1['high'],
                    'mid': (c3['low'] + c1['high']) / 2,
                    'size': gap_size,
                    'strength': gap_size / c1['high']
                })
            
            # Bearish FVG: c3.high < c1.low (gap baissier)
            if c3['high'] < c1['low']:
                gap_size = c1['low'] - c3['high']
                fvg_zones.append({
                    'type': 'BEARISH',
                    'top': c1['low'],
                    'bottom': c3['high'],
                    'mid': (c1['low'] + c3['high']) / 2,
                    'size': gap_size,
                    'strength': gap_size / c3['high']
                })
        
        self.fvg_zones = fvg_zones[-5:]
        return self.fvg_zones
    
    # ═══════════════════════════════════════════════════════════════
    # LIQUIDITY SWEEPS
    # ═══════════════════════════════════════════════════════════════
    
    def detect_liquidity_sweeps(self, data: pd.DataFrame, lookback: int = 20) -> Optional[Dict]:
        """
        Détecte les liquidity sweeps (pièges à stops).
        
        Sweep = Prix dépasse un high/low récent puis reverse rapidement
        """
        if len(data) < lookback + 1:
            return None
        
        recent = data.tail(lookback + 1)
        
        # Highs et lows récents (exclure la dernière bougie)
        prev_high = recent['high'].iloc[:-2].max()
        prev_low = recent['low'].iloc[:-2].min()
        
        current = recent.iloc[-1]
        prev = recent.iloc[-2]
        
        # Bullish Sweep: Balaye low récent puis reverse fort
        if prev['low'] <= prev_low * 1.0001:  # Touche ou dépasse
            # Reversal fort?
            if (current['close'] > prev['close'] and
                current['close'] > current['open'] and
                current['close'] - current['low'] > (current['high'] - current['low']) * 0.6):
                
                return {
                    'type': 'BULLISH_SWEEP',
                    'swept_level': prev_low,
                    'sweep_low': prev['low'],
                    'reversal_strength': (current['close'] - current['low']) / (current['high'] - current['low']),
                    'quality': 85
                }
        
        # Bearish Sweep: Balaye high récent puis reverse fort
        if prev['high'] >= prev_high * 0.9999:  # Touche ou dépasse
            if (current['close'] < prev['close'] and
                current['close'] < current['open'] and
                current['high'] - current['close'] > (current['high'] - current['low']) * 0.6):
                
                return {
                    'type': 'BEARISH_SWEEP',
                    'swept_level': prev_high,
                    'sweep_high': prev['high'],
                    'reversal_strength': (current['high'] - current['close']) / (current['high'] - current['low']),
                    'quality': 85
                }
        
        return None
    
    # ═══════════════════════════════════════════════════════════════
    # BREAKER BLOCKS
    # ═══════════════════════════════════════════════════════════════
    
    def detect_breaker_blocks(self, data: pd.DataFrame) -> List[Dict]:
        """
        Détecte les Breaker Blocks (Order Blocks cassés qui deviennent supports/résistances).
        
        Breaker = Ancien resistance qui devient support (ou inverse)
        """
        if len(data) < 50:
            return []
        
        breaker_blocks = []
        recent = data.tail(50)
        current_price = data['close'].iloc[-1]
        
        # Chercher les order blocks précédents
        order_blocks = self.detect_order_blocks(recent, lookback=40)
        
        for ob in order_blocks:
            ob_high = ob['high']
            ob_low = ob['low']
            
            # Bullish breaker: Ancien résistance cassée, devient support
            if ob['type'] == 'BEARISH':
                # Prix a-t-il cassé au-dessus?
                broke_above = recent['close'].max() > ob_high
                # Prix est-il revenu tester?
                if broke_above and ob_low < current_price < ob_high * 1.01:
                    breaker_blocks.append({
                        'type': 'BULLISH_BREAKER',
                        'zone': {'high': ob_high, 'low': ob_low},
                        'quality': 70
                    })
            
            # Bearish breaker: Ancien support cassé, devient résistance
            if ob['type'] == 'BULLISH':
                # Prix a-t-il cassé en-dessous?
                broke_below = recent['close'].min() < ob_low
                # Prix est-il revenu tester?
                if broke_below and ob_high > current_price > ob_low * 0.99:
                    breaker_blocks.append({
                        'type': 'BEARISH_BREAKER',
                        'zone': {'high': ob_high, 'low': ob_low},
                        'quality': 70
                    })
        
        return breaker_blocks
    
    # ═══════════════════════════════════════════════════════════════
    # SUPPLY/DEMAND ZONES
    # ═══════════════════════════════════════════════════════════════
    
    def detect_supply_demand_zones(self, data: pd.DataFrame, lookback: int = 100) -> Dict:
        """
        Détecte les zones de Supply (offre) et Demand (demande).
        
        Supply Zone = Zone où prix a chuté rapidement (vente institutionnelle)
        Demand Zone = Zone où prix a rebondi rapidement (achat institutionnel)
        """
        if len(data) < lookback:
            return {'supply': [], 'demand': []}
        
        recent = data.tail(lookback)
        
        supply_zones = []
        demand_zones = []
        
        for i in range(len(recent) - 10):
            # Analyser séquence
            base_candle = recent.iloc[i]
            next_10 = recent.iloc[i+1:i+11]
            
            base_high = base_candle['high']
            base_low = base_candle['low']
            
            # Demand Zone: Prix rebondit fort depuis cette zone
            if len(next_10) > 0:
                rally = next_10['close'].iloc[-1] > base_high * 1.01
                strong_move = (next_10['close'].iloc[-1] - base_low) / base_low > 0.005
                
                if rally and strong_move:
                    demand_zones.append({
                        'type': 'DEMAND',
                        'high': base_high,
                        'low': base_low,
                        'mid': (base_high + base_low) / 2,
                        'strength': (next_10['close'].iloc[-1] - base_low) / base_low
                    })
            
            # Supply Zone: Prix chute fort depuis cette zone
            if len(next_10) > 0:
                drop = next_10['close'].iloc[-1] < base_low * 0.99
                strong_move = (base_high - next_10['close'].iloc[-1]) / base_high > 0.005
                
                if drop and strong_move:
                    supply_zones.append({
                        'type': 'SUPPLY',
                        'high': base_high,
                        'low': base_low,
                        'mid': (base_high + base_low) / 2,
                        'strength': (base_high - next_10['close'].iloc[-1]) / base_high
                    })
        
        # Garder les zones les plus fortes
        supply_zones.sort(key=lambda x: x['strength'], reverse=True)
        demand_zones.sort(key=lambda x: x['strength'], reverse=True)
        
        self.supply_zones = supply_zones[:5]
        self.demand_zones = demand_zones[:5]
        
        return {
            'supply': self.supply_zones,
            'demand': self.demand_zones
        }
    
    # ═══════════════════════════════════════════════════════════════
    # MARKET STRUCTURE
    # ═══════════════════════════════════════════════════════════════
    
    def detect_market_structure_shift(self, data: pd.DataFrame) -> Optional[Dict]:
        """
        Détecte les changements de structure de marché (CHoCH - Change of Character).
        
        CHoCH = Cassure de structure (HH/HL → LH/LL ou inverse)
        """
        if len(data) < 50:
            return None
        
        recent = data.tail(50)
        
        # Trouver les swing points
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(recent) - 2):
            # Swing high
            if (recent['high'].iloc[i] > recent['high'].iloc[i-1] and
                recent['high'].iloc[i] > recent['high'].iloc[i-2] and
                recent['high'].iloc[i] > recent['high'].iloc[i+1] and
                recent['high'].iloc[i] > recent['high'].iloc[i+2]):
                swing_highs.append((i, recent['high'].iloc[i]))
            
            # Swing low
            if (recent['low'].iloc[i] < recent['low'].iloc[i-1] and
                recent['low'].iloc[i] < recent['low'].iloc[i-2] and
                recent['low'].iloc[i] < recent['low'].iloc[i+1] and
                recent['low'].iloc[i] < recent['low'].iloc[i+2]):
                swing_lows.append((i, recent['low'].iloc[i]))
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return None
        
        # Analyser la structure
        recent_structure = None
        
        # Derniers highs et lows
        last_high = swing_highs[-1][1]
        prev_high = swing_highs[-2][1]
        last_low = swing_lows[-1][1]
        prev_low = swing_lows[-2][1]
        
        # Bullish CHoCH: Cassure de downtrend (LH/LL → HH/HL)
        if prev_high > prev_low and last_high > prev_high and last_low > prev_low:
            recent_structure = {
                'type': 'BULLISH_CHOCH',
                'from': 'DOWNTREND',
                'to': 'UPTREND',
                'quality': 85
            }
        
        # Bearish CHoCH: Cassure de uptrend (HH/HL → LH/LL)
        elif prev_high < prev_low and last_high < prev_high and last_low < prev_low:
            recent_structure = {
                'type': 'BEARISH_CHOCH',
                'from': 'UPTREND',
                'to': 'DOWNTREND',
                'quality': 85
            }
        
        return recent_structure
    
    # ═══════════════════════════════════════════════════════════════
    # MITIGATION BLOCKS
    # ═══════════════════════════════════════════════════════════════
    
    def detect_mitigation_blocks(self, data: pd.DataFrame) -> List[Dict]:
        """
        Détecte les Mitigation Blocks (zones de mitigation d'ordre).
        
        Mitigation = Zone où déséquilibre est comblé
        """
        mitigation_blocks = []
        
        # Détecter les FVG d'abord
        fvg_zones = self.detect_fair_value_gaps(data, lookback=50)
        
        if not fvg_zones:
            return []
        
        current_price = data['close'].iloc[-1]
        
        # Vérifier si le prix est dans une zone FVG
        for fvg in fvg_zones:
            fvg_top = fvg['top']
            fvg_bottom = fvg['bottom']
            fvg_mid = (fvg_top + fvg_bottom) / 2
            
            # Prix mitigue le FVG (revient dans la zone)
            if fvg_bottom <= current_price <= fvg_top:
                mitigation_blocks.append({
                    'type': 'MITIGATION_' + fvg['type'],
                    'zone': {'top': fvg_top, 'bottom': fvg_bottom, 'mid': fvg_mid},
                    'original_fvg': fvg,
                    'quality': 75
                })
        
        return mitigation_blocks
    
    # ═══════════════════════════════════════════════════════════════
    # COMPREHENSIVE ANALYSIS
    # ═══════════════════════════════════════════════════════════════
    
    def get_comprehensive_analysis(self, data: pd.DataFrame) -> Dict:
        """
        Analyse complète de tous les patterns.
        
        Returns:
            {
                'order_blocks': [...],
                'fvg': [...],
                'supply_demand': {...},
                'liquidity_sweeps': {...},
                'breaker_blocks': [...],
                'mitigation': [...],
                'structure_shift': {...}
            }
        """
        analysis = {}
        
        # Order Blocks
        analysis['order_blocks'] = self.detect_order_blocks(data)
        
        # Fair Value Gaps
        analysis['fvg'] = self.detect_fair_value_gaps(data)
        
        # Supply/Demand
        analysis['supply_demand'] = self.detect_supply_demand_zones(data)
        
        # Liquidity Sweeps
        analysis['liquidity_sweep'] = self.detect_liquidity_sweeps(data)
        
        # Breaker Blocks
        analysis['breaker_blocks'] = self.detect_breaker_blocks(data)
        
        # Mitigation Blocks
        analysis['mitigation'] = self.detect_mitigation_blocks(data)
        
        # Market Structure
        analysis['structure_shift'] = self.detect_market_structure_shift(data)
        
        return analysis
    
    def is_price_in_zone(self, price: float, zone: Dict, tolerance: float = 0.001) -> bool:
        """Vérifie si le prix est dans une zone."""
        zone_high = zone.get('high', zone.get('top', 0))
        zone_low = zone.get('low', zone.get('bottom', 0))
        
        if zone_high == 0 or zone_low == 0:
            return False
        
        # Avec tolérance
        expanded_high = zone_high * (1 + tolerance)
        expanded_low = zone_low * (1 - tolerance)
        
        return expanded_low <= price <= expanded_high
