"""
STRATÉGIES DE SCALPING OPTIMISÉES
==================================

Objectif: 5-10% de rendement JOURNALIER
Multiple stratégies testées pour trouver la meilleure
"""

import sys
import numpy as np
import pandas as pd
from datetime import datetime

from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.indicators.technical_indicators import TechnicalIndicators


# ====================================================================
# STRATÉGIE 1: SCALPER AGRESSIF RSI
# ====================================================================

class AggressiveRSIScalper(BaseStrategy):
    """
    Scalper ultra-agressif basé sur RSI extrêmes
    
    Caractéristiques:
    - RSI période 5 (très court)
    - Entrées sur RSI < 20 ou > 80
    - TP: 2 pips, SL: 1.5 pips (Ratio 1.33:1)
    - Très haute fréquence
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.02):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        self.tp_pips = 2.0
        self.sl_pips = 1.5
        self.max_positions = 10
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 10 or len(self.open_positions) >= self.max_positions:
            return 0
        
        # RSI ultra-court
        rsi = self.indicators.calculate_rsi(data['close'], period=5)
        if rsi is None or pd.isna(rsi.iloc[-1]):
            return 0
        
        current_rsi = rsi.iloc[-1]
        momentum = data['close'].diff(1).iloc[-1]
        
        # ACHAT: RSI très bas + momentum positif
        if current_rsi < 20 and momentum > 0:
            return 1
        
        # VENTE: RSI très haut + momentum négatif  
        if current_rsi > 80 and momentum < 0:
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
# STRATÉGIE 2: BOLLINGER BAND BOUNCE SCALPER
# ====================================================================

class BollingerBounceScalper(BaseStrategy):
    """
    Scalper sur rebonds des Bollinger Bands
    
    Caractéristiques:
    - Bollinger période 10, std 2.5
    - Entrées quand prix touche les bandes
    - TP: 2.5 pips, SL: 1.5 pips (Ratio 1.67:1)
    - Win rate élevé attendu
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.02):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        self.tp_pips = 2.5
        self.sl_pips = 1.5
        self.max_positions = 8
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 20 or len(self.open_positions) >= self.max_positions:
            return 0
        
        # Bollinger Bands
        upper, middle, lower = self.indicators.calculate_bollinger_bands(
            data['close'], period=10, std_dev=2.5
        )
        
        if upper is None or pd.isna(upper.iloc[-1]):
            return 0
        
        current_price = data['close'].iloc[-1]
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]
        current_middle = middle.iloc[-1]
        
        # Distance aux bandes
        upper_dist = (current_upper - current_price) / current_price
        lower_dist = (current_price - current_lower) / current_price
        
        # ACHAT: Prix très proche bande inférieure
        if lower_dist < 0.0002:  # Très proche
            return 1
        
        # VENTE: Prix très proche bande supérieure
        if upper_dist < 0.0002:
            return -1
        
        return 0
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        if position.position_type == 'BUY':
            if current_price >= position.take_profit or current_price <= position.stop_loss:
                return True
        else:
            if current_price <= position.take_profit or current_price >= position.stop_loss:
                return True
        
        # Fermeture anticipée si profit > $1
        profit = position.get_current_profit(current_price)
        if profit >= 1.0 and np.random.random() < 0.40:
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
# STRATÉGIE 3: TRIPLE EMA CROSSOVER SCALPER
# ====================================================================

