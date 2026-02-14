"""
SWING TRADING AGRESSIF - OPTIMISATION POUR 1-2%/JOUR
=====================================================

Stratégies pour transformer le Swing Trading (+10.9% en 6 mois = 0.06%/jour)
en système générant 1-2% PAR JOUR:

1. Augmenter la fréquence: 2 trades → 20-30 trades/mois
2. Augmenter le lot size: 0.01 → 0.05-0.10
3. Réduire les timeframes: 1H → 15M-30M
4. Combiner plusieurs stratégies simultanément
5. Optimiser les paramètres pour plus de signaux
"""

import sys
import numpy as np
import pandas as pd

from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.algorithms.mean_reversion import MeanReversionStrategy
from quantdesk.algorithms.momentum import MomentumStrategy
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.indicators.technical_indicators import TechnicalIndicators


# ═══════════════════════════════════════════════════════════════
# STRATÉGIE 1: SWING AGRESSIF - HAUTE FRÉQUENCE
# ═══════════════════════════════════════════════════════════════

class AggressiveSwingTrader(BaseStrategy):
    """
    Swing Trading Agressif
    
    Changements vs original:
    - Timeframe plus court (15M-30M vs 1H)
    - Paramètres EMA plus courts (5/13 vs 10/30)
    - Cooldown réduit (2 barres vs 10)
    - Lot size augmenté (0.08 vs 0.01)
    - Objectif: 15-25 trades/mois
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.08):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        
        self.tp_multiplier = 3.0
        self.sl_multiplier = 2.0
        self.max_positions = 6
        
        self.bars_since_trade = 0
        self.min_bars = 2  # Cooldown minimal!
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 50:
            return 0
        
        # Cooldown minimal
        if self.bars_since_trade < self.min_bars:
            self.bars_since_trade += 1
            return 0
        
        if len(self.open_positions) >= self.max_positions:
            return 0
        
        # EMAs COURTES pour plus de signaux
        ema_fast = self.indicators.calculate_ema(data['close'], 5)
        ema_slow = self.indicators.calculate_ema(data['close'], 13)
        rsi = self.indicators.calculate_rsi(data['close'], 14)
        
        if ema_fast is None or rsi is None:
            self.bars_since_trade += 1
            return 0
        
        current_price = data['close'].iloc[-1]
        ema_f_curr = ema_fast.iloc[-1]
        ema_s_curr = ema_slow.iloc[-1]
        ema_f_prev = ema_fast.iloc[-2]
        ema_s_prev = ema_slow.iloc[-2]
        rsi_val = rsi.iloc[-1]
        
        # Croisement haussier
        if ema_f_prev <= ema_s_prev and ema_f_curr > ema_s_curr and rsi_val < 70:
            self.bars_since_trade = 0
            return 1
        
        # Croisement baissier
        if ema_f_prev >= ema_s_prev and ema_f_curr < ema_s_curr and rsi_val > 30:
            self.bars_since_trade = 0
            return -1
        
        self.bars_since_trade += 1
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
        if signal == 0 or self.market_data is None:
            return
        
        # ATR pour SL/TP
        atr = self.indicators.calculate_atr(
            self.market_data['high'],
            self.market_data['low'],
            self.market_data['close'],
            14
        )
        
        if atr is None or pd.isna(atr.iloc[-1]):
            atr_value = current_price * 0.015
        else:
            atr_value = atr.iloc[-1]
        
        position_type = 'BUY' if signal > 0 else 'SELL'
        
        if position_type == 'BUY':
            stop_loss = current_price - (self.sl_multiplier * atr_value)
            take_profit = current_price + (self.tp_multiplier * atr_value)
        else:
            stop_loss = current_price + (self.sl_multiplier * atr_value)
            take_profit = current_price - (self.tp_multiplier * atr_value)
        
        return self.open_position(position_type, current_price, stop_loss, take_profit)


# ═══════════════════════════════════════════════════════════════
# STRATÉGIE 2: MULTI-SWING (Plusieurs Stratégies en Parallèle)
# ═══════════════════════════════════════════════════════════════

class MultiSwingStrategy(BaseStrategy):
    """
    Combine 3 stratégies swing en parallèle:
    - Mean Reversion
    - Momentum  
    - Breakout
    
    Objectif: Diversifier les opportunités → Plus de trades
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.06):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        
        self.tp_multiplier = 2.5
        self.sl_multiplier = 2.0
        self.max_positions = 8
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 50 or len(self.open_positions) >= self.max_positions:
            return 0
        
        # Score de 3 systèmes
        score = 0
        
        # 1. MEAN REVERSION
        upper, middle, lower = self.indicators.calculate_bollinger_bands(data['close'], 20, 2.0)
        rsi = self.indicators.calculate_rsi(data['close'], 14)
        
        if upper is not None and rsi is not None:
            current_price = data['close'].iloc[-1]
            rsi_val = rsi.iloc[-1]
            
            # Oversold
            if current_price <= lower.iloc[-1] and rsi_val < 35:
                score += 1
            
            # Overbought
            if current_price >= upper.iloc[-1] and rsi_val > 65:
                score -= 1
        
        # 2. MOMENTUM
        macd_line, signal_line, histogram = self.indicators.calculate_macd(data['close'], 12, 26, 9)
        
        if macd_line is not None:
            # Croisement MACD
            if macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] <= signal_line.iloc[-2]:
                score += 1
            elif macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] >= signal_line.iloc[-2]:
                score -= 1
        
        # 3. BREAKOUT
        high_20 = data['high'].rolling(20).max().iloc[-1]
        low_20 = data['low'].rolling(20).min().iloc[-1]
        current_price = data['close'].iloc[-1]
        
        # Breakout haussier
        if current_price > high_20 * 0.998:
            score += 1
        
        # Breakout baissier
        if current_price < low_20 * 1.002:
            score -= 1
        
        # Signal si score ≥ 2
        if score >= 2:
            return 1
        if score <= -2:
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
        if signal == 0 or self.market_data is None:
            return
        
        atr = self.indicators.calculate_atr(
            self.market_data['high'],
            self.market_data['low'],
            self.market_data['close'],
            14
        )
        
        atr_value = atr.iloc[-1] if atr is not None and not pd.isna(atr.iloc[-1]) else current_price * 0.015
        
        position_type = 'BUY' if signal > 0 else 'SELL'
        
        if position_type == 'BUY':
            stop_loss = current_price - (self.sl_multiplier * atr_value)
            take_profit = current_price + (self.tp_multiplier * atr_value)
        else:
            stop_loss = current_price + (self.sl_multiplier * atr_value)
            take_profit = current_price - (self.tp_multiplier * atr_value)
        
        return self.open_position(position_type, current_price, stop_loss, take_profit)


