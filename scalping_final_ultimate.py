"""
SCALPING FINAL ULTIMATE - SYSTÈME COMPLET
==========================================

Dernière tentative pour atteindre 1-2%/jour avec:
- Haute fréquence (20-50 trades/jour)
- Filtrage intelligent mais pas trop strict
- Pyramiding sur tendances fortes
- Lot size progressif
- Win rate ciblé: 55-60%
- Ratio R:R: 1.5-2:1
"""

import sys
import numpy as np
import pandas as pd
from typing import Dict

from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class FinalUltimateScalper(BaseStrategy):
    """
    Scalper Final Ultimate
    
    Approche équilibrée:
    - Signaux fréquents mais filtrés
    - 3 systèmes combinés (Trend, Mean Reversion, Breakout)
    - Pyramiding intelligent
    - Gestion dynamique du risque
    """
    
    def __init__(self, symbol="XAUUSD"):
        super().__init__(symbol, lot_size=0.04)
        self.indicators = TechnicalIndicators()
        
        self.base_lot = 0.04
        self.tp_pips = 3.0
        self.sl_pips = 2.0
        self.max_positions = 10
        
        # État
        self.trend_direction = 0
        self.last_signal_price = 0
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        
    def analyze_trend(self, data: pd.DataFrame) -> int:
        """Analyse la tendance principale."""
        if len(data) < 50:
            return 0
        
        # EMAs pour la tendance
        ema8 = self.indicators.calculate_ema(data['close'], 8)
        ema21 = self.indicators.calculate_ema(data['close'], 21)
        ema50 = self.indicators.calculate_ema(data['close'], 50)
        
        if ema8 is None:
            return 0
        
        e8 = ema8.iloc[-1]
        e21 = ema21.iloc[-1]
        e50 = ema50.iloc[-1]
        
        # Tendance haussière forte
        if e8 > e21 > e50:
            return 1
        
        # Tendance baissière forte
        if e8 < e21 < e50:
            return -1
        
        return 0
    
    def detect_entry_opportunity(self, data: pd.DataFrame) -> Dict:
        """Détecte 3 types d'opportunités."""
        
        if len(data) < 50:
            return {'type': None, 'strength': 0}
        
        current_price = data['close'].iloc[-1]
        
        # Type 1: TREND FOLLOWING
        trend = self.analyze_trend(data)
        rsi = self.indicators.calculate_rsi(data['close'], 14)
        
        if rsi is not None and not pd.isna(rsi.iloc[-1]):
            rsi_val = rsi.iloc[-1]
            
            # Pullback dans tendance haussière
            if trend == 1 and 35 < rsi_val < 45:
                return {'type': 'TREND_PULLBACK_BUY', 'strength': 3}
            
            # Pullback dans tendance baissière
            if trend == -1 and 55 < rsi_val < 65:
                return {'type': 'TREND_PULLBACK_SELL', 'strength': 3}
        
        # Type 2: MEAN REVERSION
        upper, middle, lower = self.indicators.calculate_bollinger_bands(
            data['close'], 20, 2.0
        )
        
        if upper is not None:
            # Oversold bounce
            if current_price <= lower.iloc[-1] * 1.001:
                return {'type': 'MEAN_REVERSION_BUY', 'strength': 2}
            
            # Overbought reverse
            if current_price >= upper.iloc[-1] * 0.999:
                return {'type': 'MEAN_REVERSION_SELL', 'strength': 2}
        
        # Type 3: BREAKOUT
        recent_high = data['high'].tail(20).max()
        recent_low = data['low'].tail(20).min()
        volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].rolling(20).mean().iloc[-1]
        
        # Breakout haussier avec volume
        if current_price > recent_high * 0.999 and volume > avg_volume * 1.5:
            return {'type': 'BREAKOUT_BUY', 'strength': 2}
        
        # Breakout baissier avec volume
        if current_price < recent_low * 1.001 and volume > avg_volume * 1.5:
            return {'type': 'BREAKOUT_SELL', 'strength': 2}
        
        return {'type': None, 'strength': 0}
    
    def generate_signal(self, data: pd.DataFrame) -> int:
        """Génère un signal basé sur opportunités détectées."""
        if len(data) < 50 or len(self.open_positions) >= self.max_positions:
            return 0
        
        # Détecter opportunité
        opportunity = self.detect_entry_opportunity(data)
        
        if opportunity['type'] is None:
            return 0
        
        # Éviter trades trop proches
        current_price = data['close'].iloc[-1]
        if self.last_signal_price > 0:
            price_diff = abs(current_price - self.last_signal_price) / current_price
            if price_diff < 0.001:  # < 0.1%
                return 0
        
        # Ajuster lot size selon:
        # 1. Force du signal
        # 2. Série de gains/pertes
        strength = opportunity['strength']
        
        if self.consecutive_wins >= 2:
            self.lot_size = self.base_lot * 1.5  # Pyramiding
        elif self.consecutive_losses >= 2:
            self.lot_size = self.base_lot * 0.5  # Réduire risque
        else:
            self.lot_size = self.base_lot
        
        # Ajuster selon force
        self.lot_size *= (strength / 2.0)
        self.lot_size = min(self.lot_size, 0.15)  # Max 15%
        
        # Signaux
        if 'BUY' in opportunity['type']:
            self.last_signal_price = current_price
            return 1
        
        if 'SELL' in opportunity['type']:
            self.last_signal_price = current_price
            return -1
        
        return 0
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        # TP/SL
        if position.position_type == 'BUY':
            if current_price >= position.take_profit:
                return True
            if current_price <= position.stop_loss:
                return True
        else:
            if current_price <= position.take_profit:
                return True
            if current_price >= position.stop_loss:
                return True
        
        # Fermeture rapide sur bon profit
        profit = position.get_current_profit(current_price)
        if profit >= 2.0:  # $2+
            return True
        
        return False
    
    def close_position(self, position: Position, close_price: float):
        """Override pour tracker séries."""
        super().close_position(position, close_price)
        
        if position.profit > 0:
            self.consecutive_wins += 1
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
            self.consecutive_wins = 0
    
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
    """Test final ultimate."""
    
    print("="*80)
    print("   🚀 SCALPING FINAL ULTIMATE - SYSTÈME COMPLET")
    print("   OBJECTIF: 1-2% PAR JOUR")
    print("   3 SYSTÈMES COMBINÉS | PYRAMIDING | LOT ADAPTATIF")
    print("="*80)
    
    # Données 5min (meilleur que 1min pour backtesting)
    print("\n📊 Génération de données 5 MINUTES optimales...")
    
    np.random.seed(12345)
    
    # 1 mois = ~8,640 barres 5min
    dates = pd.date_range(start='2024-01-01', end='2024-02-01', freq='5min')
    n = len(dates)
    
    # Prix avec forte tendance ET cycles (opportunités variées)
    trend = np.linspace(0, 200, n)  # Forte tendance
    cycles_short = 30 * np.sin(np.linspace(0, 40*np.pi, n))
    cycles_long = 50 * np.sin(np.linspace(0, 8*np.pi, n))
    noise = np.cumsum(np.random.randn(n) * 2.0)
    close = 2000 + trend + cycles_short + cycles_long + noise
    
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
    
    print(f"✅ {len(data)} barres (31 jours)")
    print(f"💰 ${data['close'].iloc[0]:.2f} → ${data['close'].iloc[-1]:.2f}")
    print(f"📈 Market: +{((data['close'].iloc[-1]/data['close'].iloc[0])-1)*100:.1f}%")
    
    # Stratégie
    print("\n🎯 Configuration Scalper Final Ultimate...")
    strategy = FinalUltimateScalper()
    
    print(f"   Base Lot: {strategy.base_lot}")
    print(f"   Lot Adaptatif: 0.02 → 0.15 (pyramiding)")
    print(f"   TP: {strategy.tp_pips} pips | SL: {strategy.sl_pips} pips")
    print(f"   3 Systèmes: Trend + Mean Reversion + Breakout")
    print(f"   Pyramiding: Augmente après 2 wins")
    print(f"   Defensive: Réduit après 2 losses")
    
    # Risk manager
    risk_manager = RiskManager(
        initial_capital=10000,
        max_daily_loss=500,  # 5% par jour
        max_position_size=0.15,
        max_open_positions=10,
        max_drawdown_percent=30.0
    )
    
    print(f"\n🛡️ Risk Management Agressif:")
    print(f"   Max Daily Loss: $500 (5%)")
    print(f"   Max Position Size: 0.15 (15%)")
    print(f"   Max Positions: 10")
    
    # Backtest
    backtester = Backtester(strategy, initial_capital=10000)
    
    print("\n🔄 Running final ultimate backtest...")
    print("="*80)
    
    results = backtester.run(data, risk_manager, verbose=True)
    
    # RÉSULTATS FINAUX
    print("\n" + "="*80)
    print("   🏆 RÉSULTATS FINAUX - ULTIMATE SCALPER")
    print("="*80)
    
    print(f"\n💰 PERFORMANCE:")
    print(f"   Capital Initial:       ${results['initial_capital']:,.2f}")
    print(f"   Capital Final:         ${results['final_equity']:,.2f}")
    print(f"   Profit Net:            ${results['total_profit_$']:+,.2f}")
    print(f"   Return Total:          {results['total_return_%']:+.2f}%")
    
    print(f"\n📊 STATISTIQUES:")
    print(f"   Total Trades:          {results['total_trades']}")
    print(f"   Win Rate:              {results['win_rate_%']:.1f}%")
    print(f"   Profit Factor:         {results['profit_factor']:.2f}")
    print(f"   Espérance:             ${results['expectancy']:+,.2f}")
    print(f"   Max Drawdown:          {results['max_drawdown_%']:.2f}%")
    print(f"   Sharpe Ratio:          {results['sharpe_ratio']:.3f}")
    
    duration = results['duration_days']
    if duration > 0:
        daily_return = results['total_return_%'] / duration
        trades_per_day = results['total_trades'] / duration
        
        print(f"\n🎯 PERFORMANCES JOURNALIÈRES:")
        print(f"   Return/Jour:           {daily_return:+.2f}%")
        print(f"   Trades/Jour:           {trades_per_day:.1f}")
        
        if daily_return >= 1.0 and daily_return <= 2.0:
            print(f"\n✅✅✅ OBJECTIF ATTEINT! ✅✅✅")
            print(f"\n🏆 Le système génère 1-2%/jour!")
            
            weekly = daily_return * 7
            monthly = daily_return * 30
            
            print(f"\n💰 PROJECTIONS AVEC $10,000:")
            print(f"   Après 1 semaine:   ${10000 * (1 + weekly/100):,.2f}  ({weekly:+.1f}%)")
            print(f"   Après 1 mois:      ${10000 * (1 + monthly/100):,.2f}  ({monthly:+.1f}%)")
            print(f"   Après 3 mois:      ${10000 * (1 + monthly*3/100):,.2f}  ({monthly*3:+.1f}%)")
            print(f"   Après 6 mois:      ${10000 * (1 + monthly*6/100):,.2f}  ({monthly*6:+.1f}%)")
            print(f"   Après 1 an:        ${10000 * (1 + monthly*12/100):,.2f}  ({monthly*12:+.1f}%)")
            
        elif daily_return >= 0.5:
            print(f"\n⚠️ Proche: {daily_return:.2f}%/jour (objectif: 1-2%)")
            
            monthly = daily_return * 30
            print(f"\n💰 PROJECTION MENSUELLE:")
            print(f"   1 mois: {monthly:+.1f}% → ${10000 * (1 + monthly/100):,.2f}")
            
        elif daily_return > 0:
            print(f"\n⚠️ Positif mais faible: {daily_return:.2f}%/jour")
        else:
            print(f"\n❌ Négatif: {daily_return:.2f}%/jour")
    
    # Évaluation finale
    print(f"\n⭐ ÉVALUATION FINALE:")
    print(f"-"*80)
    
    score = 0
    
    if results['total_return_%'] > 20:
        score += 3
        print(f"✅ Excellente rentabilité (+{results['total_return_%']:.1f}%)")
    elif results['total_return_%'] > 10:
        score += 2
        print(f"✅ Bonne rentabilité (+{results['total_return_%']:.1f}%)")
    elif results['total_return_%'] > 0:
        score += 1
        print(f"⚠️ Rentabilité faible (+{results['total_return_%']:.1f}%)")
    else:
        print(f"❌ Perte ({results['total_return_%']:.1f}%)")
    
    if results['win_rate_%'] >= 55:
        score += 2
        print(f"✅ Excellent win rate ({results['win_rate_%']:.1f}%)")
    elif results['win_rate_%'] >= 45:
        score += 1
        print(f"⚠️ Win rate acceptable ({results['win_rate_%']:.1f}%)")
    else:
        print(f"❌ Win rate faible ({results['win_rate_%']:.1f}%)")
    
    if results['profit_factor'] >= 1.5:
        score += 3
        print(f"✅ Excellent PF ({results['profit_factor']:.2f})")
    elif results['profit_factor'] >= 1.2:
        score += 2
        print(f"✅ Bon PF ({results['profit_factor']:.2f})")
    elif results['profit_factor'] > 1.0:
        score += 1
        print(f"⚠️ PF acceptable ({results['profit_factor']:.2f})")
    else:
        print(f"❌ PF insuffisant ({results['profit_factor']:.2f})")
    
    if results['total_trades'] >= 20:
        score += 2
        print(f"✅ Bonne fréquence ({results['total_trades']} trades)")
    elif results['total_trades'] >= 10:
        score += 1
        print(f"⚠️ Fréquence acceptable ({results['total_trades']} trades)")
    else:
        print(f"❌ Fréquence trop faible ({results['total_trades']} trades)")
    
    print(f"\n🏆 SCORE GLOBAL: {score}/10")
    
    if score >= 8:
        print(f"\n💎 SYSTÈME EXCELLENT - Objectif atteint!")
    elif score >= 6:
        print(f"\n✅ SYSTÈME BON - Quelques optimisations possibles")
    elif score >= 4:
        print(f"\n⚠️ SYSTÈME ACCEPTABLE - Optimisations requises")
    else:
        print(f"\n❌ SYSTÈME À REVOIR")
    
    # Sauvegarder
    print(f"\n💾 Sauvegarde des résultats...")
    backtester.export_trades('ultimate_trades.csv')
    backtester.export_results('ultimate_results.csv')
    print(f"✅ Sauvegardé: ultimate_trades.csv, ultimate_results.csv")
    
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
