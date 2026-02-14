"""
Backtest Simplifié avec Signaux Plus Actifs
============================================
"""

import sys
import numpy as np
import pandas as pd
from datetime import datetime

from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.utils.data_loader import DataLoader
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class SimpleScalper(BaseStrategy):
    """Version simplifiée du scalper avec signaux plus actifs."""
    
    def __init__(self, symbol="XAUUSD", lot_size=0.01, tp_pips=2.0, sl_pips=3.0):
        super().__init__(symbol, lot_size)
        self.tp_pips = tp_pips
        self.sl_pips = sl_pips
        self.indicators = TechnicalIndicators()
        self.trade_cooldown = 0
    
    def generate_signal(self, data: pd.DataFrame) -> int:
        """Génère des signaux basés sur RSI et MA simples."""
        if len(data) < 20:
            return 0
        
        # Cooldown entre les trades
        if self.trade_cooldown > 0:
            self.trade_cooldown -= 1
            return 0
        
        # Limiter le nombre de positions ouvertes
        if len(self.open_positions) >= 3:
            return 0
        
        # Calculer RSI
        rsi = self.indicators.calculate_rsi(data['close'], period=14)
        if rsi is None or pd.isna(rsi.iloc[-1]):
            return 0
        
        current_rsi = rsi.iloc[-1]
        
        # Calculer MA courte et longue
        ma_short = data['close'].rolling(5).mean()
        ma_long = data['close'].rolling(20).mean()
        
        if pd.isna(ma_short.iloc[-1]) or pd.isna(ma_long.iloc[-1]):
            return 0
        
        current_price = data['close'].iloc[-1]
        
        # Signal d'achat: RSI < 40 et prix > MA courte > MA longue
        if current_rsi < 40 and ma_short.iloc[-1] > ma_long.iloc[-1]:
            self.trade_cooldown = 5  # Cooldown de 5 barres
            return 1
        
        # Signal de vente: RSI > 60 et prix < MA courte < MA longue
        if current_rsi > 60 and ma_short.iloc[-1] < ma_long.iloc[-1]:
            self.trade_cooldown = 5
            return -1
        
        return 0
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        """Ferme au TP ou SL."""
        if position.position_type == 'BUY':
            if current_price >= position.take_profit or current_price <= position.stop_loss:
                return True
        else:
            if current_price <= position.take_profit or current_price >= position.stop_loss:
                return True
        return False
    
    def execute_trade(self, signal: int, current_price: float):
        """Execute un trade."""
        if signal == 0:
            return
        
        position_type = 'BUY' if signal > 0 else 'SELL'
        
        # Calculer SL et TP
        pip_value = 0.01
        if position_type == 'BUY':
            stop_loss = current_price - (self.sl_pips * pip_value)
            take_profit = current_price + (self.tp_pips * pip_value)
        else:
            stop_loss = current_price + (self.sl_pips * pip_value)
            take_profit = current_price - (self.tp_pips * pip_value)
        
        position = self.open_position(
            position_type=position_type,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        return position


def run_backtest():
    """Lance le backtest simplifié."""
    
    print("="*70)
    print("   🚀 QUANTDESK ULTRA - BACKTEST SIMPLIFIÉ")
    print("="*70)
    
    # Générer des données
    print("\n📊 Génération des données...")
    data_loader = DataLoader()
    
    np.random.seed(42)  # Pour résultats reproductibles
    data = data_loader.generate_sample_data(
        start_date='2024-01-01',
        end_date='2024-03-31',
        freq='1h',  # Hourly pour moins de données
        initial_price=2000.0,
        volatility=0.005  # Plus de volatilité pour plus de signaux
    )
    
    print(f"✅ {len(data)} barres générées")
    print(f"📅 Période: {data.index[0]} à {data.index[-1]}")
    
    # Créer la stratégie simple
    print("\n⚙️ Configuration de la stratégie...")
    strategy = SimpleScalper(
        symbol="XAUUSD",
        lot_size=0.01,
        tp_pips=2.0,
        sl_pips=3.0
    )
    
    # Risk manager
    print("⚙️ Configuration du Risk Manager...")
    risk_manager = RiskManager(
        initial_capital=10000.0,
        max_daily_loss=200.0,
        max_position_size=0.1,
        max_open_positions=5
    )
    
    # Backtester
    backtester = Backtester(
        strategy=strategy,
        initial_capital=10000.0
    )
    
    # Lancer le backtest
    print("\n🔄 Lancement du backtest...")
    print("="*70)
    
    results = backtester.run(
        data=data,
        risk_manager=risk_manager,
        verbose=True
    )
    
    # Afficher les résultats détaillés
    print("\n" + "="*70)
    print("   📊 RÉSULTATS DÉTAILLÉS")
    print("="*70)
    
    print("\n💰 PERFORMANCE FINANCIÈRE")
    print("-"*70)
    print(f"Capital Initial:           ${results['initial_capital']:,.2f}")
    print(f"Capital Final:             ${results['final_equity']:,.2f}")
    print(f"Profit Net:                ${results['total_profit_$']:+,.2f}")
    print(f"Retour sur Investment:     {results['total_return_%']:+.2f}%")
    
    print("\n📊 STATISTIQUES DE TRADING")
    print("-"*70)
    print(f"Total de Trades:           {results['total_trades']}")
    print(f"Trades Gagnants:           {results['winning_trades']}")
    print(f"Trades Perdants:           {results['losing_trades']}")
    print(f"Taux de Réussite:          {results['win_rate_%']:.2f}%")
    print(f"Profit Factor:             {results['profit_factor']:.2f}")
    
    print("\n🎯 ANALYSE DES TRADES")
    print("-"*70)
    print(f"Profit Moyen par Trade:    ${results['avg_profit_per_trade']:+,.2f}")
    print(f"Gain Moyen:                ${results['avg_win']:,.2f}")
    print(f"Perte Moyenne:             ${results['avg_loss']:,.2f}")
    print(f"Plus Grand Gain:           ${results['biggest_win']:,.2f}")
    print(f"Plus Grande Perte:         ${results['biggest_loss']:,.2f}")
    
    print("\n📉 MÉTRIQUES DE RISQUE")
    print("-"*70)
    print(f"Sharpe Ratio:              {results['sharpe_ratio']:.3f}")
    print(f"Sortino Ratio:             {results['sortino_ratio']:.3f}")
    print(f"Max Drawdown:              {results['max_drawdown_%']:.2f}%")
    
    # Évaluation
    print("\n⭐ ÉVALUATION")
    print("-"*70)
    
    score = 0
    
    if results['total_return_%'] > 0:
        score += 2
        print("✅ Stratégie profitable")
    else:
        print("❌ Stratégie perdante")
    
    if results['win_rate_%'] > 50:
        score += 2
        print("✅ Bon taux de réussite")
    else:
        print("⚠️ Taux de réussite < 50%")
    
    if results['profit_factor'] > 1.0:
        score += 2
        print("✅ Profit factor positif")
    else:
        print("⚠️ Profit factor < 1.0")
    
    if results['max_drawdown_%'] < 20:
        score += 2
        print("✅ Drawdown contrôlé")
    else:
        print("⚠️ Drawdown élevé")
    
    if results['sharpe_ratio'] > 1.0:
        score += 2
        print("✅ Bon Sharpe Ratio")
    else:
        print("⚠️ Sharpe Ratio faible")
    
    print(f"\n🏆 Score: {score}/10")
    
    if score >= 8:
        print("💎 Excellente stratégie!")
    elif score >= 6:
        print("✅ Bonne stratégie")
    elif score >= 4:
        print("⚠️ Stratégie acceptable")
    else:
        print("❌ Stratégie à améliorer")
    
    # Sauvegarder
    print("\n💾 Sauvegarde...")
    backtester.export_trades('simple_trades.csv')
    backtester.export_results('simple_results.csv')
    print("✅ Résultats sauvegardés")
    
    print("\n" + "="*70)
    print("   ✅ BACKTEST TERMINÉ!")
    print("="*70)
    
    return results


if __name__ == "__main__":
    try:
        results = run_backtest()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
