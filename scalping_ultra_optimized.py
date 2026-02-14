"""
SCALPING ULTRA OPTIMISÉ V2
===========================

Stratégies révisées avec:
- Win rate élevé (60%+)
- Ratio R:R excellent (2:1+)
- Filtrage multi-indicateurs
- Lot size adaptatif
- Gestion agressive mais contrôlée
"""

import sys
import numpy as np
import pandas as pd

from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.indicators.technical_indicators import TechnicalIndicators


# ====================================================================
# STRATÉGIE ULTRA 1: CONFLUENCE SCALPER (Multi-Indicateurs)
# ====================================================================

class ConfluenceScalper(BaseStrategy):
    """
    Scalper basé sur confluence de PLUSIEURS signaux
    
    Filtres:
    - RSI extrême (< 15 ou > 85)
    - Bollinger Band touch
    - Volume spike
    - Momentum confirmation
    
    Objectif: Win rate 70%+ avec filtrage strict
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.05):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        self.tp_pips = 4.0  # TP agressif
        self.sl_pips = 2.0  # SL serré
        self.max_positions = 5
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 30 or len(self.open_positions) >= self.max_positions:
            return 0
        
        # Multi-indicateurs
        rsi = self.indicators.calculate_rsi(data['close'], period=14)
        upper, middle, lower = self.indicators.calculate_bollinger_bands(
            data['close'], period=20, std_dev=2.0
        )
        
        if rsi is None or upper is None:
            return 0
        
        current_price = data['close'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].rolling(20).mean().iloc[-1]
        
        # Momentum
        momentum_3 = data['close'].diff(3).iloc[-1]
        momentum_5 = data['close'].diff(5).iloc[-1]
        
        # Conditions d'achat (TOUTES doivent être vraies)
        buy_conditions = [
            current_rsi < 15,  # RSI très extrême
            current_price <= lower.iloc[-1],  # Touch bande inf
            current_volume > avg_volume * 1.2,  # Volume spike
            momentum_3 > 0,  # Momentum court positif
            momentum_5 < 0  # Mais tendance récente baissière (rebond)
        ]
        
        if all(buy_conditions):
            return 1
        
        # Conditions de vente (TOUTES doivent être vraies)
        sell_conditions = [
            current_rsi > 85,  # RSI très extrême
            current_price >= upper.iloc[-1],  # Touch bande sup
            current_volume > avg_volume * 1.2,  # Volume spike
            momentum_3 < 0,  # Momentum court négatif
            momentum_5 > 0  # Mais tendance récente haussière (rebond)
        ]
        
        if all(sell_conditions):
            return -1
        
        return 0
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        if position.position_type == 'BUY':
            if current_price >= position.take_profit or current_price <= position.stop_loss:
                return True
        else:
            if current_price <= position.take_profit or current_price >= position.stop_loss:
                return True
        
        # Trailing stop si profit > 50% du TP
        profit = position.get_current_profit(current_price)
        expected_profit = (position.take_profit - position.entry_price) * self.lot_size * 10000
        
        if abs(profit) > abs(expected_profit) * 0.5:
            # Activer trailing
            if position.position_type == 'BUY':
                new_sl = current_price - 0.01
                if new_sl > position.stop_loss:
                    position.stop_loss = new_sl
            else:
                new_sl = current_price + 0.01
                if new_sl < position.stop_loss:
                    position.stop_loss = new_sl
        
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


# ====================================================================
# STRATÉGIE ULTRA 2: MOMENTUM BREAKOUT SCALPER
# ====================================================================

class MomentumBreakoutScalper(BaseStrategy):
    """
    Scalper sur cassures de momentum violent
    
    Caractéristiques:
    - Détection de breakout fort
    - Confirmation volume + RSI
    - TP/SL dynamiques basés ATR
    - Entrées sélectives (2-3 par jour max)
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.08):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        self.max_positions = 3
        self.bars_since_last_trade = 0
        self.min_bars_between_trades = 20  # 1h40 minimum entre trades
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 50:
            return 0
        
        # Cooldown strict
        if self.bars_since_last_trade < self.min_bars_between_trades:
            self.bars_since_last_trade += 1
            return 0
        
        if len(self.open_positions) >= self.max_positions:
            return 0
        
        # Indicateurs
        rsi = self.indicators.calculate_rsi(data['close'], period=14)
        atr = self.indicators.calculate_atr(
            data['high'], data['low'], data['close'], period=14
        )
        
        if rsi is None or atr is None:
            return 0
        
        current_price = data['close'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_atr = atr.iloc[-1]
        
        # High/Low récents (range de 2 heures)
        recent_high = data['high'].tail(24).max()
        recent_low = data['low'].tail(24).min()
        
        # Volume spike
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].rolling(50).mean().iloc[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        # Momentum violent
        momentum_1 = data['close'].diff(1).iloc[-1]
        momentum_ratio = abs(momentum_1 / current_atr) if current_atr > 0 else 0
        
        # ACHAT: Breakout haussier
        if (current_price > recent_high * 0.998 and  # Proche du high
            current_rsi > 50 and current_rsi < 75 and  # RSI momentum mais pas extrême
            volume_ratio > 1.5 and  # Volume fort
            momentum_ratio > 0.3 and  # Momentum violent
            momentum_1 > 0):  # Direction haussière
            
            self.bars_since_last_trade = 0
            # TP/SL dynamiques
            self.current_atr = current_atr
            return 1
        
        # VENTE: Breakout baissier
        if (current_price < recent_low * 1.002 and  # Proche du low
            current_rsi < 50 and current_rsi > 25 and  # RSI momentum mais pas extrême
            volume_ratio > 1.5 and  # Volume fort
            momentum_ratio > 0.3 and  # Momentum violent
            momentum_1 < 0):  # Direction baissière
            
            self.bars_since_last_trade = 0
            self.current_atr = current_atr
            return -1
        
        self.bars_since_last_trade += 1
        return 0
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        if position.position_type == 'BUY':
            if current_price >= position.take_profit or current_price <= position.stop_loss:
                return True
        else:
            if current_price <= position.take_profit or current_price >= position.stop_loss:
                return True
        return False
    
    def execute_trade(self, signal: int, current_price: float):
        if signal == 0:
            return
        
        position_type = 'BUY' if signal > 0 else 'SELL'
        
        # SL/TP basés sur ATR
        atr = getattr(self, 'current_atr', current_price * 0.01)
        
        if position_type == 'BUY':
            stop_loss = current_price - (2 * atr)
            take_profit = current_price + (4 * atr)  # Ratio 2:1
        else:
            stop_loss = current_price + (2 * atr)
            take_profit = current_price - (4 * atr)
        
        return self.open_position(position_type, current_price, stop_loss, take_profit)


# ====================================================================
# STRATÉGIE ULTRA 3: SMART MONEY SCALPER
# ====================================================================

class SmartMoneyScalper(BaseStrategy):
    """
    Scalper suivant les mouvements institutionnels
    
    Détecte:
    - Accumulation/Distribution
    - Order blocks
    - Liquidity grabs
    - Fair value gaps
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.06):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        self.tp_pips = 5.0
        self.sl_pips = 2.5
        self.max_positions = 4
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 30 or len(self.open_positions) >= self.max_positions:
            return 0
        
        # Analyser les dernières bougies
        recent = data.tail(10)
        current = data.iloc[-1]
        prev = data.iloc[-2]
        
        current_price = current['close']
        
        # Détection order block (grosse bougie + consolidation)
        biggest_candle_idx = (recent['high'] - recent['low']).idxmax()
        biggest_candle = recent.loc[biggest_candle_idx]
        
        # Gap detection (écart entre bougies)
        gap_up = current['low'] > prev['high']
        gap_down = current['high'] < prev['low']
        
        # Volume analysis
        volume_ma = data['volume'].rolling(20).mean().iloc[-1]
        current_volume = current['volume']
        
        # Liquidity grab (faux mouvement puis reversal)
        recent_high = recent['high'].max()
        recent_low = recent['low'].min()
        
        swept_high = prev['high'] >= recent_high * 0.999 and current['close'] < prev['close']
        swept_low = prev['low'] <= recent_low * 1.001 and current['close'] > prev['close']
        
        # ACHAT: Liquidity grab bas + reversal
        if swept_low and current_volume > volume_ma * 1.3:
            return 1
        
        # VENTE: Liquidity grab haut + reversal
        if swept_high and current_volume > volume_ma * 1.3:
            return -1
        
        # Fair Value Gap (FVG) - écart de prix
        if gap_up and current_volume > volume_ma * 1.5:
            return 1
        
        if gap_down and current_volume > volume_ma * 1.5:
            return -1
        
        return 0
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        if position.position_type == 'BUY':
            if current_price >= position.take_profit or current_price <= position.stop_loss:
                return True
        else:
            if current_price <= position.take_profit or current_price >= position.stop_loss:
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


# ====================================================================
# TEST FUNCTION
# ====================================================================

def test_all_strategies():
    """Teste toutes les stratégies ultra optimisées."""
    
    print("="*80)
    print("   ⚡ SCALPING ULTRA OPTIMISÉ V2")
    print("   OBJECTIF: 5-10% DE RENDEMENT JOURNALIER")
    print("="*80)
    
    # Données avec FORTE tendance et volatilité
    print("\n📊 Génération de données optimales...")
    
    np.random.seed(999)
    
    # 1 mois, 5min
    dates = pd.date_range(start='2024-01-01', end='2024-02-01', freq='5min')
    n = len(dates)
    
    # Tendance FORTE + cycles + volatilité
    trend = np.linspace(0, 200, n)  # Forte tendance
    cycles = 50 * np.sin(np.linspace(0, 20*np.pi, n))  # Cycles
    noise = np.cumsum(np.random.randn(n) * 3.0)  # Forte volatilité
    close = 2000 + trend + cycles + noise
    
    # OHLC réaliste
    high = close + np.abs(np.random.randn(n) * 2.5)
    low = close - np.abs(np.random.randn(n) * 2.5)
    open_price = close + np.random.randn(n) * 1.5
    volume = np.random.gamma(2, 1000, n)  # Distribution volume réaliste
    
    data = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    print(f"✅ {len(data)} barres")
    print(f"💰 ${data['close'].iloc[0]:.2f} → ${data['close'].iloc[-1]:.2f}")
    print(f"📈 Trend: +{((data['close'].iloc[-1]/data['close'].iloc[0])-1)*100:.1f}%")
    
    # Tester les 3 stratégies ultra
    strategies = [
        (ConfluenceScalper, "Confluence Scalper (Multi-Filtre)"),
        (MomentumBreakoutScalper, "Momentum Breakout Scalper"),
        (SmartMoneyScalper, "Smart Money Scalper")
    ]
    
    results_list = []
    
    for strategy_class, name in strategies:
        print(f"\n{'='*80}")
        print(f"   TESTING: {name}")
        print(f"{'='*80}")
        
        strategy = strategy_class()
        
        print(f"\n⚙️ Config:")
        print(f"   Lot: {strategy.lot_size}")
        if hasattr(strategy, 'tp_pips'):
            print(f"   TP: {strategy.tp_pips} pips, SL: {strategy.sl_pips} pips")
            print(f"   Ratio: {strategy.tp_pips/strategy.sl_pips:.2f}:1")
        
        # Risk manager agressif
        risk_manager = RiskManager(
            initial_capital=10000,
            max_daily_loss=1000,  # 10% par jour
            max_position_size=0.2,
            max_open_positions=strategy.max_positions,
            max_drawdown_percent=25.0
        )
        
        backtester = Backtester(strategy, initial_capital=10000)
        
        print(f"\n🔄 Running...")
        results = backtester.run(data, risk_manager, verbose=False)
        
        # Results
        print(f"\n📊 RESULTS:")
        print(f"   Trades: {results['total_trades']}")
        print(f"   Return: {results['total_return_%']:+.2f}%")
        print(f"   Win Rate: {results['win_rate_%']:.1f}%")
        print(f"   Profit Factor: {results['profit_factor']:.2f}")
        print(f"   Max DD: {results['max_drawdown_%']:.2f}%")
        
        daily_return = results['total_return_%'] / results['duration_days']
        print(f"   📅 DAILY: {daily_return:+.2f}%/jour")
        
        results_list.append((name, results, daily_return))
    
    # Comparaison
    print(f"\n{'='*80}")
    print(f"   🏆 RÉSULTATS FINAUX")
    print(f"{'='*80}")
    
    print(f"\n{'Stratégie':<40} {'Trades':<10} {'Return':<12} {'Daily%':<12}")
    print("-"*80)
    
    best = max(results_list, key=lambda x: x[2])
    
    for name, results, daily in results_list:
        marker = "🥇" if daily == best[2] else "  "
        print(f"{marker} {name:<38} {results['total_trades']:<10} {results['total_return_%']:+.2f}%     {daily:+.2f}%/d")
    
    # Best strategy
    print(f"\n🥇 MEILLEURE: {best[0]}")
    print(f"   Return Journalier: {best[2]:+.2f}%/jour")
    
    if best[2] >= 5.0:
        print(f"\n✅ OBJECTIF ATTEINT! ≥ 5%/jour")
        print(f"\n💰 Projections avec ${10000:,}:")
        print(f"   1 semaine: ${10000 * (1 + best[2]*7/100):,.2f}")
        print(f"   1 mois: ${10000 * (1 + best[2]*30/100):,.2f}")
        print(f"   3 mois: ${10000 * (1 + best[2]*90/100):,.2f}")
    elif best[2] >= 2.0:
        print(f"\n⚠️ Proche mais pas atteint (besoin: 5%/jour)")
    else:
        print(f"\n❌ Objectif non atteint ({best[2]:.2f}% < 5%)")
    
    print(f"\n{'='*80}")
    
    return results_list


if __name__ == "__main__":
    try:
        test_all_strategies()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
