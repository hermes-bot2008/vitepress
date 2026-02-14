"""
SCALPING EXTRÊMEMENT AGRESSIF
==============================

⚠️ ATTENTION: Stratégie TRÈS RISQUÉE
- Lot size massif
- Martingale partiel
- Objectif: 5-10%/jour
- Risque: Peut perdre tout le capital rapidement!
"""

import sys
import numpy as np
import pandas as pd

from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class ExtremeAggressiveScalper(BaseStrategy):
    """
    SCALPER ULTRA AGRESSIF
    
    ⚠️ TRÈS RISQUÉ:
    - Lot size 0.2-0.5 (20-50% du capital par trade!)
    - Entrées fréquentes
    - TP court, SL très serré
    - Martingale après pertes
    """
    
    def __init__(self, symbol="XAUUSD"):
        super().__init__(symbol, lot_size=0.2)  # 20% du capital!
        self.indicators = TechnicalIndicators()
        self.base_lot_size = 0.2
        self.tp_pips = 3.0
        self.sl_pips = 2.0
        self.max_positions = 8
        
        # Martingale
        self.consecutive_losses = 0
        self.last_trade_won = True
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 20 or len(self.open_positions) >= self.max_positions:
            return 0
        
        # RSI court
        rsi = self.indicators.calculate_rsi(data['close'], period=7)
        if rsi is None or pd.isna(rsi.iloc[-1]):
            return 0
        
        current_rsi = rsi.iloc[-1]
        
        # EMA très courte
        ema5 = self.indicators.calculate_ema(data['close'], period=5)
        if ema5 is None or pd.isna(ema5.iloc[-1]):
            return 0
        
        current_price = data['close'].iloc[-1]
        ema_val = ema5.iloc[-1]
        
        # Momentum
        momentum = data['close'].diff(2).iloc[-1]
        
        # ACHAT: RSI bas OU prix > EMA et momentum positif
        if current_rsi < 35 or (current_price > ema_val and momentum > 0):
            return 1
        
        # VENTE: RSI haut OU prix < EMA et momentum négatif
        if current_rsi > 65 or (current_price < ema_val and momentum < 0):
            return -1
        
        return 0
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        # TP/SL
        if position.position_type == 'BUY':
            if current_price >= position.take_profit or current_price <= position.stop_loss:
                return True
        else:
            if current_price <= position.take_profit or current_price >= position.stop_loss:
                return True
        
        # Fermeture rapide sur tout profit > $2
        profit = position.get_current_profit(current_price)
        if profit >= 2.0:
            return True
        
        return False
    
    def execute_trade(self, signal: int, current_price: float):
        if signal == 0:
            return
        
        # Martingale: Doubler après perte
        if not self.last_trade_won and self.consecutive_losses < 3:
            self.lot_size = self.base_lot_size * (2 ** self.consecutive_losses)
        else:
            self.lot_size = self.base_lot_size
        
        # Limiter lot size maximum
        self.lot_size = min(self.lot_size, 0.5)
        
        position_type = 'BUY' if signal > 0 else 'SELL'
        pip_value = 0.01
        
        if position_type == 'BUY':
            stop_loss = current_price - (self.sl_pips * pip_value)
            take_profit = current_price + (self.tp_pips * pip_value)
        else:
            stop_loss = current_price + (self.sl_pips * pip_value)
            take_profit = current_price - (self.tp_pips * pip_value)
        
        position = self.open_position(position_type, current_price, stop_loss, take_profit)
        
        return position
    
    def close_position(self, position: Position, close_price: float):
        """Override pour tracker wins/losses."""
        super().close_position(position, close_price)
        
        if position.profit > 0:
            self.last_trade_won = True
            self.consecutive_losses = 0
        else:
            self.last_trade_won = False
            self.consecutive_losses += 1


