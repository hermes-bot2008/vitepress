"""
SWING HYPER-ACTIF - 1-2%/JOUR AVEC HAUTE FRÉQUENCE
===================================================

Objectif: 1-2%/jour MAIS avec 20-30 trades/mois (vs 2)
- Plus de signaux
- Lot size adaptatif
- Sortie rapide
- Plusieurs opportunités
"""

import sys
import numpy as np
import pandas as pd

from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class HyperActiveSwing(BaseStrategy):
    """
    Swing Hyper-Actif pour 1-2%/jour.
    
    Différence clé:
    - Cooldown ultra-court: 10 barres (50 min)
    - Conditions permissives: ≥ 2/5 (vs 3/5)
    - Lot size 0.10 (10%)
    - Objectif: 1 trade/jour en moyenne
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.10):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        
        self.base_lot = lot_size
        self.tp_multiplier = 2.2
        self.sl_multiplier = 1.7
        self.max_positions = 6
        
        self.bars_since_trade = 0
        self.min_bars = 10  # 50 min seulement!
        
        # Pyramiding
        self.consecutive_wins = 0
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 30:
            return 0
        
        # Cooldown court
        if self.bars_since_trade < self.min_bars:
            self.bars_since_trade += 1
            return 0
        
        if len(self.open_positions) >= self.max_positions:
            return 0
        
        # Indicateurs
        ema5 = self.indicators.calculate_ema(data['close'], 5)
        ema13 = self.indicators.calculate_ema(data['close'], 13)
        rsi = self.indicators.calculate_rsi(data['close'], 14)
        upper, middle, lower = self.indicators.calculate_bollinger_bands(data['close'], 20, 2.0)
        
        if ema5 is None or rsi is None or upper is None:
            self.bars_since_trade += 1
            return 0
        
        current_price = data['close'].iloc[-1]
        e5 = ema5.iloc[-1]
        e13 = ema13.iloc[-1]
        rsi_val = rsi.iloc[-1]
        
        # Momentum
        mom = data['close'].diff(3).iloc[-1]
        
        # Score d'achat
        buy_score = 0
        
        # 1. EMA trend
        if e5 > e13:
            buy_score += 1
        
        # 2. RSI
        if 30 < rsi_val < 60:
            buy_score += 1
        
        # 3. Bollinger
        if current_price < middle.iloc[-1]:
            buy_score += 1
        
        # 4. Momentum
        if mom > 0:
            buy_score += 1
        
        # 5. Prix action
        if data['close'].iloc[-1] > data['open'].iloc[-1]:
            buy_score += 1
        
        # Signal si ≥ 2/5 (permissif!)
        if buy_score >= 2:
            self.bars_since_trade = 0
            
            # Pyramiding: augmenter lot après wins
            if self.consecutive_wins >= 2:
                self.lot_size = min(self.base_lot * 1.3, 0.15)
            else:
                self.lot_size = self.base_lot
            
            return 1
        
        # Score de vente
        sell_score = 0
        
        if e5 < e13:
            sell_score += 1
        
        if 40 < rsi_val < 70:
            sell_score += 1
        
        if current_price > middle.iloc[-1]:
            sell_score += 1
        
        if mom < 0:
            sell_score += 1
        
        if data['close'].iloc[-1] < data['open'].iloc[-1]:
            sell_score += 1
        
        if sell_score >= 2:
            self.bars_since_trade = 0
            
            if self.consecutive_wins >= 2:
                self.lot_size = min(self.base_lot * 1.3, 0.15)
            else:
                self.lot_size = self.base_lot
            
            return -1
        
        self.bars_since_trade += 1
        return 0
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        # TP/SL
        if position.position_type == 'BUY':
            if current_price >= position.take_profit or current_price <= position.stop_loss:
                return True
        else:
            if current_price <= position.take_profit or current_price >= position.stop_loss:
                return True
        
        # Fermeture rapide sur profit
        profit = position.get_current_profit(current_price)
        if profit >= 4.0:  # $4+
            return True
        
        return False
    
    def close_position(self, position: Position, close_price: float):
        """Track wins for pyramiding."""
        super().close_position(position, close_price)
        
        if position.profit > 0:
            self.consecutive_wins += 1
        else:
            self.consecutive_wins = 0
    
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


def main():
    """Test hyper-active swing."""
    
    print("="*80)
    print("   ⚡ SWING HYPER-ACTIF - 1-2%/JOUR AVEC HAUTE FRÉQUENCE")
    print("   OBJECTIF: 1-2%/jour + 20-30 trades/mois")
    print("="*80)
    
    # Données réelles
    print("\n📥 Chargement GOLD 5M (données réelles)...")
    
    try:
        data = pd.read_csv('data/GOLD_5m.csv', index_col=0)
        data.columns = [c.lower() for c in data.columns]
        data.index = pd.to_datetime(data.index, utc=True).tz_localize(None)
        
        # 1 mois
        data = data.tail(8640)
        
        print(f"✅ {len(data)} barres (30 jours)")
        print(f"💰 ${data['close'].iloc[0]:.2f} → ${data['close'].iloc[-1]:.2f}")
        
    except Exception as e:
        print(f"❌ {e}")
        print("Utiliser données simulées...")
        
        np.random.seed(12345)
        dates = pd.date_range(start='2024-01-01', end='2024-02-01', freq='5min')
        n = len(dates)
        
        trend = np.linspace(0, 250, n)
        cycles = 60 * np.sin(np.linspace(0, 50*np.pi, n))
        noise = np.cumsum(np.random.randn(n) * 3.0)
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
        
        print(f"✅ {len(data)} barres simulées")
    
    # Stratégie
    print(f"\n⚡ Configuration Hyper-Active...")
    strategy = HyperActiveSwing(lot_size=0.10)
    
    print(f"   Lot Size: {strategy.lot_size} (10%)")
    print(f"   Pyramiding: x1.3 après 2 wins")
    print(f"   TP: {strategy.tp_multiplier}x ATR")
    print(f"   SL: {strategy.sl_multiplier}x ATR")
    print(f"   Conditions: ≥ 2/5 (PERMISSIF)")
    print(f"   Cooldown: {strategy.min_bars} barres (50 min)")
    
    # Risk
    risk_manager = RiskManager(
        initial_capital=10000,
        max_daily_loss=800,
        max_position_size=0.15,
        max_open_positions=6,
        max_drawdown_percent=35.0
    )
    
    # Backtest
    backtester = Backtester(strategy, initial_capital=10000)
    
    print(f"\n🔄 Running hyper-active swing...")
    print("="*80)
    
    results = backtester.run(data, risk_manager, verbose=True)
    
    # RÉSULTATS
    print("\n" + "="*80)
    print("   🏆 RÉSULTATS HYPER-ACTIVE SWING")
    print("="*80)
    
    print(f"\n💰 PERFORMANCE:")
    print(f"   Capital Initial:       ${results['initial_capital']:,.2f}")
    print(f"   Capital Final:         ${results['final_equity']:,.2f}")
    print(f"   Profit Net:            ${results['total_profit_$']:+,.2f}")
    print(f"   Return Total:          {results['total_return_%']:+.2f}%")
    
    print(f"\n📊 TRADING:")
    print(f"   Total Trades:          {results['total_trades']}")
    print(f"   Win Rate:              {results['win_rate_%']:.1f}%")
    print(f"   Profit Factor:         {results['profit_factor']:.2f}")
    print(f"   Max Drawdown:          {results['max_drawdown_%']:.2f}%")
    
    duration = results['duration_days']
    if duration > 0:
        daily_return = results['total_return_%'] / duration
        trades_per_day = results['total_trades'] / duration
        
        print(f"\n🎯 RENDEMENT JOURNALIER:")
        print(f"   {daily_return:+.2f}%/jour")
        print(f"   {trades_per_day:.1f} trades/jour")
        
        if daily_return >= 1.0 and daily_return <= 3.0:
            print(f"\n{'='*80}")
            print(f"   ✅✅✅ OBJECTIF 1-2%/JOUR ATTEINT! ✅✅✅")
            print(f"{'='*80}")
            
            print(f"\n🎉 SWING TRADING GÉNÈRE {daily_return:.2f}%/JOUR!")
            print(f"✅ Win Rate: {results['win_rate_%']:.1f}%")
            print(f"✅ Trades: {results['total_trades']}")
            
            monthly = daily_return * 30
            print(f"\n💰 AVEC $10,000:")
            print(f"   1 mois: ${10000 * (1 + monthly/100):,.2f} ({monthly:+.1f}%)")
            
            print(f"\n🏆 SWING TRADING OPTIMISÉ POUR 1-2%/JOUR!")
            
        elif daily_return >= 0.5:
            print(f"\n⚠️ Proche: {daily_return:.2f}%/jour")
        else:
            print(f"\n⚠️ {daily_return:.2f}%/jour")
    
    # Sauvegarder
    print(f"\n💾 Sauvegarde...")
    backtester.export_trades('hyperactive_swing_trades.csv')
    backtester.export_results('hyperactive_swing_results.csv')
    
    print("\n" + "="*80)
    
    return results


if __name__ == "__main__":
    try:
        results = main()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