class TripleEMAScalper(BaseStrategy):
    """
    Scalper sur croisements de 3 EMA
    
    Caractéristiques:
    - EMA 3, 8, 21
    - Entrées sur alignement parfait
    - TP: 3 pips, SL: 2 pips (Ratio 1.5:1)
    - Moins de trades mais meilleure qualité
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.03):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        self.tp_pips = 3.0
        self.sl_pips = 2.0
        self.max_positions = 6
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 30 or len(self.open_positions) >= self.max_positions:
            return 0
        
        # Triple EMA
        ema3 = self.indicators.calculate_ema(data['close'], period=3)
        ema8 = self.indicators.calculate_ema(data['close'], period=8)
        ema21 = self.indicators.calculate_ema(data['close'], period=21)
        
        if ema3 is None or pd.isna(ema3.iloc[-1]):
            return 0
        
        current_price = data['close'].iloc[-1]
        e3 = ema3.iloc[-1]
        e8 = ema8.iloc[-1]
        e21 = ema21.iloc[-1]
        
        # Croisement récent
        e3_prev = ema3.iloc[-2]
        e8_prev = ema8.iloc[-2]
        
        # ACHAT: EMA3 > EMA8 > EMA21 ET croisement récent
        if e3 > e8 > e21:
            if e3_prev <= e8_prev and e3 > e8:  # Croisement
                return 1
        
        # VENTE: EMA3 < EMA8 < EMA21 ET croisement récent
        if e3 < e8 < e21:
            if e3_prev >= e8_prev and e3 < e8:  # Croisement
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
# STRATÉGIE 4: PRICE ACTION SCALPER (CANDLESTICK)
# ====================================================================

class PriceActionScalper(BaseStrategy):
    """
    Scalper basé sur price action pure
    
    Caractéristiques:
    - Détection de patterns (engulfing, pinbar)
    - Support/Résistance instantanés
    - TP: 2.5 pips, SL: 1.8 pips (Ratio 1.39:1)
    - Haute précision
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.025):
        super().__init__(symbol, lot_size)
        self.tp_pips = 2.5
        self.sl_pips = 1.8
        self.max_positions = 8
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 5 or len(self.open_positions) >= self.max_positions:
            return 0
        
        # Dernières bougies
        current = data.iloc[-1]
        prev = data.iloc[-2]
        
        # Détection patterns
        is_bullish_engulfing = (
            prev['close'] < prev['open'] and  # Baissière
            current['close'] > current['open'] and  # Haussière
            current['open'] < prev['close'] and
            current['close'] > prev['open']
        )
        
        is_bearish_engulfing = (
            prev['close'] > prev['open'] and  # Haussière
            current['close'] < current['open'] and  # Baissière
            current['open'] > prev['close'] and
            current['close'] < prev['open']
        )
        
        # Support/Résistance sur 20 dernières bougies
        recent = data.tail(20)
        support = recent['low'].min()
        resistance = recent['high'].max()
        
        current_price = current['close']
        
        # ACHAT: Engulfing haussier près support
        if is_bullish_engulfing:
            dist_support = (current_price - support) / current_price
            if dist_support < 0.002:  # 0.2% du support
                return 1
        
        # VENTE: Engulfing baissier près résistance
        if is_bearish_engulfing:
            dist_resistance = (resistance - current_price) / current_price
            if dist_resistance < 0.002:
                return -1
        
        return 0
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        if position.position_type == 'BUY':
            if current_price >= position.take_profit or current_price <= position.stop_loss:
                return True
        else:
            if current_price <= position.take_profit or current_price >= position.stop_loss:
                return True
        
        # Fermeture sur profit partiel
        profit = position.get_current_profit(current_price)
        if profit >= 1.5 and np.random.random() < 0.50:
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
# FONCTION DE TEST
# ====================================================================

def test_strategy(strategy_class, strategy_name, data, initial_capital=10000):
    """Teste une stratégie et retourne les résultats."""
    
    print(f"\n{'='*80}")
    print(f"   TESTING: {strategy_name}")
    print(f"{'='*80}")
    
    # Créer la stratégie
    strategy = strategy_class()
    
    print(f"\n⚙️ Configuration:")
    print(f"   Lot Size: {strategy.lot_size}")
    print(f"   TP: {strategy.tp_pips} pips")
    print(f"   SL: {strategy.sl_pips} pips")
    print(f"   Ratio: {strategy.tp_pips/strategy.sl_pips:.2f}:1")
    print(f"   Max Positions: {strategy.max_positions}")
    
    # Risk manager agressif
    risk_manager = RiskManager(
        initial_capital=initial_capital,
        max_daily_loss=500.0,  # 5% du capital
        max_position_size=0.1,
        max_open_positions=strategy.max_positions,
        max_drawdown_percent=20.0
    )
    
    # Backtester
    backtester = Backtester(strategy, initial_capital=initial_capital)
    
    # Run
    print(f"\n🔄 Running backtest...")
    results = backtester.run(data, risk_manager=risk_manager, verbose=False)
    
    # Afficher résultats compacts
    print(f"\n📊 RESULTS:")
    print(f"   Trades: {results['total_trades']}")
    print(f"   Return: {results['total_return_%']:+.2f}%")
    print(f"   Profit: ${results['total_profit_$']:+,.2f}")
    print(f"   Win Rate: {results['win_rate_%']:.1f}%")
    print(f"   Profit Factor: {results['profit_factor']:.2f}")
    print(f"   Max Drawdown: {results['max_drawdown_%']:.2f}%")
    print(f"   Sharpe: {results['sharpe_ratio']:.3f}")
    
    # Calcul rendement journalier
    duration_days = results['duration_days']
    if duration_days > 0:
        daily_return = results['total_return_%'] / duration_days
        print(f"   📅 DAILY RETURN: {daily_return:+.2f}%/day")
    
    return results, backtester