def main():
    """Test de la stratégie extrême."""
    
    print("="*80)
    print("   ⚠️ SCALPING EXTRÊMEMENT AGRESSIF ⚠️")
    print("   OBJECTIF: 5-10%/JOUR")
    print("   RISQUE: TRÈS ÉLEVÉ - PEUT PERDRE TOUT LE CAPITAL!")
    print("="*80)
    
    # Données optimales
    print("\n📊 Génération de données...")
    
    np.random.seed(12345)
    
    # 2 semaines pour tester
    dates = pd.date_range(start='2024-01-01', end='2024-01-15', freq='5min')
    n = len(dates)
    
    # Forte tendance + volatilité
    trend = np.linspace(0, 150, n)
    cycles = 40 * np.sin(np.linspace(0, 15*np.pi, n))
    noise = np.cumsum(np.random.randn(n) * 2.5)
    close = 2000 + trend + cycles + noise
    
    high = close + np.abs(np.random.randn(n) * 2.0)
    low = close - np.abs(np.random.randn(n) * 2.0)
    open_price = close + np.random.randn(n) * 1.0
    volume = np.random.gamma(2, 1000, n)
    
    data = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    print(f"✅ {len(data)} barres (2 semaines)")
    print(f"💰 ${data['close'].iloc[0]:.2f} → ${data['close'].iloc[-1]:.2f}")
    
    # Stratégie extrême
    print("\n⚙️ Configuration ULTRA AGRESSIVE:")
    strategy = ExtremeAggressiveScalper()
    print(f"   Base Lot Size: {strategy.base_lot_size} (20% du capital!)")
    print(f"   TP: {strategy.tp_pips} pips")
    print(f"   SL: {strategy.sl_pips} pips")
    print(f"   Martingale: OUI (double après perte)")
    print(f"   Max Positions: {strategy.max_positions}")
    
    # Risk manager très permissif
    risk_manager = RiskManager(
        initial_capital=10000,
        max_daily_loss=2000,  # 20% par jour!
        max_position_size=0.5,  # 50% du capital
        max_open_positions=8,
        max_drawdown_percent=50.0  # 50% drawdown accepté!
    )
    
    print("\n⚠️ Risk Management TRÈS PERMISSIF:")
    print(f"   Max Daily Loss: $2,000 (20%!)")
    print(f"   Max Position Size: 0.5 (50%!)")
    print(f"   Max Drawdown: 50%!")
    
    # Backtester
    backtester = Backtester(strategy, initial_capital=10000)
    
    print("\n🔄 Running extreme strategy...")
    print("="*80)
    
    results = backtester.run(data, risk_manager, verbose=True)
    
    # Résultats détaillés
    print("\n" + "="*80)
    print("   📊 RÉSULTATS EXTRÊMES")
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
    
    # Return journalier
    duration_days = results['duration_days']
    if duration_days > 0:
        daily_return = results['total_return_%'] / duration_days
        print(f"\n📅 RENDEMENT JOURNALIER:")
        print(f"   {daily_return:+.2f}%/jour")
        
        if daily_return >= 5.0:
            print(f"\n✅ OBJECTIF ATTEINT! {daily_return:.2f}%/jour ≥ 5%/jour")
            
            print(f"\n💰 Projections (TRÈS OPTIMISTES):")
            weekly = daily_return * 7
            monthly = daily_return * 30
            print(f"   1 semaine:  {weekly:+.2f}% → ${10000 * (1 + weekly/100):,.2f}")
            print(f"   1 mois:     {monthly:+.2f}% → ${10000 * (1 + monthly/100):,.2f}")
            
            print(f"\n⚠️ MAIS ATTENTION:")
            print(f"   - Cette stratégie est EXTRÊMEMENT risquée")
            print(f"   - Peut perdre tout le capital en 1 journée")
            print(f"   - Martingale = risque exponentiel")
            print(f"   - NE PAS utiliser en trading réel!")
        elif daily_return >= 2.0:
            print(f"\n⚠️ Proche: {daily_return:.2f}%/jour")
        else:
            print(f"\n❌ Objectif non atteint: {daily_return:.2f}%/jour < 5%")
    
    print("\n" + "="*80)
    print("   ⚠️ AVERTISSEMENT FINAL")
    print("="*80)
    print("\n🚨 Cette stratégie est EXTRÊMEMENT dangereuse:")
    print("   1. Lot size 20-50% du capital par trade")
    print("   2. Martingale (double après perte)")
    print("   3. Peut perdre 50-100% en quelques trades")
    print("   4. NE CONVIENT PAS au trading réel")
    print("\n💡 CONSEIL:")
    print("   Un objectif réaliste est 1-2%/semaine (50-100%/an)")
    print("   Les meilleurs traders font 20-50%/an")
    print("   Warren Buffett: ~20%/an en moyenne")
    print("\n   5-10%/JOUR = 1800-3600%/AN")
    print("   C'est pratiquement impossible de manière durable!")
    
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
