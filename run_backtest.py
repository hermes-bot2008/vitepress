"""
Script de Backtest - Quantdesk Ultra
=====================================

Lance un backtest complet du Hyper Scalper et affiche les résultats.
"""

import sys
import numpy as np
from datetime import datetime

# Import des modules Quantdesk
from quantdesk import HyperScalper, RiskManager, Backtester
from quantdesk.utils.data_loader import DataLoader


def run_backtest():
    """Lance un backtest complet."""
    
    print("="*70)
    print("   🚀 QUANTDESK ULTRA - BACKTEST HYPER SCALPER")
    print("="*70)
    
    # 1. Générer des données de marché réalistes
    print("\n📊 Génération des données de marché...")
    print("-"*70)
    
    data_loader = DataLoader()
    
    # Générer 6 mois de données 5 minutes pour l'or
    data = data_loader.generate_sample_data(
        start_date='2024-01-01',
        end_date='2024-06-30',
        freq='5min',
        initial_price=2000.0,
        volatility=0.0015  # Volatilité réaliste pour l'or
    )
    
    print(f"✅ {len(data)} barres générées")
    print(f"📅 Période: {data.index[0]} à {data.index[-1]}")
    print(f"💰 Prix de départ: ${data['close'].iloc[0]:.2f}")
    print(f"💰 Prix de fin: ${data['close'].iloc[-1]:.2f}")
    print(f"📈 Plus haut: ${data['high'].max():.2f}")
    print(f"📉 Plus bas: ${data['low'].min():.2f}")
    
    # 2. Configuration de la stratégie
    print("\n⚙️ Configuration du Hyper Scalper...")
    print("-"*70)
    
    strategy = HyperScalper(
        symbol="XAUUSD",
        lot_size=0.01,
        tp_pips=1.5,
        sl_pips=2.0,
        max_positions=10,  # Limité pour un backtest stable
        max_spread=3.0,
        rsi_period=3,
        rsi_upper=80,
        rsi_lower=20,
        tick_ma_period=5,
        min_volatility=0.3,
        max_volatility=5.0
    )
    
    print(f"Symbol: {strategy.symbol}")
    print(f"Lot Size: {strategy.lot_size}")
    print(f"TP: {strategy.tp_pips} pips")
    print(f"SL: {strategy.sl_pips} pips")
    print(f"Max Positions: {strategy.max_positions}")
    
    # 3. Configuration du Risk Manager
    print("\n🛡️ Configuration du Risk Manager...")
    print("-"*70)
    
    risk_manager = RiskManager(
        initial_capital=10000.0,
        max_daily_loss=100.0,
        max_daily_loss_percent=2.0,
        max_position_size=0.1,
        max_open_positions=10,
        max_drawdown_percent=15.0,
        use_equity_protection=True,
        equity_protection_percent=10.0,
        max_risk_per_trade=1.0
    )
    
    print(f"Capital Initial: ${risk_manager.initial_capital:,.2f}")
    print(f"Max Daily Loss: ${risk_manager.max_daily_loss}")
    print(f"Max Drawdown: {risk_manager.max_drawdown_percent}%")
    print(f"Max Positions: {risk_manager.max_open_positions}")
    
    # 4. Création du Backtester
    print("\n🔧 Création du Backtester...")
    print("-"*70)
    
    backtester = Backtester(
        strategy=strategy,
        initial_capital=10000.0,
        commission=0.0,
        slippage=0.0
    )
    
    print("✅ Backtester créé")
    
    # 5. Lancement du Backtest
    print("\n" + "="*70)
    print("   🔄 LANCEMENT DU BACKTEST")
    print("="*70)
    
    results = backtester.run(
        data=data,
        risk_manager=risk_manager,
        verbose=True
    )
    
    # 6. Affichage des résultats détaillés
    print("\n" + "="*70)
    print("   📊 RÉSULTATS DÉTAILLÉS DU BACKTEST")
    print("="*70)
    
    # Performance financière
    print("\n💰 PERFORMANCE FINANCIÈRE")
    print("-"*70)
    print(f"Capital Initial:           ${results['initial_capital']:,.2f}")
    print(f"Capital Final:             ${results['final_equity']:,.2f}")
    print(f"Profit Net:                ${results['total_profit_$']:+,.2f}")
    print(f"Retour sur Investment:     {results['total_return_%']:+.2f}%")
    print(f"Profit Brut:               ${results['gross_profit']:,.2f}")
    print(f"Perte Brute:               ${results['gross_loss']:,.2f}")
    
    # Statistiques de trading
    print("\n📊 STATISTIQUES DE TRADING")
    print("-"*70)
    print(f"Total de Trades:           {results['total_trades']}")
    print(f"Trades Gagnants:           {results['winning_trades']}")
    print(f"Trades Perdants:           {results['losing_trades']}")
    print(f"Taux de Réussite:          {results['win_rate_%']:.2f}%")
    print(f"Profit Factor:             {results['profit_factor']:.2f}")
    print(f"Espérance par Trade:       ${results['expectancy']:+,.2f}")
    
    # Analyse des trades
    print("\n🎯 ANALYSE DES TRADES")
    print("-"*70)
    print(f"Profit Moyen par Trade:    ${results['avg_profit_per_trade']:+,.2f}")
    print(f"Gain Moyen:                ${results['avg_win']:,.2f}")
    print(f"Perte Moyenne:             ${results['avg_loss']:,.2f}")
    print(f"Plus Grand Gain:           ${results['biggest_win']:,.2f}")
    print(f"Plus Grande Perte:         ${results['biggest_loss']:,.2f}")
    
    # Métriques de risque
    print("\n📉 MÉTRIQUES DE RISQUE")
    print("-"*70)
    print(f"Sharpe Ratio:              {results['sharpe_ratio']:.3f}")
    print(f"Sortino Ratio:             {results['sortino_ratio']:.3f}")
    print(f"Calmar Ratio:              {results['calmar_ratio']:.3f}")
    print(f"Drawdown Maximum:          {results['max_drawdown_%']:.2f}%")
    
    # Période et durée
    print("\n📅 PÉRIODE")
    print("-"*70)
    print(f"Date de Début:             {results['start_date']}")
    print(f"Date de Fin:               {results['end_date']}")
    print(f"Durée:                     {results['duration_days']} jours")
    
    # Calculs additionnels
    print("\n📈 STATISTIQUES ADDITIONNELLES")
    print("-"*70)
    
    if results['total_trades'] > 0:
        trades_per_day = results['total_trades'] / max(results['duration_days'], 1)
        profit_per_day = results['total_profit_$'] / max(results['duration_days'], 1)
        
        print(f"Trades par Jour (moy):     {trades_per_day:.1f}")
        print(f"Profit par Jour (moy):     ${profit_per_day:+,.2f}")
        
        # Ratio gain/perte
        if results['avg_loss'] != 0:
            avg_win_loss_ratio = abs(results['avg_win'] / results['avg_loss'])
            print(f"Ratio Gain/Perte Moyen:    {avg_win_loss_ratio:.2f}:1")
        
        # Facteur de récupération
        if results['max_drawdown_%'] > 0:
            recovery_factor = abs(results['total_return_%'] / results['max_drawdown_%'])
            print(f"Facteur de Récupération:   {recovery_factor:.2f}")
    
    # Note de la stratégie
    print("\n⭐ ÉVALUATION DE LA STRATÉGIE")
    print("-"*70)
    
    score = 0
    notes = []
    
    # Critère 1: Rentabilité
    if results['total_return_%'] > 20:
        score += 2
        notes.append("✅ Excellente rentabilité")
    elif results['total_return_%'] > 10:
        score += 1
        notes.append("✅ Bonne rentabilité")
    elif results['total_return_%'] > 0:
        notes.append("⚠️ Rentabilité faible")
    else:
        notes.append("❌ Stratégie perdante")
    
    # Critère 2: Win Rate
    if results['win_rate_%'] > 60:
        score += 2
        notes.append("✅ Excellent taux de réussite")
    elif results['win_rate_%'] > 50:
        score += 1
        notes.append("✅ Bon taux de réussite")
    else:
        notes.append("⚠️ Taux de réussite à améliorer")
    
    # Critère 3: Sharpe Ratio
    if results['sharpe_ratio'] > 2.0:
        score += 2
        notes.append("✅ Excellent Sharpe Ratio")
    elif results['sharpe_ratio'] > 1.0:
        score += 1
        notes.append("✅ Bon Sharpe Ratio")
    else:
        notes.append("⚠️ Sharpe Ratio à améliorer")
    
    # Critère 4: Drawdown
    if results['max_drawdown_%'] < 10:
        score += 2
        notes.append("✅ Drawdown bien contrôlé")
    elif results['max_drawdown_%'] < 20:
        score += 1
        notes.append("✅ Drawdown acceptable")
    else:
        notes.append("⚠️ Drawdown élevé")
    
    # Critère 5: Profit Factor
    if results['profit_factor'] > 1.5:
        score += 2
        notes.append("✅ Excellent Profit Factor")
    elif results['profit_factor'] > 1.2:
        score += 1
        notes.append("✅ Bon Profit Factor")
    else:
        notes.append("⚠️ Profit Factor à améliorer")
    
    for note in notes:
        print(note)
    
    print(f"\n🏆 Score Global: {score}/10")
    
    if score >= 8:
        print("💎 Stratégie EXCELLENTE - Prête pour le trading réel (avec compte démo d'abord)")
    elif score >= 6:
        print("✅ Stratégie BONNE - Quelques optimisations possibles")
    elif score >= 4:
        print("⚠️ Stratégie ACCEPTABLE - Optimisations recommandées")
    else:
        print("❌ Stratégie À REVOIR - Nécessite des ajustements importants")
    
    # 7. Sauvegarder les résultats
    print("\n💾 Sauvegarde des résultats...")
    print("-"*70)
    
    try:
        backtester.export_trades('backtest_trades.csv')
        print("✅ Trades exportés: backtest_trades.csv")
    except Exception as e:
        print(f"⚠️ Erreur export trades: {e}")
    
    try:
        backtester.export_results('backtest_results.csv')
        print("✅ Résultats exportés: backtest_results.csv")
    except Exception as e:
        print(f"⚠️ Erreur export résultats: {e}")
    
    print("\n" + "="*70)
    print("   ✅ BACKTEST TERMINÉ AVEC SUCCÈS!")
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
