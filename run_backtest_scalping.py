"""
BACKTEST SCALPING ULTRA HAUTE FRÉQUENCE
========================================

Vrai scalping avec:
- Timeframe 5 minutes
- 50-200 trades par jour
- TP/SL très courts (1.5-2 pips)
- Entrées/sorties rapides
"""

import sys
import numpy as np
import pandas as pd

from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class TrueScalper(BaseStrategy):
    """
    VRAI Scalper Ultra Haute Fréquence
    
    Caractéristiques:
    - Timeframe: 5 minutes
    - TP: 1.5 pips
    - SL: 2.0 pips  
    - Signaux fréquents
    - Sorties rapides
    """
    
    def __init__(self, symbol="XAUUSD", lot_size=0.01):
        super().__init__(symbol, lot_size)
        self.indicators = TechnicalIndicators()
        
        # Paramètres de scalping
        self.tp_pips = 1.5  # Take Profit
        self.sl_pips = 2.0  # Stop Loss
        self.max_positions = 5
        
        # Pas de cooldown en scalping!
        self.bars_since_trade = 0
        
        # Compteurs
        self.signals_generated = 0
        self.signals_rejected = 0
    
    def generate_signal(self, data: pd.DataFrame) -> int:
        """
        Génère des signaux de scalping basés sur:
        1. RSI ultra-court (période 3)
        2. Micro momentum
        3. Volatilité instantanée
        """
        if len(data) < 10:
            return 0
        
        # Limiter positions ouvertes
        if len(self.open_positions) >= self.max_positions:
            self.signals_rejected += 1
            return 0
        
        # Calculer RSI court (3 périodes pour scalping)
        rsi = self.indicators.calculate_rsi(data['close'], period=3)
        if rsi is None or pd.isna(rsi.iloc[-1]):
            return 0
        
        current_rsi = rsi.iloc[-1]
        
        # Calculer micro momentum (2 barres)
        momentum = data['close'].diff(2).iloc[-1]
        
        # Prix actuel et MA courte
        current_price = data['close'].iloc[-1]
        ma_fast = data['close'].rolling(3).mean().iloc[-1]
        
        if pd.isna(ma_fast) or pd.isna(momentum):
            return 0
        
        # SIGNAL D'ACHAT (Scalping)
        # RSI très bas + momentum positif
        if current_rsi < 30 and momentum > 0 and current_price > ma_fast:
            self.signals_generated += 1
            return 1
        
        # SIGNAL DE VENTE (Scalping)
        # RSI très haut + momentum négatif
        if current_rsi > 70 and momentum < 0 and current_price < ma_fast:
            self.signals_generated += 1
            return -1
        
        # Signal additionnel: Rebond sur MA
        price_dist = abs(current_price - ma_fast) / ma_fast
        
        # Si prix très proche de MA (scalping de rebond)
        if price_dist < 0.0005:  # 0.05%
            if current_price > ma_fast and momentum > 0:
                self.signals_generated += 1
                return 1
            elif current_price < ma_fast and momentum < 0:
                self.signals_generated += 1
                return -1
        
        return 0
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        """
        Fermeture rapide en scalping:
        1. TP/SL classiques
        2. Fermeture anticipée si petit profit
        3. Time-based exit (pas trop longtemps)
        """
        
        # TP/SL standard
        if position.position_type == 'BUY':
            if current_price >= position.take_profit:
                return True
            if current_price <= position.stop_loss:
                return True
        else:  # SELL
            if current_price <= position.take_profit:
                return True
            if current_price >= position.stop_loss:
                return True
        
        # Fermeture anticipée sur petit profit (scalping)
        current_profit = position.get_current_profit(current_price)
        
        # Si profit >= $0.50, sortir rapidement (60% chance)
        if current_profit >= 0.50:
            if np.random.random() < 0.60:
                return True
        
        # Time-based exit: si position > 30 barres (2h30), fermer
        if self.market_data is not None and not self.market_data.empty:
            bars_open = len(self.market_data) - len(self.market_data[:position.open_time])
            if bars_open > 30:  # Max 2h30 en scalping
                return True
        
        return False
    
    def execute_trade(self, signal: int, current_price: float):
        """Execute un trade de scalping avec TP/SL courts."""
        if signal == 0:
            return
        
        position_type = 'BUY' if signal > 0 else 'SELL'
        
        # TP/SL fixes pour scalping (en prix)
        pip_value = 0.01  # Pour l'or
        
        if position_type == 'BUY':
            stop_loss = current_price - (self.sl_pips * pip_value)
            take_profit = current_price + (self.tp_pips * pip_value)
        else:  # SELL
            stop_loss = current_price + (self.sl_pips * pip_value)
            take_profit = current_price - (self.tp_pips * pip_value)
        
        position = self.open_position(
            position_type=position_type,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        return position


def main():
    """Lance le backtest de scalping."""
    
    print("="*80)
    print("   ⚡ QUANTDESK ULTRA - BACKTEST SCALPING HAUTE FRÉQUENCE ⚡")
    print("="*80)
    
    # Générer données 5 MINUTES (scalping)
    print("\n📊 Génération des données 5 MINUTES (scalping)...")
    
    np.random.seed(456)
    
    # 2 mois de données 5min = ~17,000 barres
    dates = pd.date_range(start='2024-01-01', end='2024-03-01', freq='5min')
    n = len(dates)
    
    print(f"   Nombre de barres: {n}")
    print(f"   Période: 2 mois")
    print(f"   Timeframe: 5 MINUTES ⚡")
    
    # Prix avec volatilité pour scalping
    # Tendance légère + beaucoup de bruit
    trend = np.linspace(0, 50, n)
    noise = np.cumsum(np.random.randn(n) * 1.0)  # Plus de volatilité
    close = 2000 + trend + noise
    
    # OHLC avec micro-mouvements
    high = close + np.abs(np.random.randn(n) * 0.8)
    low = close - np.abs(np.random.randn(n) * 0.8)
    open_price = close + np.random.randn(n) * 0.3
    volume = np.random.randint(500, 5000, n)
    
    data = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    print(f"\n✅ {len(data)} barres générées")
    print(f"📅 Du {data.index[0]} au {data.index[-1]}")
    print(f"💰 Prix initial: ${data['close'].iloc[0]:.2f}")
    print(f"💰 Prix final: ${data['close'].iloc[-1]:.2f}")
    
    # Créer le scalper
    print("\n⚡ Configuration du VRAI Scalper...")
    print("-"*80)
    strategy = TrueScalper(
        symbol="XAUUSD",
        lot_size=0.01
    )
    print(f"Symbol:         {strategy.symbol}")
    print(f"Lot Size:       {strategy.lot_size}")
    print(f"TP:             {strategy.tp_pips} pips")
    print(f"SL:             {strategy.sl_pips} pips")
    print(f"Max Positions:  {strategy.max_positions}")
    print(f"Style:          SCALPING ULTRA HAUTE FRÉQUENCE ⚡")
    
    # Risk manager pour scalping
    print("\n🛡️ Configuration du Risk Manager (Scalping)...")
    print("-"*80)
    risk_manager = RiskManager(
        initial_capital=10000.0,
        max_daily_loss=150.0,  # Plus élevé pour scalping
        max_position_size=0.05,
        max_open_positions=5,  # Plus de positions simultanées
        max_drawdown_percent=15.0
    )
    print(f"Capital Initial:  ${risk_manager.initial_capital:,.2f}")
    print(f"Max Daily Loss:   ${risk_manager.max_daily_loss}")
    print(f"Max Positions:    {risk_manager.max_open_positions}")
    print(f"Max Drawdown:     {risk_manager.max_drawdown_percent}%")
    
    # Backtester
    print("\n🔧 Création du Backtester...")
    backtester = Backtester(
        strategy=strategy,
        initial_capital=10000.0,
        commission=0.0,  # Pas de commission en simulation
        slippage=0.0
    )
    print("✅ Backtester prêt pour scalping haute fréquence")
    
    # Lancer le backtest
    print("\n" + "="*80)
    print("   🔄 LANCEMENT DU BACKTEST SCALPING")
    print("="*80)
    print("\n⚡ Analyse de", len(data), "barres de 5 minutes...")
    print("⚡ Recherche de signaux de scalping...\n")
    
    results = backtester.run(
        data=data,
        risk_manager=risk_manager,
        verbose=True
    )
    
    # RÉSULTATS DÉTAILLÉS
    print("\n" + "="*80)
    print("   📊 RÉSULTATS DU SCALPING - QUANTDESK ULTRA")
    print("="*80)
    
    # Performance
    print("\n💰 PERFORMANCE FINANCIÈRE")
    print("-"*80)
    print(f"Capital de Départ:         ${results['initial_capital']:>15,.2f}")
    print(f"Capital Final:             ${results['final_equity']:>15,.2f}")
    print(f"Profit/Perte Net:          ${results['total_profit_$']:>15,.2f}  ({results['total_return_%']:+.2f}%)")
    print(f"Profit Brut:               ${results['gross_profit']:>15,.2f}")
    print(f"Perte Brute:               ${abs(results['gross_loss']):>15,.2f}")
    
    # Trading stats
    print("\n📊 STATISTIQUES DE TRADING (SCALPING)")
    print("-"*80)
    print(f"Nombre Total de Trades:    {results['total_trades']:>15}")
    print(f"Trades Gagnants:           {results['winning_trades']:>15}  ({results['win_rate_%']:.1f}%)")
    print(f"Trades Perdants:           {results['losing_trades']:>15}  ({100-results['win_rate_%']:.1f}%)")
    print(f"Profit Factor:             {results['profit_factor']:>15.2f}")
    
    # Fréquence (important pour scalping)
    duration_days = results['duration_days']
    if duration_days > 0:
        trades_per_day = results['total_trades'] / duration_days
        print(f"Trades par Jour:           {trades_per_day:>15.1f}  ⚡")
        
        # Trades par heure (scalping)
        duration_hours = duration_days * 24
        trades_per_hour = results['total_trades'] / duration_hours
        print(f"Trades par Heure:          {trades_per_hour:>15.2f}  ⚡⚡")
    
    # Analyse trades
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
    print(f"Espérance:                 ${results['expectancy']:>15,.2f}")
    
    # Risk metrics
    print("\n📉 MÉTRIQUES DE RISQUE")
    print("-"*80)
    print(f"Sharpe Ratio:              {results['sharpe_ratio']:>15.3f}")
    print(f"Sortino Ratio:             {results['sortino_ratio']:>15.3f}")
    print(f"Calmar Ratio:              {results['calmar_ratio']:>15.3f}")
    print(f"Drawdown Maximum:          {results['max_drawdown_%']:>15.2f}%")
    
    # Période
    print("\n📅 PÉRIODE DE TEST (SCALPING)")
    print("-"*80)
    print(f"Date de Début:             {results['start_date']}")
    print(f"Date de Fin:               {results['end_date']}")
    print(f"Durée Totale:              {results['duration_days']:>15} jours ({results['duration_days']/30:.1f} mois)")
    print(f"Barres Analysées:          {len(data):>15} (5min)")
    
    # Stats du scalper
    print("\n⚡ STATISTIQUES SPÉCIFIQUES AU SCALPING")
    print("-"*80)
    print(f"Signaux Générés:           {strategy.signals_generated:>15}")
    print(f"Signaux Rejetés:           {strategy.signals_rejected:>15}")
    
    if strategy.signals_generated > 0:
        acceptance_rate = (results['total_trades'] / strategy.signals_generated) * 100
        print(f"Taux d'Acceptation:        {acceptance_rate:>15.1f}%")
    
    # Évaluation
    print("\n⭐ ÉVALUATION DU SCALPING")
    print("-"*80)
    
    score = 0
    feedback = []
    
    # Rentabilité
    if results['total_return_%'] > 15:
        score += 2
        feedback.append("✅ Excellente rentabilité pour scalping (>15%)")
    elif results['total_return_%'] > 8:
        score += 1
        feedback.append("✅ Bonne rentabilité (>8%)")
    elif results['total_return_%'] > 0:
        feedback.append("⚠️ Rentabilité faible mais positive")
    else:
        feedback.append("❌ Stratégie perdante")
    
    # Fréquence de trading (crucial pour scalping!)
    if results['total_trades'] > 100:
        score += 2
        feedback.append(f"✅ Excellente fréquence ({results['total_trades']} trades)")
    elif results['total_trades'] > 50:
        score += 1
        feedback.append(f"✅ Bonne fréquence ({results['total_trades']} trades)")
    elif results['total_trades'] > 20:
        feedback.append(f"⚠️ Fréquence acceptable ({results['total_trades']} trades)")
    else:
        feedback.append(f"❌ Fréquence trop faible pour scalping ({results['total_trades']} trades)")
    
    # Win rate
    if results['win_rate_%'] >= 55:
        score += 2
        feedback.append("✅ Excellent win rate (≥55%)")
    elif results['win_rate_%'] >= 45:
        score += 1
        feedback.append("✅ Bon win rate (≥45%)")
    else:
        feedback.append("⚠️ Win rate à améliorer")
    
    # Profit Factor
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
    
    # Drawdown
    if results['max_drawdown_%'] < 10:
        score += 2
        feedback.append("✅ Drawdown excellent (<10%)")
    elif results['max_drawdown_%'] < 15:
        score += 1
        feedback.append("✅ Drawdown bon (<15%)")
    else:
        feedback.append("⚠️ Drawdown élevé")
    
    for item in feedback:
        print(item)
    
    print(f"\n🏆 SCORE SCALPING: {score}/10")
    print("")
    
    if score >= 8:
        print("💎 SCALPER EXCELLENT!")
        print("   → Performance exceptionnelle")
        print("   → Haute fréquence atteinte")
        print("   → Prêt pour tests avancés")
    elif score >= 6:
        print("✅ SCALPER BON")
        print("   → Bonnes performances")
        print("   → Quelques optimisations possibles")
    elif score >= 4:
        print("⚠️ SCALPER ACCEPTABLE")
        print("   → Nécessite optimisations")
        print("   → Augmenter la fréquence")
    else:
        print("❌ SCALPER À REVOIR")
        print("   → Fréquence trop faible")
        print("   → Revoir la stratégie")
    
    # Comparaison avec Swing Trading
    print("\n📊 COMPARAISON SCALPING vs SWING TRADING")
    print("-"*80)
    print(f"{'Métrique':<30} {'Scalping (5min)':<20} {'Swing (1H)':<20}")
    print("-"*80)
    print(f"{'Trades Totaux':<30} {results['total_trades']:<20} {'2':<20}")
    
    if duration_days > 0:
        trades_day = results['total_trades'] / duration_days
        print(f"{'Trades/Jour':<30} {trades_day:<20.1f} {'0.01':<20}")
    
    print(f"{'Durée Moyenne':<30} {'< 2h30 (scalping)':<20} {'4-11 jours':<20}")
    print(f"{'Timeframe':<30} {'5 minutes ⚡':<20} {'1 heure':<20}")
    print(f"{'Style':<30} {'Ultra actif':<20} {'Passif':<20}")
    
    # Sauvegarde
    print("\n💾 SAUVEGARDE DES RÉSULTATS")
    print("-"*80)
    
    backtester.export_trades('scalping_trades.csv')
    print("✅ Trades sauvegardés: scalping_trades.csv")
    
    backtester.export_results('scalping_results.csv')
    print("✅ Résultats sauvegardés: scalping_results.csv")
    
    print("\n" + "="*80)
    print("   ✅ BACKTEST SCALPING TERMINÉ!")
    print("="*80)
    print("\n⚡ QUANTDESK ULTRA - Plateforme de Scalping Haute Fréquence")
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
