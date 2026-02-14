"""
Base Strategy Class
===================

Classe de base pour toutes les stratégies de trading.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd


class Position:
    """Représente une position de trading."""
    
    def __init__(
        self,
        ticket: int,
        symbol: str,
        position_type: str,  # 'BUY' or 'SELL'
        entry_price: float,
        lot_size: float,
        stop_loss: float,
        take_profit: float,
        open_time: datetime,
        magic_number: int = 0
    ):
        self.ticket = ticket
        self.symbol = symbol
        self.position_type = position_type
        self.entry_price = entry_price
        self.lot_size = lot_size
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.open_time = open_time
        self.close_time: Optional[datetime] = None
        self.close_price: Optional[float] = None
        self.profit: float = 0.0
        self.magic_number = magic_number
        self.is_open = True
    
    def close(self, close_price: float, close_time: datetime):
        """Ferme la position."""
        self.close_price = close_price
        self.close_time = close_time
        self.is_open = False
        
        # Calculer le profit
        if self.position_type == 'BUY':
            self.profit = (close_price - self.entry_price) * self.lot_size * 100000
        else:  # SELL
            self.profit = (self.entry_price - close_price) * self.lot_size * 100000
    
    def get_current_profit(self, current_price: float) -> float:
        """Calcule le profit actuel."""
        if self.position_type == 'BUY':
            return (current_price - self.entry_price) * self.lot_size * 100000
        else:  # SELL
            return (self.entry_price - current_price) * self.lot_size * 100000
    
    def to_dict(self) -> Dict:
        """Convertit la position en dictionnaire."""
        return {
            'ticket': self.ticket,
            'symbol': self.symbol,
            'type': self.position_type,
            'entry_price': self.entry_price,
            'lot_size': self.lot_size,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'open_time': self.open_time,
            'close_time': self.close_time,
            'close_price': self.close_price,
            'profit': self.profit,
            'is_open': self.is_open
        }


class BaseStrategy(ABC):
    """Classe de base pour toutes les stratégies de trading."""
    
    def __init__(
        self,
        symbol: str,
        lot_size: float = 0.01,
        magic_number: int = 123456
    ):
        self.symbol = symbol
        self.lot_size = lot_size
        self.magic_number = magic_number
        
        # Positions
        self.positions: List[Position] = []
        self.open_positions: List[Position] = []
        
        # Statistiques
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.biggest_win = 0.0
        self.biggest_loss = 0.0
        
        # Données de marché
        self.current_price: float = 0.0
        self.current_time: datetime = datetime.now()
        self.market_data: Optional[pd.DataFrame] = None
    
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> int:
        """
        Génère un signal de trading.
        
        Returns:
            1: Signal d'achat (BUY)
            -1: Signal de vente (SELL)
            0: Pas de signal
        """
        pass
    
    @abstractmethod
    def should_close_position(self, position: Position, current_price: float) -> bool:
        """Détermine si une position doit être fermée."""
        pass
    
    def update_market_data(self, data: pd.DataFrame):
        """Met à jour les données de marché."""
        self.market_data = data
        if not data.empty:
            self.current_price = data['close'].iloc[-1]
            self.current_time = data.index[-1]
    
    def open_position(
        self,
        position_type: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ) -> Position:
        """Ouvre une nouvelle position."""
        self.total_trades += 1
        ticket = self.total_trades
        
        position = Position(
            ticket=ticket,
            symbol=self.symbol,
            position_type=position_type,
            entry_price=entry_price,
            lot_size=self.lot_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            open_time=self.current_time,
            magic_number=self.magic_number
        )
        
        self.positions.append(position)
        self.open_positions.append(position)
        
        return position
    
    def close_position(self, position: Position, close_price: float):
        """Ferme une position."""
        position.close(close_price, self.current_time)
        
        # Mettre à jour les statistiques
        self.total_profit += position.profit
        
        if position.profit > 0:
            self.winning_trades += 1
            if position.profit > self.biggest_win:
                self.biggest_win = position.profit
        else:
            self.losing_trades += 1
            if position.profit < self.biggest_loss:
                self.biggest_loss = position.profit
        
        # Retirer de la liste des positions ouvertes
        if position in self.open_positions:
            self.open_positions.remove(position)
    
    def manage_open_positions(self):
        """Gère les positions ouvertes."""
        positions_to_close = []
        
        for position in self.open_positions:
            if self.should_close_position(position, self.current_price):
                positions_to_close.append(position)
        
        for position in positions_to_close:
            self.close_position(position, self.current_price)
    
    def get_statistics(self) -> Dict:
        """Retourne les statistiques de la stratégie."""
        win_rate = 0.0
        if self.total_trades > 0:
            win_rate = (self.winning_trades / self.total_trades) * 100
        
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_profit': self.total_profit,
            'biggest_win': self.biggest_win,
            'biggest_loss': self.biggest_loss,
            'open_positions': len(self.open_positions)
        }
    
    def reset(self):
        """Réinitialise la stratégie."""
        self.positions = []
        self.open_positions = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.biggest_win = 0.0
        self.biggest_loss = 0.0
