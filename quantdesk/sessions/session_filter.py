"""
Session Filter
==============

Filtrage par sessions de trading pour optimiser les entrées.

Sessions principales:
- Asian: 23:00-08:00 GMT (faible volatilité)
- London: 08:00-17:00 GMT (haute volatilité)
- New York: 13:00-22:00 GMT (haute volatilité)
- London/NY Overlap: 13:00-17:00 GMT (MEILLEURE période!)
"""

from datetime import datetime, time
from typing import Dict, Optional, Tuple
import pandas as pd


class SessionFilter:
    """
    Filtre les trades selon les sessions de trading.
    
    Usage:
        filter = SessionFilter()
        
        if filter.is_best_time(current_time):
            # Trade!
        
        session = filter.get_current_session(current_time)
        # Returns: 'LONDON', 'NY', 'ASIAN', 'OVERLAP'
    """
    
    def __init__(
        self,
        allow_asian: bool = False,
        allow_london: bool = True,
        allow_ny: bool = True,
        prefer_overlap: bool = True,
        avoid_friday_afternoon: bool = True
    ):
        """
        Configure les sessions autorisées.
        
        Args:
            allow_asian: Autoriser session asiatique (déconseillé pour scalping)
            allow_london: Autoriser session de Londres
            allow_ny: Autoriser session de New York
            prefer_overlap: Préférer l'overlap London/NY
            avoid_friday_afternoon: Éviter vendredi après-midi (spread élevé)
        """
        self.allow_asian = allow_asian
        self.allow_london = allow_london
        self.allow_ny = allow_ny
        self.prefer_overlap = prefer_overlap
        self.avoid_friday_afternoon = avoid_friday_afternoon
        
        # Définition des sessions (GMT)
        self.sessions = {
            'ASIAN': {
                'start': time(23, 0),
                'end': time(8, 0),
                'volatility': 'LOW',
                'recommended': False
            },
            'LONDON': {
                'start': time(8, 0),
                'end': time(17, 0),
                'volatility': 'HIGH',
                'recommended': True
            },
            'NY': {
                'start': time(13, 0),
                'end': time(22, 0),
                'volatility': 'HIGH',
                'recommended': True
            },
            'OVERLAP': {  # London/NY overlap - MEILLEUR!
                'start': time(13, 0),
                'end': time(17, 0),
                'volatility': 'HIGHEST',
                'recommended': True
            }
        }
    
    def get_current_session(self, current_time: datetime) -> str:
        """
        Détermine la session de trading actuelle.
        
        Args:
            current_time: Heure actuelle (datetime)
            
        Returns:
            Nom de la session: 'ASIAN', 'LONDON', 'NY', 'OVERLAP'
        """
        # Convertir en GMT si nécessaire
        # (assume input is already GMT for simplicity)
        current_hour = current_time.time()
        
        # Overlap London/NY (prioritaire)
        if time(13, 0) <= current_hour <= time(17, 0):
            return 'OVERLAP'
        
        # London
        if time(8, 0) <= current_hour < time(17, 0):
            return 'LONDON'
        
        # NY (sans overlap)
        if time(17, 0) < current_hour <= time(22, 0):
            return 'NY'
        
        # Asian
        if current_hour >= time(23, 0) or current_hour < time(8, 0):
            return 'ASIAN'
        
        return 'UNKNOWN'
    
    def is_best_time(self, current_time: datetime) -> bool:
        """
        Vérifie si c'est le meilleur moment pour trader.
        
        Returns:
            True si conditions optimales
        """
        session = self.get_current_session(current_time)
        
        # Overlap = meilleur moment
        if self.prefer_overlap and session == 'OVERLAP':
            return self._check_day_restrictions(current_time)
        
        # Autres sessions selon configuration
        if session == 'LONDON' and self.allow_london:
            return self._check_day_restrictions(current_time)
        
        if session == 'NY' and self.allow_ny:
            return self._check_day_restrictions(current_time)
        
        if session == 'ASIAN' and self.allow_asian:
            return self._check_day_restrictions(current_time)
        
        return False
    
    def _check_day_restrictions(self, current_time: datetime) -> bool:
        """Vérifie les restrictions de jour (vendredi PM, weekend)."""
        
        # Weekend
        if current_time.weekday() >= 5:  # Samedi (5), Dimanche (6)
            return False
        
        # Vendredi après-midi (après 16h GMT)
        if self.avoid_friday_afternoon:
            if current_time.weekday() == 4 and current_time.hour >= 16:
                return False
        
        return True
    
    def get_session_info(self, current_time: datetime) -> Dict:
        """
        Retourne les informations complètes sur la session actuelle.
        
        Returns:
            {
                'name': str,
                'volatility': str,
                'recommended': bool,
                'is_tradeable': bool,
                'quality': 0-100
            }
        """
        session_name = self.get_current_session(current_time)
        is_tradeable = self.is_best_time(current_time)
        
        session_info = self.sessions.get(session_name, {})
        
        # Quality score
        quality = 0
        if session_name == 'OVERLAP':
            quality = 100
        elif session_name in ['LONDON', 'NY']:
            quality = 75
        elif session_name == 'ASIAN':
            quality = 30
        
        # Ajustements
        if current_time.weekday() == 4 and current_time.hour >= 14:
            quality -= 30  # Vendredi PM
        
        return {
            'name': session_name,
            'volatility': session_info.get('volatility', 'UNKNOWN'),
            'recommended': session_info.get('recommended', False),
            'is_tradeable': is_tradeable,
            'quality': max(0, quality),
            'day_of_week': current_time.strftime('%A'),
            'time_gmt': current_time.strftime('%H:%M GMT')
        }
    
    def get_next_best_session(self, current_time: datetime) -> Dict:
        """
        Calcule quand sera la prochaine bonne session.
        
        Returns:
            {
                'session': str,
                'starts_at': datetime,
                'hours_until': float
            }
        """
        current_session = self.get_current_session(current_time)
        current_hour = current_time.hour
        
        # Si dans overlap ou bonne session, retourner actuel
        if current_session in ['OVERLAP', 'LONDON', 'NY'] and self.is_best_time(current_time):
            return {
                'session': current_session,
                'starts_at': current_time,
                'hours_until': 0
            }
        
        # Calculer prochaine session
        # Logique simplifiée
        if current_hour < 8:
            return {'session': 'LONDON', 'hours_until': 8 - current_hour}
        elif current_hour < 13:
            return {'session': 'OVERLAP', 'hours_until': 13 - current_hour}
        elif current_hour < 17:
            return {'session': 'NY', 'hours_until': 0}
        else:
            return {'session': 'LONDON', 'hours_until': 24 - current_hour + 8}
    
    def should_trade_now(self, current_time: datetime) -> Tuple[bool, str]:
        """
        Décision finale: trader maintenant?
        
        Returns:
            (should_trade: bool, reason: str)
        """
        if not self.is_best_time(current_time):
            session = self.get_current_session(current_time)
            return False, f"Mauvaise session: {session}"
        
        session_info = self.get_session_info(current_time)
        
        if session_info['quality'] < 50:
            return False, f"Qualité session trop faible: {session_info['quality']}"
        
        return True, f"Session optimale: {session_info['name']}"