# ═══════════════════════════════════════════════════════════════
# STRATÉGIE 3: TURBO SWING (Timeframe Court)
# ═══════════════════════════════════════════════════════════════

class TurboSwingTrader(BaseStrategy):
    """
    Swing Trading sur timeframe court (15M)
    
    Caractéristiques:
    - Timeframe 15M (vs 1H)
    - Durée moyenne: 4-8 heures (vs 4 jours)
    - Fréquence: 3-5 trades/jour
    - Lot size: 0.10 (10% du capital)
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.10):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        
        self.tp_multiplier = 2.0
        self.sl_multiplier = 1.5
        self.max_positions = 8
        
        self.bars_since_trade = 0
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 30:
            return 0
        
        # Cooldown ultra-court
        if self.bars_since_trade < 4:  # 1 heure seulement
            self.bars_since_trade += 1
            return 0
        
        if len(self.open_positions) >= self.max_positions:
            return 0
        
        # Triple système
        rsi = self.indicators.calculate_rsi(data['close'], 14)
        ema8 = self.indicators.calculate_ema(data['close'], 8)
        ema21 = self.indicators.calculate_ema(data['close'], 21)
        
        if rsi is None or ema8 is None:
            self.bars_since_trade += 1
            return 0
        
        current_price = data['close'].iloc[-1]
        rsi_val = rsi.iloc[-1]
        e8 = ema8.iloc[-1]
        e21 = ema21.iloc[-1]
        
        # Momentum
        momentum = data['close'].diff(5).iloc[-1]
        
        # Volume
        volume_ratio = data['volume'].iloc[-1] / data['volume'].rolling(20).mean().iloc[-1]
        
        # ACHAT: EMA cross + RSI + Momentum + Volume
        if (e8 > e21 and 
            30 < rsi_val < 65 and 
            momentum > 0 and 
            volume_ratio > 0.8):
            self.bars_since_trade = 0
            return 1
        
        # VENTE
        if (e8 < e21 and 
            35 < rsi_val < 70 and 
            momentum < 0 and 
            volume_ratio > 0.8):
            self.bars_since_trade = 0
            return -1
        
        self.bars_since_trade += 1
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
        if profit >= 5.0:  # $5+
            return True
        
        return False
    
    def execute_trade(self, signal: int, current_price: float):
        if signal == 0 or self.market_data is None:
            return
        
        atr = self.indicators.calculate_atr(
            self.market_data['high'],
            self.market_data['low'],
            self.market_data['close'],
            14
        )
        
        atr_value = atr.iloc[-1] if atr is not None and not pd.isna(atr.iloc[-1]) else current_price * 0.015
        
        position_type = 'BUY' if signal > 0 else 'SELL'
        
        if position_type == 'BUY':
            stop_loss = current_price - (self.sl_multiplier * atr_value)
            take_profit = current_price + (self.tp_multiplier * atr_value)
        else:
            stop_loss = current_price + (self.sl_multiplier * atr_value)
            take_profit = current_price - (self.tp_multiplier * atr_value)
        
        return self.open_position(position_type, current_price, stop_loss, take_profit)


# ═══════════════════════════════════════════════════════════════
# TEST FUNCTION
# ═══════════════════════════════════════════════════════════════

def test_aggressive_swing(strategy_class, name, data, lot_size=0.08):
    """Teste une stratégie swing agressive."""
    
    print(f"\n{'='*80}")
    print(f"   TESTING: {name}")
    print(f"{'='*80}")
    
    strategy = strategy_class(lot_size=lot_size)
    
    print(f"\n⚙️ Configuration:")
    print(f"   Lot Size: {strategy.lot_size} ({strategy.lot_size*100}% du capital)")
    if hasattr(strategy, 'tp_multiplier'):
        print(f"   TP: {strategy.tp_multiplier}x ATR")
        print(f"   SL: {strategy.sl_multiplier}x ATR")
        print(f"   Ratio: {strategy.tp_multiplier/strategy.sl_multiplier:.2f}:1")
    
    # Risk manager agressif
    risk_manager = RiskManager(
        initial_capital=10000,
        max_daily_loss=800,  # 8% par jour!
        max_position_size=0.15,
        max_open_positions=strategy.max_positions,
        max_drawdown_percent=30.0
    )
    
    # Backtest
    backtester = Backtester(strategy, initial_capital=10000)
    
    print(f"\n🔄 Running backtest...")
    results = backtester.run(data, risk_manager, verbose=False)
    
    # Results
    print(f"\n📊 RESULTS:")
    print(f"   Trades: {results['total_trades']}")
    print(f"   Return: {results['total_return_%']:+.2f}%")
    print(f"   Win Rate: {results['win_rate_%']:.1f}%")
    print(f"   Profit Factor: {results['profit_factor']:.2f}")
    print(f"   Max DD: {results['max_drawdown_%']:.2f}%")
    
    duration = results['duration_days']
    if duration > 0:
        daily_return = results['total_return_%'] / duration
        trades_per_day = results['total_trades'] / duration
        
        print(f"\n🎯 DAILY PERFORMANCE:")
        print(f"   {daily_return:+.2f}%/jour")
        print(f"   {trades_per_day:.1f} trades/jour")
        
        if daily_return >= 1.0 and daily_return <= 3.0:
            print(f"\n   ✅✅✅ OBJECTIF ATTEINT! ✅✅✅")
        elif daily_return >= 0.5:
            print(f"\n   ⚠️ Proche: {daily_return:.2f}%/jour")
        elif daily_return > 0:
            print(f"\n   ✅ Positif: {daily_return:.2f}%/jour")
        else:
            print(f"\n   ❌ Négatif: {daily_return:.2f}%/jour")
    
    return results


def main():
    """Teste toutes les optimisations swing."""
    
    print("="*80)
    print("   🚀 OPTIMISATION SWING TRADING POUR 1-2%/JOUR")
    print("   OBJECTIF: Transformer +0.06%/jour en +1-2%/jour")
    print("="*80)
    
    # Charger données réelles
    print("\n📥 Chargement données réelles GOLD 15M...")
    
    try:
        data = pd.read_csv('data/GOLD_15m.csv', index_col=0)
        data.columns = [c.lower() for c in data.columns]
        data.index = pd.to_datetime(data.index, utc=True).tz_localize(None)
        
        # Utiliser 1 mois
        data = data.tail(2880)  # 30 jours de 15M
        
        print(f"✅ {len(data)} barres (30 jours en 15M)")
        print(f"💰 ${data['close'].iloc[0]:.2f} → ${data['close'].iloc[-1]:.2f}")
        print(f"📈 Market: {((data['close'].iloc[-1]/data['close'].iloc[0])-1)*100:+.1f}%")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("Générer données simulées...")
        
        # Fallback: données simulées
        np.random.seed(999)
        dates = pd.date_range(start='2024-01-01', end='2024-02-01', freq='15min')
        n = len(dates)
        
        trend = np.linspace(0, 150, n)
        cycles = 40 * np.sin(np.linspace(0, 30*np.pi, n))
        noise = np.cumsum(np.random.randn(n) * 2.0)
        close = 2000 + trend + cycles + noise
        
        high = close + np.abs(np.random.randn(n) * 2.5)
        low = close - np.abs(np.random.randn(n) * 2.5)
        open_price = close + np.random.randn(n) * 1.5
        volume = np.random.gamma(2, 1000, n)
        
        data = pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }, index=dates)
        
        print(f"✅ {len(data)} barres simulées (31 jours)")
    
    # Tester les 3 stratégies
    strategies = [
        (AggressiveSwingTrader, "Aggressive Swing (High Frequency)", 0.08),
        (MultiSwingStrategy, "Multi-Swing (3 Systems Combined)", 0.06),
        (TurboSwingTrader, "Turbo Swing (15M Timeframe)", 0.10)
    ]
    
    all_results = []
    
    for strategy_class, name, lot_size in strategies:
        results = test_aggressive_swing(strategy_class, name, data, lot_size)
        all_results.append((name, results))
    
    # COMPARAISON
    print(f"\n{'='*80}")
    print(f"   📊 COMPARAISON DES STRATÉGIES SWING AGRESSIVES")
    print(f"{'='*80}")
    
    print(f"\n{'Stratégie':<45} {'Trades':<10} {'Return':<12} {'Daily%':<12}")
    print("-"*80)
    
    best_daily = -999
    best_strategy = None
    
    for name, results in all_results:
        trades = results['total_trades']
        ret = results['total_return_%']
        daily = ret / results['duration_days']
        
        marker = ""
        if daily > best_daily:
            best_daily = daily
            best_strategy = (name, results)
        
        print(f"{name:<45} {trades:<10} {ret:+.2f}%     {daily:+.2f}%/d")
    
    # MEILLEURE STRATÉGIE
    if best_strategy:
        print(f"\n{'='*80}")
        print(f"   🏆 MEILLEURE STRATÉGIE SWING")
        print(f"{'='*80}")
        
        name, results = best_strategy
        daily_return = results['total_return_%'] / results['duration_days']
        
        print(f"\n🥇 GAGNANTE: {name}")
        print(f"\n📊 Performance:")
        print(f"   Return Total: {results['total_return_%']:+.2f}%")
        print(f"   Return Journalier: {daily_return:+.2f}%/jour")
        print(f"   Trades: {results['total_trades']}")
        print(f"   Win Rate: {results['win_rate_%']:.1f}%")
        print(f"   Profit Factor: {results['profit_factor']:.2f}")
        print(f"   Max Drawdown: {results['max_drawdown_%']:.2f}%")
        
        if daily_return >= 1.0 and daily_return <= 3.0:
            print(f"\n✅✅✅ OBJECTIF ATTEINT! ✅✅✅")
            print(f"\n🎉 Le Swing Trading génère {daily_return:.2f}%/jour!")
            
            weekly = daily_return * 7
            monthly = daily_return * 30
            
            print(f"\n💰 PROJECTIONS AVEC $10,000:")
            print(f"   1 semaine:  {weekly:+.1f}% → ${10000 * (1 + weekly/100):,.2f}")
            print(f"   1 mois:     {monthly:+.1f}% → ${10000 * (1 + monthly/100):,.2f}")
            print(f"   3 mois:     {monthly*3:+.1f}% → ${10000 * (1 + monthly*3/100):,.2f}")
            print(f"   6 mois:     {monthly*6:+.1f}% → ${10000 * (1 + monthly*6/100):,.2f}")
            
        elif daily_return >= 0.5:
            print(f"\n⚠️ Proche de l'objectif: {daily_return:.2f}%/jour")
            print(f"\n💡 Suggestions:")
            print(f"   - Augmenter lot size à 0.12-0.15")
            print(f"   - Réduire cooldown")
            print(f"   - Utiliser timeframe 10M ou 5M")
        elif daily_return > 0:
            print(f"\n✅ Positif mais faible: {daily_return:.2f}%/jour")
        else:
            print(f"\n❌ Négatif: {daily_return:.2f}%/jour")
    
    print(f"\n{'='*80}")
    print(f"   ✅ OPTIMISATION SWING TERMINÉE")
    print(f"{'='*80}")
    
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
