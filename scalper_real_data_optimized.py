"""
SCALPER OPTIMISÉ POUR DONNÉES RÉELLES
======================================

Version simplifiée mais efficace sur données réelles:
- Seuils permissifs pour plus de trades
- Lot size modéré (2-3%)
- Indicateurs simples mais robustes
- Objectif: 0.5-1.5%/jour réaliste
"""

import sys
import pandas as pd
import numpy as np

from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class RealDataScalper(BaseStrategy):
    """
    Scalper optimisé pour données réelles.
    
    Approche équilibrée:
    - Indicateurs robustes
    - Filtrage intelligent
    - Frequency modérée (2-5 trades/jour)
    - Win rate visé: 55%+
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.03):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        
        self.tp_pips = 3.5
        self.sl_pips = 2.5
        self.max_positions = 5
        
        # Cooldown
        self.bars_since_trade = 0
        self.min_bars = 10  # 50 min entre trades
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        """Génère des signaux avec filtrage équilibré."""
        if len(data) < 50:
            return 0
        
        # Cooldown
        if self.bars_since_trade < self.min_bars:
            self.bars_since_trade += 1
            return 0
        
        # Positions
        if len(self.open_positions) >= self.max_positions:
            return 0
        
        # Indicateurs
        rsi = self.indicators.calculate_rsi(data['close'], 14)
        ema_fast = self.indicators.calculate_ema(data['close'], 10)
        ema_slow = self.indicators.calculate_ema(data['close'], 30)
        upper, middle, lower = self.indicators.calculate_bollinger_bands(data['close'], 20, 2.0)
        
        if rsi is None or ema_fast is None or upper is None:
            self.bars_since_trade += 1
            return 0
        
        current_price = data['close'].iloc[-1]
        rsi_val = rsi.iloc[-1]
        ema_f = ema_fast.iloc[-1]
        ema_s = ema_slow.iloc[-1]
        
        # Volume
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].rolling(20).mean().iloc[-1]
        
        # ACHAT: Conditions multiples
        buy_conditions = 0
        
        # RSI oversold
        if rsi_val < 40:
            buy_conditions += 1
        
        # Trend
        if ema_f > ema_s:
            buy_conditions += 1
        
        # Bollinger
        if current_price <= middle.iloc[-1]:
            buy_conditions += 1
        
        # Volume
        if current_volume > avg_volume:
            buy_conditions += 1
        
        # Momentum
        if data['close'].diff(3).iloc[-1] > 0:
            buy_conditions += 1
        
        # Signal BUY si ≥ 3/5 conditions
        if buy_conditions >= 3:
            self.bars_since_trade = 0
            return 1
        
        # VENTE: Conditions multiples
        sell_conditions = 0
        
        if rsi_val > 60:
            sell_conditions += 1
        
        if ema_f < ema_s:
            sell_conditions += 1
        
        if current_price >= middle.iloc[-1]:
            sell_conditions += 1
        
        if current_volume > avg_volume:
            sell_conditions += 1
        
        if data['close'].diff(3).iloc[-1] < 0:
            sell_conditions += 1
        
        # Signal SELL si ≥ 3/5 conditions
        if sell_conditions >= 3:
            self.bars_since_trade = 0
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
        
        # Take profit rapide sur $3+
        profit = position.get_current_profit(current_price)
        if profit >= 3.0:
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
    """Test sur données réelles."""
    
    print("="*80)
    print("   💎 SCALPER OPTIMISÉ - TEST SUR DONNÉES RÉELLES")
    print("   OBJECTIF: 0.5-1.5%/JOUR (RÉALISTE)")
    print("="*80)
    
    # Charger données réelles
    print("\n📥 Chargement GOLD 5M (données réelles)...")
    
    try:
        data = pd.read_csv('data/GOLD_5m.csv', index_col=0)
        data.columns = [c.lower().replace(' ', '_') for c in data.columns]
        data.index = pd.to_datetime(data.index, utc=True).tz_localize(None)
        
        # Utiliser 1 mois de données
        data = data.tail(8640)  # 1 mois de 5M
        
        print(f"✅ {len(data)} barres chargées")
        print(f"📅 {data.index[0]} → {data.index[-1]}")
        print(f"💰 ${data['close'].iloc[0]:.2f} → ${data['close'].iloc[-1]:.2f}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("Lancer d'abord: python3 download_real_data.py")
        return None
    
    # Stratégie
    print(f"\n⚙️ Configuration Scalper Optimisé...")
    strategy = RealDataScalper(lot_size=0.03)
    
    print(f"   Lot Size: {strategy.lot_size} (3% du capital)")
    print(f"   TP: {strategy.tp_pips} pips | SL: {strategy.sl_pips} pips")
    print(f"   Ratio: {strategy.tp_pips/strategy.sl_pips:.2f}:1")
    print(f"   Conditions: ≥ 3/5 indicateurs")
    print(f"   Cooldown: 50 minutes")
    
    # Risk Manager
    risk_manager = RiskManager(
        initial_capital=10000,
        max_daily_loss=300,
        max_position_size=0.08,
        max_open_positions=5,
        max_drawdown_percent=20.0
    )
    
    # Backtest
    backtester = Backtester(strategy, initial_capital=10000)
    
    print(f"\n🔄 Running sur DONNÉES RÉELLES...")
    print("="*80)
    
    results = backtester.run(data, risk_manager, verbose=True)
    
    # RÉSULTATS
    print("\n" + "="*80)
    print("   📊 RÉSULTATS FINAUX SUR DONNÉES RÉELLES")
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
    print(f"   Sharpe Ratio:          {results['sharpe_ratio']:.3f}")
    
    duration = results['duration_days']
    if duration > 0:
        daily_return = results['total_return_%'] / duration
        trades_per_day = results['total_trades'] / duration
        
        print(f"\n🎯 RENDEMENT JOURNALIER:")
        print(f"   {daily_return:+.2f}%/jour")
        print(f"   {trades_per_day:.1f} trades/jour")
        
        if daily_return >= 0.5 and daily_return <= 2.0:
            print(f"\n✅✅✅ OBJECTIF ATTEINT! ✅✅✅")
            print(f"\n🎉 Le système génère {daily_return:.2f}%/jour sur DONNÉES RÉELLES!")
            
            monthly = daily_return * 30
            print(f"\n💰 PROJECTIONS:")
            print(f"   1 mois: {monthly:+.1f}% → ${10000 * (1 + monthly/100):,.2f}")
            
        elif daily_return > 0:
            print(f"\n✅ POSITIF: {daily_return:.2f}%/jour")
        else:
            print(f"\n❌ NÉGATIF: {daily_return:.2f}%/jour")
    
    # Sauvegarder
    print(f"\n💾 Sauvegarde...")
    backtester.export_trades('real_data_trades.csv')
    backtester.export_results('real_data_results.csv')
    
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
