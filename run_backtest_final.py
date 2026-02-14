"""
Backtest Final avec Stratégie Optimisée
========================================
"""

import sys
import numpy as np
import pandas as pd

from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class OptimizedScalper(BaseStrategy):
    """Scalper optimisé avec meilleurs signaux et gestion du risque."""
    
    def __init__(self, symbol="XAUUSD", lot_size=0.01):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        self.bars_since_last_trade = 0
    
    def generate_signal(self, data: pd.DataFrame) -> int:
        """Génère des signaux basés sur croisements de moyennes mobiles et RSI."""
        if len(data) < 50:
            return 0
        
        # Cooldown entre trades
        if self.bars_since_last_trade < 10:
            self.bars_since_last_trade += 1
            return 0
        
        # Limiter positions ouvertes
        if len(self.open_positions) >= 2:
            return 0
        
        # RSI
        rsi = self.indicators.calculate_rsi(data['close'], period=14)
        if rsi is None or pd.isna(rsi.iloc[-1]):
            return 0
        
        # Moyennes mobiles
        ema_fast = self.indicators.calculate_ema(data['close'], period=10)
        ema_slow = self.indicators.calculate_ema(data['close'], period=30)
        
        if ema_fast is None or ema_slow is None:
            return 0
        
        if pd.isna(ema_fast.iloc[-1]) or pd.isna(ema_slow.iloc[-1]):
            return 0
        
        current_rsi = rsi.iloc[-1]
        ema_fast_curr = ema_fast.iloc[-1]
        ema_slow_curr = ema_slow.iloc[-1]
        ema_fast_prev = ema_fast.iloc[-2]
        ema_slow_prev = ema_slow.iloc[-2]
        
        # Signal d'achat: Croisement haussier + RSI < 70
        if ema_fast_prev < ema_slow_prev and ema_fast_curr > ema_slow_curr and current_rsi < 70:
            self.bars_since_last_trade = 0
            return 1
        
        # Signal de vente: Croisement baissier + RSI > 30
        if ema_fast_prev > ema_slow_prev and ema_fast_curr < ema_slow_curr and current_rsi > 30:
            self.bars_since_last_trade = 0
            return -1
        
        self.bars_since_last_trade += 1
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
        """Execute un trade avec TP/SL basé sur ATR."""
        if signal == 0 or self.market_data is None:
            return
        
        # Calculer l'ATR pour SL/TP dynamiques
        atr = self.indicators.calculate_atr(
            self.market_data['high'],
            self.market_data['low'],
            self.market_data['close'],
            period=14
        )
        
        if atr is None or pd.isna(atr.iloc[-1]):
            atr_value = current_price * 0.01  # 1% comme fallback
        else:
            atr_value = atr.iloc[-1]
        
        position_type = 'BUY' if signal > 0 else 'SELL'
        
        # SL = 2 * ATR, TP = 3 * ATR (ratio 1.5:1)
        if position_type == 'BUY':
            stop_loss = current_price - (2 * atr_value)
            take_profit = current_price + (3 * atr_value)
        else:
            stop_loss = current_price + (2 * atr_value)
            take_profit = current_price - (3 * atr_value)
        
        position = self.open_position(
            position_type=position_type,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        return position


def main():
    """Lance le backtest final."""
    
    print("="*80)
    print("   🚀 QUANTDESK ULTRA - RÉSULTATS DE BACKTEST FINAL")
    print("="*80)
    
    # Générer des données avec tendance
    print("\n📊 Génération des données de marché...")
    
    np.random.seed(123)
    
    # Créer des données avec une tendance haussière
    dates = pd.date_range(start='2024-01-01', end='2024-06-30', freq='1h')
    n = len(dates)
    
    # Tendance + bruit
    trend = np.linspace(0, 100, n)  # Tendance haussière
    noise = np.cumsum(np.random.randn(n) * 2)  # Bruit aléatoire
    close = 2000 + trend + noise
    
    # OHLC
    high = close + np.abs(np.random.randn(n) * 5)
    low = close - np.abs(np.random.randn(n) * 5)
    open_price = close + np.random.randn(n) * 2
    volume = np.random.randint(1000, 10000, n)
    
    data = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    print(f"✅ {len(data)} barres générées")
    print(f"📅 Période: {data.index[0]} à {data.index[-1]}")
    print(f"💰 Prix initial: ${data['close'].iloc[0]:.2f}")
    print(f"💰 Prix final: ${data['close'].iloc[-1]:.2f}")
    print(f"📈 Variation: {((data['close'].iloc[-1] / data['close'].iloc[0]) - 1) * 100:.2f}%")
    
    # Créer la stratégie
    print("\n⚙️ Configuration de la stratégie...")
    strategy = OptimizedScalper(
        symbol="XAUUSD",
        lot_size=0.01
    )
    print(f"Symbol: {strategy.symbol}")
    print(f"Lot Size: {strategy.lot_size}")
    
    # Risk manager
    print("\n🛡️ Configuration du Risk Manager...")
    risk_manager = RiskManager(
        initial_capital=10000.0,
        max_daily_loss=200.0,
        max_position_size=0.1,
        max_open_positions=5,
        max_drawdown_percent=20.0
    )
    print(f"Capital Initial: ${risk_manager.initial_capital:,.2f}")
    print(f"Max Daily Loss: ${risk_manager.max_daily_loss}")
    print(f"Max Drawdown: {risk_manager.max_drawdown_percent}%")
    
    # Backtester
    print("\n🔧 Création du Backtester...")
    backtester = Backtester(
        strategy=strategy,
        initial_capital=10000.0
    )
    print("✅ Backtester prêt")
    
    # Lancer le backtest
    print("\n" + "="*80)
    print("   🔄 LANCEMENT DU BACKTEST")
    print("="*80 + "\n")
    
    results = backtester.run(
        data=data,
        risk_manager=risk_manager,
        verbose=True
    )
    
    # Afficher résultats détaillés
    print("\n" + "="*80)
    print("   📊 RÉSULTATS DU BACKTEST - QUANTDESK ULTRA")
    print("="*80)
    
    print("\n💰 PERFORMANCE FINANCIÈRE")
    print("-"*80)
    print(f"Capital de Départ:         ${results['initial_capital']:>15,.2f}")
    print(f"Capital Final:             ${results['final_equity']:>15,.2f}")
    print(f"Profit/Perte Net:          ${results['total_profit_$']:>15,.2f}  ({results['total_return_%']:+.2f}%)")
    print(f"Profit Brut:               ${results['gross_profit']:>15,.2f}")
    print(f"Perte Brute:               ${abs(results['gross_loss']):>15,.2f}")
    
    print("\n📊 STATISTIQUES DE TRADING")
    print("-"*80)
    print(f"Nombre Total de Trades:    {results['total_trades']:>15}")
    print(f"Trades Gagnants:           {results['winning_trades']:>15}  ({results['win_rate_%']:.1f}%)")
    print(f"Trades Perdants:           {results['losing_trades']:>15}  ({100-results['win_rate_%']:.1f}%)")
    print(f"Profit Factor:             {results['profit_factor']:>15.2f}")
    print(f"Espérance par Trade:       ${results['expectancy']:>15,.2f}")
    
    print("\n🎯 ANALYSE DES TRADES")
    print("-"*80)
    print(f"Profit Moyen/Trade:        ${results['avg_profit_per_trade']:>15,.2f}")
    print(f"Gain Moyen:                ${results['avg_win']:>15,.2f}")
    print(f"Perte Moyenne:             ${abs(results['avg_loss']):>15,.2f}")
    
    if results['avg_loss'] != 0:
        ratio = abs(results['avg_win'] / results['avg_loss'])
        print(f"Ratio Gain/Perte:          {ratio:>15.2f}:1")
    
    print(f"Plus Grand Gain:           ${results['biggest_win']:>15,.2f}")
    print(f"Plus Grande Perte:         ${abs(results['biggest_loss']):>15,.2f}")
    
    print("\n📉 MÉTRIQUES DE RISQUE")
    print("-"*80)
    print(f"Sharpe Ratio:              {results['sharpe_ratio']:>15.3f}")
    print(f"Sortino Ratio:             {results['sortino_ratio']:>15.3f}")
    print(f"Calmar Ratio:              {results['calmar_ratio']:>15.3f}")
    print(f"Drawdown Maximum:          {results['max_drawdown_%']:>15.2f}%")
    
    print("\n📅 PÉRIODE ET FRÉQUENCE")
    print("-"*80)
    print(f"Date de Début:             {results['start_date']}")
    print(f"Date de Fin:               {results['end_date']}")
    print(f"Durée Totale:              {results['duration_days']:>15} jours")
    
    if results['duration_days'] > 0:
        trades_per_day = results['total_trades'] / results['duration_days']
        print(f"Trades/Jour (moyenne):     {trades_per_day:>15.2f}")
    
    if results['total_trades'] > 0:
        profit_per_trade = results['total_profit_$'] / results['total_trades']
        print(f"Profit Moyen/Trade:        ${profit_per_trade:>15,.2f}")
    
    # Évaluation globale
    print("\n⭐ ÉVALUATION DE LA STRATÉGIE")
    print("-"*80)
    
    score = 0
    feedback = []
    
    if results['total_return_%'] > 10:
        score += 2
        feedback.append("✅ Excellente rentabilité (>10%)")
    elif results['total_return_%'] > 5:
        score += 1
        feedback.append("✅ Bonne rentabilité (>5%)")
    elif results['total_return_%'] > 0:
        feedback.append("⚠️ Rentabilité faible mais positive")
    else:
        feedback.append("❌ Stratégie perdante")
    
    if results['win_rate_%'] >= 55:
        score += 2
        feedback.append("✅ Excellent taux de réussite (≥55%)")
    elif results['win_rate_%'] >= 45:
        score += 1
        feedback.append("✅ Bon taux de réussite (≥45%)")
    else:
        feedback.append("⚠️ Taux de réussite à améliorer")
    
    if results['profit_factor'] >= 1.5:
        score += 2
        feedback.append("✅ Excellent Profit Factor (≥1.5)")
    elif results['profit_factor'] >= 1.2:
        score += 1
        feedback.append("✅ Bon Profit Factor (≥1.2)")
    elif results['profit_factor'] > 1.0:
        feedback.append("⚠️ Profit Factor acceptable")
    else:
        feedback.append("❌ Profit Factor insuffisant")
    
    if results['max_drawdown_%'] < 10:
        score += 2
        feedback.append("✅ Drawdown excellent (<10%)")
    elif results['max_drawdown_%'] < 20:
        score += 1
        feedback.append("✅ Drawdown acceptable (<20%)")
    else:
        feedback.append("⚠️ Drawdown élevé")
    
    if results['sharpe_ratio'] >= 2.0:
        score += 2
        feedback.append("✅ Sharpe Ratio exceptionnel (≥2.0)")
    elif results['sharpe_ratio'] >= 1.0:
        score += 1
        feedback.append("✅ Sharpe Ratio bon (≥1.0)")
    else:
        feedback.append("⚠️ Sharpe Ratio à améliorer")
    
    for item in feedback:
        print(item)
    
    print(f"\n🏆 SCORE GLOBAL: {score}/10")
    print("")
    
    if score >= 8:
        print("💎 STRATÉGIE EXCELLENTE")
        print("   → Prête pour le trading réel (testez d'abord en démo)")
        print("   → Tous les indicateurs sont au vert")
    elif score >= 6:
        print("✅ STRATÉGIE BONNE")
        print("   → Performances solides")
        print("   → Quelques optimisations possibles")
    elif score >= 4:
        print("⚠️ STRATÉGIE ACCEPTABLE")
        print("   → Nécessite des optimisations")
        print("   → À tester plus longuement")
    else:
        print("❌ STRATÉGIE À REVOIR")
        print("   → Ajustements importants nécessaires")
        print("   → Modifier les paramètres ou la logique")
    
    # Sauvegarder
    print("\n💾 SAUVEGARDE DES RÉSULTATS")
    print("-"*80)
    
    backtester.export_trades('final_trades.csv')
    print("✅ Trades sauvegardés: final_trades.csv")
    
    backtester.export_results('final_results.csv')
    print("✅ Résultats sauvegardés: final_results.csv")
    
    print("\n" + "="*80)
    print("   ✅ BACKTEST TERMINÉ AVEC SUCCÈS")
    print("="*80)
    print("\n📁 Fichiers générés:")
    print("   - final_trades.csv (détails des trades)")
    print("   - final_results.csv (métriques de performance)")
    print("\n🎯 Quantdesk Ultra AI - Plateforme de Trading Quantitatif")
    print("="*80 + "\n")
    
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
