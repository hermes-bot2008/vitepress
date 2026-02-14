"""
Backtester
==========

Système de backtesting pour tester les stratégies de trading sur données historiques.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

from quantdesk.algorithms.base_strategy import BaseStrategy
from quantdesk.risk.risk_manager import RiskManager


class Backtester:
    """
    Backtester pour évaluer les performances d'une stratégie.
    
    Paramètres:
        strategy: Stratégie à tester
        initial_capital: Capital initial
        commission: Commission par trade (en dollars ou %)
        slippage: Slippage par trade (en pips)
    """
    
    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float = 10000.0,
        commission: float = 0.0,
        slippage: float = 0.0
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        
        # Résultats
        self.results: Optional[Dict] = None
        self.trades_df: Optional[pd.DataFrame] = None
        self.equity_curve: List[float] = []
        self.dates: List[datetime] = []
        
        # Performance
        self.total_return = 0.0
        self.sharpe_ratio = 0.0
        self.max_drawdown = 0.0
        self.win_rate = 0.0
        self.profit_factor = 0.0
    
    def run(
        self,
        data: pd.DataFrame,
        risk_manager: Optional[RiskManager] = None,
        verbose: bool = True
    ) -> Dict:
        """
        Lance le backtest sur les données historiques.
        
        Args:
            data: DataFrame avec colonnes ['open', 'high', 'low', 'close', 'volume']
            risk_manager: Gestionnaire de risques (optionnel)
            verbose: Afficher les logs
            
        Returns:
            Dictionnaire des résultats
        """
        if verbose:
            print("=" * 60)
            print("🚀 Starting Backtest")
            print("=" * 60)
            print(f"Strategy: {self.strategy.__class__.__name__}")
            print(f"Symbol: {self.strategy.symbol}")
            print(f"Period: {data.index[0]} to {data.index[-1]}")
            print(f"Total bars: {len(data)}")
            print(f"Initial Capital: ${self.initial_capital:,.2f}")
            print("-" * 60)
        
        # Réinitialiser la stratégie
        self.strategy.reset()
        
        # Initialiser le risk manager si fourni
        if risk_manager:
            risk_manager.reset()
            risk_manager.initial_capital = self.initial_capital
            risk_manager.current_capital = self.initial_capital
        
        # Initialiser l'equity curve
        self.equity_curve = [self.initial_capital]
        self.dates = [data.index[0]]
        current_equity = self.initial_capital
        
        # Parcourir les données
        for i in range(len(data)):
            current_bar = data.iloc[:i+1]
            current_price = data['close'].iloc[i]
            current_date = data.index[i]
            
            # Mettre à jour les données de marché
            self.strategy.update_market_data(current_bar)
            
            # Vérifier et fermer les positions
            self.strategy.manage_open_positions()
            
            # Générer un signal
            if len(current_bar) >= 30:  # Attendre assez de données
                signal = self.strategy.generate_signal(current_bar)
                
                # Vérifier avec le risk manager
                can_trade = True
                if risk_manager:
                    can_trade, reason = risk_manager.can_open_position(
                        len(self.strategy.open_positions),
                        self.strategy.lot_size
                    )
                
                # Exécuter le trade si signal et autorisation
                if signal != 0 and can_trade:
                    self.strategy.execute_trade(signal, current_price)
            
            # Calculer l'equity actuelle
            realized_profit = sum([p.profit for p in self.strategy.positions if not p.is_open])
            unrealized_profit = sum([p.get_current_profit(current_price) for p in self.strategy.open_positions])
            
            current_equity = self.initial_capital + realized_profit + unrealized_profit
            
            # Mettre à jour le risk manager
            if risk_manager:
                risk_manager.equity = current_equity
                if current_equity > risk_manager.max_equity:
                    risk_manager.max_equity = current_equity
            
            # Enregistrer l'equity
            self.equity_curve.append(current_equity)
            self.dates.append(current_date)
            
            # Afficher la progression
            if verbose and (i + 1) % 1000 == 0:
                progress = ((i + 1) / len(data)) * 100
                print(f"Progress: {progress:.1f}% | Trades: {self.strategy.total_trades} | "
                      f"Equity: ${current_equity:,.2f}")
        
        # Fermer toutes les positions restantes
        final_price = data['close'].iloc[-1]
        for position in list(self.strategy.open_positions):
            self.strategy.close_position(position, final_price)
        
        # Calculer les résultats
        self.results = self._calculate_results(data, risk_manager)
        
        if verbose:
            print("-" * 60)
            self.print_results()
        
        return self.results
    
    def _calculate_results(self, data: pd.DataFrame, risk_manager: Optional[RiskManager]) -> Dict:
        """Calcule les métriques de performance."""
        
        # Créer le DataFrame des trades
        trades_list = []
        for position in self.strategy.positions:
            trades_list.append(position.to_dict())
        
        self.trades_df = pd.DataFrame(trades_list) if trades_list else pd.DataFrame()
        
        # Métriques de base
        total_trades = self.strategy.total_trades
        winning_trades = self.strategy.winning_trades
        losing_trades = self.strategy.losing_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Profit/Loss
        total_profit = self.strategy.total_profit
        final_equity = self.equity_curve[-1]
        total_return = ((final_equity - self.initial_capital) / self.initial_capital) * 100
        
        # Calcul du Profit Factor
        gross_profit = sum([p.profit for p in self.strategy.positions if p.profit > 0])
        gross_loss = abs(sum([p.profit for p in self.strategy.positions if p.profit < 0]))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        
        # Drawdown
        equity_series = pd.Series(self.equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max * 100
        max_drawdown = abs(drawdown.min())
        
        # Sharpe Ratio
        returns = equity_series.pct_change().dropna()
        sharpe_ratio = 0.0
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
        
        # Sortino Ratio
        downside_returns = returns[returns < 0]
        sortino_ratio = 0.0
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino_ratio = (returns.mean() / downside_returns.std()) * np.sqrt(252)
        
        # Calmar Ratio
        calmar_ratio = (total_return / max_drawdown) if max_drawdown > 0 else 0
        
        # Average Trade
        avg_profit = total_profit / total_trades if total_trades > 0 else 0
        avg_win = (gross_profit / winning_trades) if winning_trades > 0 else 0
        avg_loss = (gross_loss / losing_trades) if losing_trades > 0 else 0
        
        # Expectancy
        expectancy = (win_rate/100 * avg_win) - ((100-win_rate)/100 * abs(avg_loss))
        
        # Durée du backtest
        duration = data.index[-1] - data.index[0]
        
        # Risk metrics
        risk_metrics = {}
        if risk_manager:
            risk_metrics = risk_manager.get_risk_metrics()
        
        results = {
            # Performance globale
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return_%': total_return,
            'total_profit_$': total_profit,
            
            # Trades
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_%': win_rate,
            
            # Profit/Loss
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'profit_factor': profit_factor,
            'avg_profit_per_trade': avg_profit,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'biggest_win': self.strategy.biggest_win,
            'biggest_loss': self.strategy.biggest_loss,
            'expectancy': expectancy,
            
            # Risk-adjusted metrics
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown_%': max_drawdown,
            
            # Période
            'start_date': data.index[0],
            'end_date': data.index[-1],
            'duration_days': duration.days,
            
            # Risk management
            'risk_metrics': risk_metrics
        }
        
        return results
    
    def print_results(self):
        """Affiche les résultats du backtest."""
        if not self.results:
            print("No results available. Run the backtest first.")
            return
        
        print("\n" + "=" * 60)
        print("📊 BACKTEST RESULTS")
        print("=" * 60)
        
        print("\n📈 PERFORMANCE")
        print(f"Initial Capital:     ${self.results['initial_capital']:,.2f}")
        print(f"Final Equity:        ${self.results['final_equity']:,.2f}")
        print(f"Total Return:        {self.results['total_return_%']:+.2f}%")
        print(f"Total Profit:        ${self.results['total_profit_$']:+,.2f}")
        
        print("\n📊 TRADES")
        print(f"Total Trades:        {self.results['total_trades']}")
        print(f"Winning Trades:      {self.results['winning_trades']}")
        print(f"Losing Trades:       {self.results['losing_trades']}")
        print(f"Win Rate:            {self.results['win_rate_%']:.2f}%")
        
        print("\n💰 PROFIT/LOSS")
        print(f"Gross Profit:        ${self.results['gross_profit']:,.2f}")
        print(f"Gross Loss:          ${self.results['gross_loss']:,.2f}")
        print(f"Profit Factor:       {self.results['profit_factor']:.2f}")
        print(f"Avg Profit/Trade:    ${self.results['avg_profit_per_trade']:+,.2f}")
        print(f"Avg Win:             ${self.results['avg_win']:,.2f}")
        print(f"Avg Loss:            ${self.results['avg_loss']:,.2f}")
        print(f"Biggest Win:         ${self.results['biggest_win']:,.2f}")
        print(f"Biggest Loss:        ${self.results['biggest_loss']:,.2f}")
        print(f"Expectancy:          ${self.results['expectancy']:+,.2f}")
        
        print("\n📉 RISK METRICS")
        print(f"Sharpe Ratio:        {self.results['sharpe_ratio']:.2f}")
        print(f"Sortino Ratio:       {self.results['sortino_ratio']:.2f}")
        print(f"Calmar Ratio:        {self.results['calmar_ratio']:.2f}")
        print(f"Max Drawdown:        {self.results['max_drawdown_%']:.2f}%")
        
        print("\n📅 PERIOD")
        print(f"Start Date:          {self.results['start_date']}")
        print(f"End Date:            {self.results['end_date']}")
        print(f"Duration:            {self.results['duration_days']} days")
        
        print("\n" + "=" * 60)
    
    def plot_equity_curve(self, save_path: Optional[str] = None):
        """Affiche la courbe d'equity."""
        if not self.equity_curve:
            print("No equity data available. Run the backtest first.")
            return
        
        plt.figure(figsize=(14, 7))
        
        # Equity curve
        plt.subplot(2, 1, 1)
        plt.plot(self.dates, self.equity_curve, linewidth=2, color='#2E86DE')
        plt.axhline(y=self.initial_capital, color='red', linestyle='--', alpha=0.5, label='Initial Capital')
        plt.fill_between(self.dates, self.initial_capital, self.equity_curve, 
                         where=np.array(self.equity_curve) >= self.initial_capital, 
                         alpha=0.3, color='green', label='Profit')
        plt.fill_between(self.dates, self.initial_capital, self.equity_curve, 
                         where=np.array(self.equity_curve) < self.initial_capital, 
                         alpha=0.3, color='red', label='Loss')
        plt.title('Equity Curve', fontsize=16, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Equity ($)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Drawdown
        plt.subplot(2, 1, 2)
        equity_series = pd.Series(self.equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max * 100
        plt.fill_between(self.dates, 0, drawdown, color='red', alpha=0.5)
        plt.title('Drawdown', fontsize=16, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Drawdown (%)')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {save_path}")
        else:
            plt.show()
    
    def plot_trades_distribution(self, save_path: Optional[str] = None):
        """Affiche la distribution des profits/pertes."""
        if self.trades_df is None or self.trades_df.empty:
            print("No trade data available.")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Distribution des profits
        axes[0, 0].hist(self.trades_df['profit'], bins=50, color='steelblue', edgecolor='black', alpha=0.7)
        axes[0, 0].axvline(x=0, color='red', linestyle='--', linewidth=2)
        axes[0, 0].set_title('Profit/Loss Distribution', fontweight='bold')
        axes[0, 0].set_xlabel('Profit ($)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Profits cumulés
        cumulative_profit = self.trades_df['profit'].cumsum()
        axes[0, 1].plot(cumulative_profit, linewidth=2, color='#2E86DE')
        axes[0, 1].axhline(y=0, color='red', linestyle='--', alpha=0.5)
        axes[0, 1].set_title('Cumulative Profit', fontweight='bold')
        axes[0, 1].set_xlabel('Trade #')
        axes[0, 1].set_ylabel('Cumulative Profit ($)')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Win/Loss ratio
        win_loss_data = self.trades_df['profit'].apply(lambda x: 'Win' if x > 0 else 'Loss')
        win_loss_count = win_loss_data.value_counts()
        colors = ['green' if x == 'Win' else 'red' for x in win_loss_count.index]
        axes[1, 0].bar(win_loss_count.index, win_loss_count.values, color=colors, alpha=0.7, edgecolor='black')
        axes[1, 0].set_title('Win/Loss Count', fontweight='bold')
        axes[1, 0].set_ylabel('Count')
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # Box plot
        win_trades = self.trades_df[self.trades_df['profit'] > 0]['profit']
        loss_trades = self.trades_df[self.trades_df['profit'] < 0]['profit']
        axes[1, 1].boxplot([win_trades, loss_trades], labels=['Wins', 'Losses'],
                          patch_artist=True,
                          boxprops=dict(facecolor='lightblue', color='black'),
                          medianprops=dict(color='red', linewidth=2))
        axes[1, 1].set_title('Win/Loss Box Plot', fontweight='bold')
        axes[1, 1].set_ylabel('Profit ($)')
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {save_path}")
        else:
            plt.show()
    
    def export_trades(self, filename: str = 'trades.csv'):
        """Exporte les trades vers un fichier CSV."""
        if self.trades_df is not None and not self.trades_df.empty:
            self.trades_df.to_csv(filename, index=False)
            print(f"Trades exported to {filename}")
        else:
            print("No trades to export.")
    
    def export_results(self, filename: str = 'results.csv'):
        """Exporte les résultats vers un fichier CSV."""
        if self.results:
            results_df = pd.DataFrame([self.results])
            results_df.to_csv(filename, index=False)
            print(f"Results exported to {filename}")
        else:
            print("No results to export.")