def main():
    """Teste toutes les stratégies."""
    
    print("="*80)
    print("   🚀 OPTIMISATION DES STRATÉGIES DE SCALPING")
    print("   OBJECTIF: 5-10% DE RENDEMENT JOURNALIER")
    print("="*80)
    
    # Générer données optimisées pour scalping
    print("\n📊 Génération des données (5min, 1 mois)...")
    
    np.random.seed(789)
    
    # 1 mois de données 5min = ~8,640 barres
    dates = pd.date_range(start='2024-01-01', end='2024-02-01', freq='5min')
    n = len(dates)
    
    # Prix avec forte tendance + volatilité
    trend = np.linspace(0, 100, n)  # Tendance haussière marquée
    noise = np.cumsum(np.random.randn(n) * 2.0)  # Forte volatilité
    close = 2000 + trend + noise
    
    # OHLC avec mouvements
    high = close + np.abs(np.random.randn(n) * 1.5)
    low = close - np.abs(np.random.randn(n) * 1.5)
    open_price = close + np.random.randn(n) * 0.8
    volume = np.random.randint(500, 5000, n)
    
    data = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    print(f"✅ {len(data)} barres générées")
    print(f"📅 Période: 1 mois (31 jours)")
    print(f"💰 Prix: ${data['close'].iloc[0]:.2f} → ${data['close'].iloc[-1]:.2f}")
    
    # Tester toutes les stratégies
    strategies = [
        (AggressiveRSIScalper, "Aggressive RSI Scalper"),
        (BollingerBounceScalper, "Bollinger Bounce Scalper"),
        (TripleEMAScalper, "Triple EMA Scalper"),
        (PriceActionScalper, "Price Action Scalper")
    ]
    
    all_results = []
    
    for strategy_class, strategy_name in strategies:
        results, backtester = test_strategy(strategy_class, strategy_name, data)
        all_results.append((strategy_name, results, backtester))
    
    # Comparaison finale
    print("\n" + "="*80)
    print("   📊 COMPARAISON DES STRATÉGIES")
    print("="*80)
    
    print(f"\n{'Stratégie':<30} {'Trades':<10} {'Return':<12} {'Daily%':<12} {'Win%':<10} {'PF':<8}")
    print("-"*80)
    
    best_strategy = None
    best_daily_return = -999
    
    for name, results, _ in all_results:
        trades = results['total_trades']
        total_return = results['total_return_%']
        win_rate = results['win_rate_%']
        pf = results['profit_factor']
        daily_return = total_return / results['duration_days']
        
        print(f"{name:<30} {trades:<10} {total_return:+.2f}%     {daily_return:+.2f}%/d    {win_rate:.1f}%    {pf:.2f}")
        
        if daily_return > best_daily_return:
            best_daily_return = daily_return
            best_strategy = (name, results)
    
    # Meilleure stratégie
    print("\n" + "="*80)
    print("   🏆 MEILLEURE STRATÉGIE")
    print("="*80)
    
    if best_strategy:
        name, results = best_strategy
        print(f"\n🥇 GAGNANTE: {name}")
        print(f"\n📊 Performance:")
        print(f"   Return Total: {results['total_return_%']:+.2f}%")
        print(f"   Return Journalier: {best_daily_return:+.2f}%/jour")
        print(f"   Trades: {results['total_trades']}")
        print(f"   Win Rate: {results['win_rate_%']:.1f}%")
        print(f"   Profit Factor: {results['profit_factor']:.2f}")
        print(f"   Max Drawdown: {results['max_drawdown_%']:.2f}%")
        
        # Objectif atteint?
        if best_daily_return >= 5.0:
            print(f"\n✅ OBJECTIF ATTEINT! {best_daily_return:.2f}%/jour ≥ 5%/jour")
        elif best_daily_return >= 3.0:
            print(f"\n⚠️ Proche de l'objectif: {best_daily_return:.2f}%/jour")
        else:
            print(f"\n❌ Objectif non atteint: {best_daily_return:.2f}%/jour < 5%/jour")
        
        # Projection
        print(f"\n📈 Projections:")
        monthly = best_daily_return * 30
        yearly = best_daily_return * 365
        print(f"   Mensuel: {monthly:+.2f}%")
        print(f"   Annuel: {yearly:+.2f}%")
        
        capital_1_month = 10000 * (1 + monthly/100)
        capital_1_year = 10000 * (1 + yearly/100)
        print(f"\n💰 Capital après:")
        print(f"   1 mois: ${capital_1_month:,.2f}")
        print(f"   1 an: ${capital_1_year:,.2f}")
    
    print("\n" + "="*80)
    print("   ✅ OPTIMISATION TERMINÉE")
    print("="*80)
    
    return all_results


if __name__ == "__main__":
    try:
        results = main()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
