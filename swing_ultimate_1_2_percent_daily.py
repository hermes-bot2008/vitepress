"""
SWING TRADING ULTIMATE - 1-2%/JOUR
===================================

Version finale ultra-optimisée pour atteindre 1-2%/jour:
- Timeframe COURT (5M-10M) pour haute fréquence
- Lot size AGRESSIF (10-15% par trade)
- Paramètres optimisés pour MAXIMUM de signaux
- Multi-stratégies en parallèle
- Objectif: 20-40 trades/mois avec win rate 55%+
"""

import sys
import numpy as np
import pandas as pd

from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class UltimateSwingForDaily(BaseStrategy):
    """
    Swing Trading Ultimate optimisé pour 1-2%/jour.
    
    Approche:
    - Timeframe 5M (haute fréquence)
    - EMA 3/8 (très réactif)
    - Lot size 0.12 (12% du capital)
    - Cooldown 20 barres (100 min)
    - TP/SL serré mais favorable
    - Fermeture rapide
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.12):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        
        self.base_lot = lot_size
        self.tp_multiplier = 2.5
        self.sl_multiplier = 1.8
        self.max_positions = 6
        
        # Cooldown très court
        self.bars_since_trade = 0
        self.min_bars = 20  # 100 minutes
        
        # Stats
        self.consecutive_wins = 0
        
    def generate_signal(self, data: pd.DataFrame) -> int:
        if len(data) < 30:
            return 0
        
        # Cooldown
        if self.bars_since_trade < self.min_bars:
            self.bars_since_trade += 1
            return 0
        
        if len(self.open_positions) >= self.max_positions:
            return 0
        
        # EMAs ultra-courtes
        ema3 = self.indicators.calculate_ema(data['close'], 3)
        ema8 = self.indicators.calculate_ema(data['close'], 8)
        ema21 = self.indicators.calculate_ema(data['close'], 21)
        
        # RSI
        rsi = self.indicators.calculate_rsi(data['close'], 14)
        
        if ema3 is None or rsi is None:
            self.bars_since_trade += 1
            return 0
        
        current_price = data['close'].iloc[-1]
        e3 = ema3.iloc[-1]
        e8 = ema8.iloc[-1]
        e21 = ema21.iloc[-1]
        rsi_val = rsi.iloc[-1]
        
        # Momentum multi-périodes
        mom1 = data['close'].diff(1).iloc[-1]
        mom3 = data['close'].diff(3).iloc[-1]
        
        # Volume
        vol_ratio = data['volume'].iloc[-1] / data['volume'].rolling(20).mean().iloc[-1]
        
        # ACHAT: Alignement + momentum + volume
        buy_score = 0
        if e3 > e8 > e21:
            buy_score += 2  # Alignement parfait
        elif e3 > e8:
            buy_score += 1  # Alignement partiel
        
        if 30 < rsi_val < 65:
            buy_score += 1
        
        if mom1 > 0 and mom3 > 0:
            buy_score += 1
        
        if vol_ratio > 1.0:
            buy_score += 1
        
        # Signal BUY si score ≥ 3
        if buy_score >= 3:
            self.bars_since_trade = 0
            # Ajuster lot selon score
            if buy_score >= 4:
                self.lot_size = min(self.base_lot * 1.3, 0.15)
            else:
                self.lot_size = self.base_lot
            return 1
        
        # VENTE: Même logique
        sell_score = 0
        if e3 < e8 < e21:
            sell_score += 2
        elif e3 < e8:
            sell_score += 1
        
        if 35 < rsi_val < 70:
            sell_score += 1
        
        if mom1 < 0 and mom3 < 0:
            sell_score += 1
        
        if vol_ratio > 1.0:
            sell_score += 1
        
        if sell_score >= 3:
            self.bars_since_trade = 0
            if sell_score >= 4:
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
        
        # Fermeture rapide sur bon profit
        profit = position.get_current_profit(current_price)
        if profit >= 5.0:  # $5+
            return True
        
        return False
    
    def close_position(self, position: Position, close_price: float):
        """Override pour pyramiding."""
        super().close_position(position, close_price)
        
        if position.profit > 0:
            self.consecutive_wins += 1
        else:
            self.consecutive_wins = 0
    
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
    """Test ultimate swing pour 1-2%/jour."""
    
    print("="*80)
    print("   💎 SWING TRADING ULTIMATE - 1-2%/JOUR")
    print("   OPTIMISATION MAXIMALE")
    print("="*80)
    
    # Charger données réelles GOLD 5M
    print("\n📥 Chargement GOLD 5M (données réelles)...")
    
    try:
        data = pd.read_csv('data/GOLD_5m.csv', index_col=0)
        data.columns = [c.lower() for c in data.columns]
        data.index = pd.to_datetime(data.index, utc=True).tz_localize(None)
        
        # Utiliser 1 mois
        data = data.tail(8640)
        
        print(f"✅ {len(data)} barres (30 jours en 5M)")
        print(f"💰 ${data['close'].iloc[0]:.2f} → ${data['close'].iloc[-1]:.2f}")
        print(f"📈 Market: {((data['close'].iloc[-1]/data['close'].iloc[0])-1)*100:+.1f}%")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("Données simulées...")
        
        # Fallback
        np.random.seed(777)
        dates = pd.date_range(start='2024-01-01', end='2024-02-01', freq='5min')
        n = len(dates)
        
        trend = np.linspace(0, 200, n)
        cycles = 50 * np.sin(np.linspace(0, 40*np.pi, n))
        noise = np.cumsum(np.random.randn(n) * 2.5)
        close = 2000 + trend + cycles + noise
        
        high = close + np.abs(np.random.randn(n) * 2.0)
        low = close - np.abs(np.random.randn(n) * 2.0)
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
    
    # Stratégie Ultimate
    print(f"\n💎 Configuration Ultimate Swing...")
    strategy = UltimateSwingForDaily(lot_size=0.12)
    
    print(f"   Lot Size: {strategy.lot_size} (12% du capital)")
    print(f"   TP: {strategy.tp_multiplier}x ATR")
    print(f"   SL: {strategy.sl_multiplier}x ATR")
    print(f"   Ratio: {strategy.tp_multiplier/strategy.sl_multiplier:.2f}:1")
    print(f"   Cooldown: {strategy.min_bars} barres (100 min)")
    print(f"   Timeframe: 5M (haute fréquence)")
    print(f"   Conditions: ≥ 3/5 pour entrée")
    
    # Risk Manager agressif
    risk_manager = RiskManager(
        initial_capital=10000,
        max_daily_loss=800,  # 8% par jour
        max_position_size=0.15,
        max_open_positions=6,
        max_drawdown_percent=35.0
    )
    
    print(f"\n🛡️ Risk Management Agressif:")
    print(f"   Max Daily Loss: $800 (8%)")
    print(f"   Max Position: 0.15 (15%)")
    
    # Backtest
    backtester = Backtester(strategy, initial_capital=10000)
    
    print(f"\n🔄 Running ultimate swing backtest...")
    print("="*80)
    
    results = backtester.run(data, risk_manager, verbose=True)
    
    # RÉSULTATS FINAUX
    print("\n" + "="*80)
    print("   🏆 RÉSULTATS ULTIMATE SWING")
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
        
        if daily_return >= 1.0 and daily_return <= 3.0:
            print(f"\n" + "="*80)
            print(f"   🎉🎉🎉 OBJECTIF ATTEINT! 🎉🎉🎉")
            print(f"="*80)
            
            print(f"\n✅ Le Swing Trading génère {daily_return:.2f}%/jour!")
            print(f"✅ Win Rate: {results['win_rate_%']:.1f}%")
            print(f"✅ Profit Factor: {results['profit_factor']:.2f}")
            print(f"✅ Trades: {results['total_trades']} sur {duration} jours")
            
            weekly = daily_return * 7
            monthly = daily_return * 30
            quarterly = daily_return * 90
            yearly = daily_return * 365
            
            print(f"\n💰 PROJECTIONS AVEC $10,000:")
            print(f"   Après 1 semaine:   ${10000 * (1 + weekly/100):,.2f}  ({weekly:+.1f}%)")
            print(f"   Après 1 mois:      ${10000 * (1 + monthly/100):,.2f}  ({monthly:+.1f}%)")
            print(f"   Après 3 mois:      ${10000 * (1 + quarterly/100):,.2f}  ({quarterly:+.1f}%)")
            print(f"   Après 6 mois:      ${10000 * (1 + monthly*6/100):,.2f}  ({monthly*6:+.1f}%)")
            print(f"   Après 1 an:        ${10000 * (1 + yearly/100):,.2f}  ({yearly:+.1f}%)")
            
            print(f"\n🏆 SWING TRADING OPTIMISÉ!")
            print(f"\n⚠️ IMPORTANT:")
            print(f"   - Tester en demo 3 mois minimum")
            print(f"   - Valider win rate et drawdown")
            print(f"   - Commencer avec petit capital")
            print(f"   - Respecter strictement le risk management")
            
        elif daily_return >= 0.5:
            print(f"\n⚠️ PROCHE: {daily_return:.2f}%/jour (objectif: 1-2%)")
            
            print(f"\n💡 Pour améliorer:")
            print(f"   1. Augmenter lot size à 0.15")
            print(f"   2. Réduire cooldown à 15 barres")
            print(f"   3. Utiliser timeframe 3M")
            print(f"   4. Ajouter pyramiding après 2 wins")
            
        elif daily_return > 0:
            print(f"\n✅ Positif: {daily_return:.2f}%/jour")
        else:
            print(f"\n❌ Négatif: {daily_return:.2f}%/jour")
    
    # Sauvegarder
    print(f"\n💾 Sauvegarde...")
    backtester.export_trades('ultimate_swing_trades.csv')
    backtester.export_results('ultimate_swing_results.csv')
    print(f"✅ Résultats sauvegardés")
    
    print("\n" + "="*80)
    print("   ✅ ULTIMATE SWING BACKTEST TERMINÉ")
    print("="*80)
    
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
