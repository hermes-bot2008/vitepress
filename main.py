"""
Quantdesk Ultra - Main Entry Point
===================================

Exemple d'utilisation de la plateforme Quantdesk Ultra.
"""

import sys
from datetime import datetime
import pandas as pd

from quantdesk import HyperScalper, MomentumStrategy, MeanReversionStrategy
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.utils.data_loader import DataLoader


def run_hyper_scalper_demo():
    """Démonstration du Hyper Scalper."""
    print("\n" + "="*70)
    print("🚀 QUANTDESK ULTRA - HYPER SCALPER DEMO")
    print("="*70)
    
    # Charger les données
    print("\n📥 Loading market data...")
    data_loader = DataLoader()
    
    # Générer des données de test pour l'or (XAUUSD)
    data = data_loader.generate_sample_data(
        start_date='2024-01-01',
        end_date='2024-06-30',
        freq='5min',
        initial_price=2000.0,
        volatility=0.001  # Faible volatilité pour scalping
    )
    
    print(f"✅ Loaded {len(data)} bars")
    
    # Créer la stratégie
    print("\n⚙️ Initializing Hyper Scalper strategy...")
    strategy = HyperScalper(
        symbol="XAUUSD",
        lot_size=0.01,
        tp_pips=1.5,
        sl_pips=2.0,
        max_positions=10,
        rsi_period=3,
        tick_ma_period=5
    )
    
    # Créer le risk manager
    print("⚙️ Initializing Risk Manager...")
    risk_manager = RiskManager(
        initial_capital=10000.0,
        max_daily_loss=100.0,
        max_daily_loss_percent=2.0,
        max_position_size=0.1,
        max_open_positions=10,
        max_drawdown_percent=10.0
    )
    
    # Créer le backtester
    backtester = Backtester(
        strategy=strategy,
        initial_capital=10000.0
    )
    
    # Lancer le backtest
    print("\n🔄 Running backtest...")
    results = backtester.run(data, risk_manager=risk_manager, verbose=True)
    
    # Afficher les graphiques
    print("\n📊 Generating charts...")
    try:
        backtester.plot_equity_curve()
        backtester.plot_trades_distribution()
    except Exception as e:
        print(f"⚠️ Could not display charts: {e}")
        print("Charts require a display. Running in headless mode.")
    
    return results


def run_momentum_demo():
    """Démonstration de la stratégie Momentum."""
    print("\n" + "="*70)
    print("🚀 QUANTDESK ULTRA - MOMENTUM STRATEGY DEMO")
    print("="*70)
    
    # Charger les données
    print("\n📥 Loading market data...")
    data_loader = DataLoader()
    
    # Générer des données de test pour EUR/USD
    data = data_loader.generate_sample_data(
        start_date='2024-01-01',
        end_date='2024-12-31',
        freq='1H',
        initial_price=1.1000,
        volatility=0.005
    )
    
    print(f"✅ Loaded {len(data)} bars")
    
    # Créer la stratégie
    print("\n⚙️ Initializing Momentum strategy...")
    strategy = MomentumStrategy(
        symbol="EURUSD",
        lot_size=0.01,
        macd_fast=12,
        macd_slow=26,
        macd_signal=9,
        rsi_period=14
    )
    
    # Créer le risk manager
    risk_manager = RiskManager(
        initial_capital=10000.0,
        max_daily_loss=150.0,
        max_position_size=0.1
    )
    
    # Créer le backtester
    backtester = Backtester(
        strategy=strategy,
        initial_capital=10000.0
    )
    
    # Lancer le backtest
    print("\n🔄 Running backtest...")
    results = backtester.run(data, risk_manager=risk_manager, verbose=True)
    
    return results


def run_mean_reversion_demo():
    """Démonstration de la stratégie Mean Reversion."""
    print("\n" + "="*70)
    print("🚀 QUANTDESK ULTRA - MEAN REVERSION STRATEGY DEMO")
    print("="*70)
    
    # Charger les données
    print("\n📥 Loading market data...")
    data_loader = DataLoader()
    
    # Générer des données de test pour GBP/USD
    data = data_loader.generate_sample_data(
        start_date='2024-01-01',
        end_date='2024-12-31',
        freq='1H',
        initial_price=1.2500,
        volatility=0.008
    )
    
    print(f"✅ Loaded {len(data)} bars")
    
    # Créer la stratégie
    print("\n⚙️ Initializing Mean Reversion strategy...")
    strategy = MeanReversionStrategy(
        symbol="GBPUSD",
        lot_size=0.01,
        bb_period=20,
        bb_std=2.0,
        rsi_period=14,
        rsi_oversold=30,
        rsi_overbought=70
    )
    
    # Créer le risk manager
    risk_manager = RiskManager(
        initial_capital=10000.0,
        max_daily_loss=150.0,
        max_position_size=0.1
    )
    
    # Créer le backtester
    backtester = Backtester(
        strategy=strategy,
        initial_capital=10000.0
    )
    
    # Lancer le backtest
    print("\n🔄 Running backtest...")
    results = backtester.run(data, risk_manager=risk_manager, verbose=True)
    
    return results


def main():
    """Fonction principale."""
    print("\n" + "="*70)
    print("       🎯 QUANTDESK ULTRA AI - TRADING PLATFORM")
    print("="*70)
    print("\nSelect a strategy to test:")
    print("1. Hyper Scalper (Ultra High Frequency)")
    print("2. Momentum Strategy")
    print("3. Mean Reversion Strategy")
    print("4. Run all strategies")
    print("0. Exit")
    
    choice = input("\nEnter your choice (0-4): ").strip()
    
    if choice == '1':
        run_hyper_scalper_demo()
    elif choice == '2':
        run_momentum_demo()
    elif choice == '3':
        run_mean_reversion_demo()
    elif choice == '4':
        print("\n🔄 Running all strategies...\n")
        run_hyper_scalper_demo()
        run_momentum_demo()
        run_mean_reversion_demo()
    elif choice == '0':
        print("\n👋 Goodbye!")
        sys.exit(0)
    else:
        print("\n❌ Invalid choice. Please try again.")
        main()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
