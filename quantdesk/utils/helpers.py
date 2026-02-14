"""
Helper Functions
================

Fonctions utilitaires diverses.
"""

from typing import Union


def format_currency(amount: float, currency: str = '$') -> str:
    """
    Formate un montant en devise.
    
    Args:
        amount: Montant à formater
        currency: Symbole de devise
        
    Returns:
        Chaîne formatée
    """
    sign = '+' if amount >= 0 else ''
    return f"{sign}{currency}{amount:,.2f}"


def calculate_pips(price1: float, price2: float, pip_position: int = 4) -> float:
    """
    Calcule la différence en pips entre deux prix.
    
    Args:
        price1: Premier prix
        price2: Deuxième prix
        pip_position: Position du pip (4 pour la plupart des paires, 2 pour JPY)
        
    Returns:
        Différence en pips
    """
    multiplier = 10 ** pip_position
    return abs(price1 - price2) * multiplier


def calculate_lot_value(
    lot_size: float,
    pip_value: float = 10.0,
    pips: float = 1.0
) -> float:
    """
    Calcule la valeur monétaire d'un mouvement de prix.
    
    Args:
        lot_size: Taille du lot
        pip_value: Valeur d'un pip pour 1 lot standard
        pips: Nombre de pips de mouvement
        
    Returns:
        Valeur en dollars
    """
    return lot_size * pip_value * pips


def calculate_position_pnl(
    position_type: str,
    entry_price: float,
    current_price: float,
    lot_size: float,
    contract_size: int = 100000
) -> float:
    """
    Calcule le P&L d'une position.
    
    Args:
        position_type: 'BUY' ou 'SELL'
        entry_price: Prix d'entrée
        current_price: Prix actuel
        lot_size: Taille du lot
        contract_size: Taille du contrat (100,000 pour forex standard)
        
    Returns:
        Profit ou perte en dollars
    """
    if position_type.upper() == 'BUY':
        pnl = (current_price - entry_price) * lot_size * contract_size
    else:  # SELL
        pnl = (entry_price - current_price) * lot_size * contract_size
    
    return pnl


def calculate_risk_reward_ratio(
    entry_price: float,
    stop_loss: float,
    take_profit: float
) -> float:
    """
    Calcule le ratio risque/récompense.
    
    Args:
        entry_price: Prix d'entrée
        stop_loss: Niveau de stop loss
        take_profit: Niveau de take profit
        
    Returns:
        Ratio risque/récompense
    """
    risk = abs(entry_price - stop_loss)
    reward = abs(take_profit - entry_price)
    
    if risk == 0:
        return 0.0
    
    return reward / risk


def validate_ohlc_data(data) -> bool:
    """
    Valide que les données OHLC sont cohérentes.
    
    Args:
        data: DataFrame avec colonnes OHLC
        
    Returns:
        True si valide, False sinon
    """
    required_columns = ['open', 'high', 'low', 'close']
    
    # Vérifier les colonnes
    if not all(col in data.columns for col in required_columns):
        return False
    
    # Vérifier que high >= low
    if not (data['high'] >= data['low']).all():
        return False
    
    # Vérifier que high >= open et high >= close
    if not ((data['high'] >= data['open']).all() and (data['high'] >= data['close']).all()):
        return False
    
    # Vérifier que low <= open et low <= close
    if not ((data['low'] <= data['open']).all() and (data['low'] <= data['close']).all()):
        return False
    
    return True


def calculate_win_rate(winning_trades: int, total_trades: int) -> float:
    """
    Calcule le taux de réussite.
    
    Args:
        winning_trades: Nombre de trades gagnants
        total_trades: Nombre total de trades
        
    Returns:
        Taux de réussite en pourcentage
    """
    if total_trades == 0:
        return 0.0
    
    return (winning_trades / total_trades) * 100


def calculate_expectancy(
    win_rate: float,
    avg_win: float,
    avg_loss: float
) -> float:
    """
    Calcule l'espérance mathématique par trade.
    
    Args:
        win_rate: Taux de réussite (%)
        avg_win: Gain moyen
        avg_loss: Perte moyenne
        
    Returns:
        Espérance par trade
    """
    return (win_rate/100 * avg_win) - ((100-win_rate)/100 * abs(avg_loss))
