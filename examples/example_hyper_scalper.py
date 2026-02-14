"""
Example: Hyper Scalper Strategy
================================

Exemple d'utilisation de la stratégie Hyper Scalper pour le trading de l'or (XAUUSD).
"""

from quantdesk import HyperScalper, RiskManager, Backtester
from quantdesk.utils.data_loader import DataLoader


def main():
    """Exemple complet d'utilisation du Hyper Scalper."""
    
    print("="*60)
    print("HYPER SCALPER - Example")
    print("="*60)
    
    # 1. Charger les données
    print("\n1. Loading data...")
    data_loader = DataLoader()
    
    # Option A: Charger depuis Yahoo Finance
    # data = data_loader.load_from_yahoo(
    #     symbol='GC=F',  # Gold futures
    #     start_date='2024-01-01',
    #     end_date='2024-12-31',
    #     interval='5m'
    # )
    
    # Option B: Générer des données de test
    data = data_loader.generate_sample_data(
        start_date='2024-01-01',
        end_date='2024-06-30',
        freq='5min',
        initial_price=2000.0,
        volatility=0.001
    )
    
    print(f"Loaded {len(data)} bars")
    
    # 2. Configurer la stratégie
    print("\n2. Configuring strategy...")
    strategy = HyperScalper(
        symbol="XAUUSD",
        lot_size=0.01,
        tp_pips=1.5,
        sl_pips=2.0,
        max_positions=50,
        max_spread=3.0,
        rsi_period=3,
        rsi_upper=80,
        rsi_lower=20,
        tick_ma_period=5,
        min_volatility=0.3,
        max_volatility=5.0
    )
    
    # 3. Configurer le risk manager
    print("3. Configuring risk manager...")
    risk_manager = RiskManager(
        initial_capital=10000.0,
        max_daily_loss=100.0,
        max_daily_loss_percent=2.0,
        max_position_size=0.1,
        max_open_positions=50,
        max_drawdown_percent=10.0,
        use_equity_protection=True,
        equity_protection_percent=10.0
    )
    
    # 4. Créer le backtester
    print("4. Creating backtester...")
    backtester = Backtester(
        strategy=strategy,
        initial_capital=10000.0,
        commission=0.0,
        slippage=0.0
    )
    
    # 5. Lancer le backtest
    print("\n5. Running backtest...\n")
    results = backtester.run(
        data=data,
        risk_manager=risk_manager,
        verbose=True
    )
    
    # 6. Afficher les résultats détaillés
    print("\n" + "="*60)
    print("DETAILED RESULTS")
    print("="*60)
    
    print(f"\n💰 Financial Performance:")
    print(f"   Initial Capital:    ${results['initial_capital']:,.2f}")
    print(f"   Final Equity:       ${results['final_equity']:,.2f}")
    print(f"   Net Profit:         ${results['total_profit_$']:+,.2f}")
    print(f"   Return:             {results['total_return_%']:+.2f}%")
    
    print(f"\n📊 Trading Statistics:")
    print(f"   Total Trades:       {results['total_trades']}")
    print(f"   Winning Trades:     {results['winning_trades']}")
    print(f"   Losing Trades:      {results['losing_trades']}")
    print(f"   Win Rate:           {results['win_rate_%']:.2f}%")
    print(f"   Profit Factor:      {results['profit_factor']:.2f}")
    
    print(f"\n📈 Risk Metrics:")
    print(f"   Sharpe Ratio:       {results['sharpe_ratio']:.2f}")
    print(f"   Sortino Ratio:      {results['sortino_ratio']:.2f}")
    print(f"   Max Drawdown:       {results['max_drawdown_%']:.2f}%")
    
    print(f"\n🎯 Trade Analysis:")
    print(f"   Avg Profit/Trade:   ${results['avg_profit_per_trade']:+,.2f}")
    print(f"   Biggest Win:        ${results['biggest_win']:,.2f}")
    print(f"   Biggest Loss:       ${results['biggest_loss']:,.2f}")
    print(f"   Expectancy:         ${results['expectancy']:+,.2f}")
    
    # 7. Exporter les résultats
    print("\n7. Exporting results...")
    backtester.export_trades('hyper_scalper_trades.csv')
    backtester.export_results('hyper_scalper_results.csv')
    
    # 8. Générer les graphiques
    print("\n8. Generating charts...")
    try:
        backtester.plot_equity_curve(save_path='hyper_scalper_equity.png')
        backtester.plot_trades_distribution(save_path='hyper_scalper_distribution.png')
        print("✅ Charts saved successfully")
    except Exception as e:
        print(f"⚠️ Could not save charts: {e}")
    
    print("\n" + "="*60)
    print("✅ Example completed successfully!")
    print("="*60)
    
    return results


if __name__ == "__main__":
    results = main()
