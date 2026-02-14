"""
Risk Manager
============

Système de gestion des risques pour le trading.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd


class RiskManager:
    """
    Gestionnaire de risques pour contrôler l'exposition et les pertes.
    
    Paramètres:
        initial_capital: Capital initial
        max_daily_loss: Perte journalière maximale en dollars
        max_daily_loss_percent: Perte journalière maximale en pourcentage
        max_position_size: Taille maximale d'une position (en lots)
        max_open_positions: Nombre maximum de positions ouvertes
        max_drawdown_percent: Drawdown maximum autorisé (%)
        use_equity_protection: Activer la protection du capital
        equity_protection_percent: Pourcentage de protection du capital
        max_risk_per_trade: Risque maximum par trade (%)
        max_leverage: Levier maximum autorisé
    """
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        max_daily_loss: float = 100.0,
        max_daily_loss_percent: float = 2.0,
        max_position_size: float = 0.1,
        max_open_positions: int = 10,
        max_drawdown_percent: float = 10.0,
        use_equity_protection: bool = True,
        equity_protection_percent: float = 10.0,
        max_risk_per_trade: float = 1.0,
        max_leverage: float = 10.0
    ):
        # Capital
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.equity = initial_capital
        self.max_equity = initial_capital
        
        # Limites de risque
        self.max_daily_loss = max_daily_loss
        self.max_daily_loss_percent = max_daily_loss_percent
        self.max_position_size = max_position_size
        self.max_open_positions = max_open_positions
        self.max_drawdown_percent = max_drawdown_percent
        self.max_risk_per_trade = max_risk_per_trade
        self.max_leverage = max_leverage
        
        # Protection du capital
        self.use_equity_protection = use_equity_protection
        self.equity_protection_percent = equity_protection_percent
        self.min_equity = initial_capital * (1 - equity_protection_percent / 100)
        
        # Statistiques journalières
        self.daily_profit = 0.0
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        
        # État du trading
        self.trading_enabled = True
        self.stop_loss_hit = False
        self.drawdown_exceeded = False
        
        # Historique
        self.equity_history = [initial_capital]
        self.daily_returns = []
        self.trade_history = []
    
    def can_open_position(
        self,
        current_positions: int,
        proposed_lot_size: float
    ) -> tuple[bool, str]:
        """
        Vérifie si une nouvelle position peut être ouverte.
        
        Returns:
            Tuple (can_open, reason)
        """
        if not self.trading_enabled:
            return False, "Trading disabled by risk manager"
        
        # Vérifier le nombre de positions
        if current_positions >= self.max_open_positions:
            return False, f"Max positions reached ({self.max_open_positions})"
        
        # Vérifier la taille de la position
        if proposed_lot_size > self.max_position_size:
            return False, f"Position size exceeds maximum ({self.max_position_size})"
        
        # Vérifier la perte journalière en dollars
        if abs(self.daily_loss) >= self.max_daily_loss:
            self.trading_enabled = False
            return False, f"Daily loss limit reached (${self.max_daily_loss})"
        
        # Vérifier la perte journalière en pourcentage
        daily_loss_percent = (abs(self.daily_loss) / self.initial_capital) * 100
        if daily_loss_percent >= self.max_daily_loss_percent:
            self.trading_enabled = False
            return False, f"Daily loss % limit reached ({self.max_daily_loss_percent}%)"
        
        # Vérifier la protection du capital
        if self.use_equity_protection and self.equity < self.min_equity:
            self.trading_enabled = False
            return False, f"Equity protection triggered (${self.min_equity})"
        
        # Vérifier le drawdown
        current_drawdown = self.calculate_drawdown()
        if current_drawdown >= self.max_drawdown_percent:
            self.trading_enabled = False
            self.drawdown_exceeded = True
            return False, f"Max drawdown exceeded ({self.max_drawdown_percent}%)"
        
        return True, "Position allowed"
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        risk_percent: Optional[float] = None
    ) -> float:
        """
        Calcule la taille de position optimale basée sur le risque.
        
        Args:
            entry_price: Prix d'entrée
            stop_loss: Niveau de stop loss
            risk_percent: Pourcentage du capital à risquer (défaut: max_risk_per_trade)
            
        Returns:
            Taille de position en lots
        """
        if risk_percent is None:
            risk_percent = self.max_risk_per_trade
        
        # Montant à risquer
        risk_amount = self.current_capital * (risk_percent / 100)
        
        # Distance du stop loss
        sl_distance = abs(entry_price - stop_loss)
        
        if sl_distance == 0:
            return self.max_position_size
        
        # Calculer la taille de position
        # Pour le forex: 1 lot = 100,000 unités
        pip_value = 10  # Pour 1 lot standard
        pips_at_risk = sl_distance * 10000  # Convertir en pips
        
        position_size = risk_amount / (pips_at_risk * pip_value / 100000)
        
        # Limiter à la taille maximale
        position_size = min(position_size, self.max_position_size)
        
        return round(position_size, 2)
    
    def update_equity(self, profit: float):
        """Met à jour le capital et l'equity."""
        self.current_capital += profit
        self.equity = self.current_capital
        
        # Mettre à jour l'equity maximum
        if self.equity > self.max_equity:
            self.max_equity = self.equity
        
        # Mettre à jour les statistiques journalières
        if profit > 0:
            self.daily_profit += profit
        else:
            self.daily_loss += profit
        
        self.daily_trades += 1
        
        # Historique
        self.equity_history.append(self.equity)
        
        # Mettre à jour la protection du capital
        if self.use_equity_protection:
            self.min_equity = self.max_equity * (1 - self.equity_protection_percent / 100)
    
    def calculate_drawdown(self) -> float:
        """
        Calcule le drawdown actuel en pourcentage.
        
        Returns:
            Drawdown en pourcentage
        """
        if self.max_equity == 0:
            return 0.0
        
        drawdown = ((self.max_equity - self.equity) / self.max_equity) * 100
        return max(0.0, drawdown)
    
    def calculate_max_drawdown(self) -> float:
        """
        Calcule le drawdown maximum historique.
        
        Returns:
            Max drawdown en pourcentage
        """
        if not self.equity_history or len(self.equity_history) < 2:
            return 0.0
        
        equity_series = pd.Series(self.equity_history)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max * 100
        
        return abs(drawdown.min())
    
    def reset_daily_stats(self):
        """Réinitialise les statistiques journalières."""
        # Sauvegarder le rendement journalier
        if self.initial_capital > 0:
            daily_return = (self.daily_profit + self.daily_loss) / self.initial_capital * 100
            self.daily_returns.append(daily_return)
        
        # Réinitialiser
        self.daily_profit = 0.0
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        
        # Réactiver le trading si drawdown respecté
        if not self.drawdown_exceeded:
            self.trading_enabled = True
    
    def check_daily_reset(self):
        """Vérifie si on doit réinitialiser les stats journalières."""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.reset_daily_stats()
    
    def get_risk_metrics(self) -> Dict:
        """
        Retourne les métriques de risque actuelles.
        
        Returns:
            Dictionnaire des métriques de risque
        """
        # Calculer les métriques
        total_return = ((self.equity - self.initial_capital) / self.initial_capital) * 100
        current_drawdown = self.calculate_drawdown()
        max_drawdown = self.calculate_max_drawdown()
        
        # Sharpe Ratio (simplifié)
        sharpe_ratio = 0.0
        if len(self.daily_returns) > 0:
            avg_return = sum(self.daily_returns) / len(self.daily_returns)
            if len(self.daily_returns) > 1:
                std_return = pd.Series(self.daily_returns).std()
                if std_return > 0:
                    sharpe_ratio = (avg_return / std_return) * (252 ** 0.5)
        
        return {
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'equity': self.equity,
            'max_equity': self.max_equity,
            'total_return_%': total_return,
            'daily_profit': self.daily_profit,
            'daily_loss': self.daily_loss,
            'daily_trades': self.daily_trades,
            'current_drawdown_%': current_drawdown,
            'max_drawdown_%': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'trading_enabled': self.trading_enabled,
            'min_equity': self.min_equity
        }
    
    def get_position_limits(self) -> Dict:
        """Retourne les limites de position."""
        return {
            'max_position_size': self.max_position_size,
            'max_open_positions': self.max_open_positions,
            'max_daily_loss': self.max_daily_loss,
            'max_daily_loss_percent': self.max_daily_loss_percent,
            'max_drawdown_percent': self.max_drawdown_percent,
            'max_risk_per_trade': self.max_risk_per_trade,
            'max_leverage': self.max_leverage
        }
    
    def emergency_stop(self, reason: str = "Emergency stop triggered"):
        """Arrêt d'urgence du trading."""
        self.trading_enabled = False
        print(f"⚠️ EMERGENCY STOP: {reason}")
        print(f"Current Equity: ${self.equity:.2f}")
        print(f"Drawdown: {self.calculate_drawdown():.2f}%")
    
    def enable_trading(self):
        """Réactive le trading (à utiliser avec précaution)."""
        self.trading_enabled = True
        self.stop_loss_hit = False
        print("✅ Trading re-enabled")
    
    def reset(self):
        """Réinitialise le risk manager."""
        self.current_capital = self.initial_capital
        self.equity = self.initial_capital
        self.max_equity = self.initial_capital
        self.min_equity = self.initial_capital * (1 - self.equity_protection_percent / 100)
        
        self.daily_profit = 0.0
        self.daily_loss = 0.0
        self.daily_trades = 0
        self.last_reset_date = datetime.now().date()
        
        self.trading_enabled = True
        self.stop_loss_hit = False
        self.drawdown_exceeded = False
        
        self.equity_history = [self.initial_capital]
        self.daily_returns = []
        self.trade_history = []
