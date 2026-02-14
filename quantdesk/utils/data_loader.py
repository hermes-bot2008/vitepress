"""
Data Loader
===========

Chargement de données de marché depuis différentes sources.
"""

import pandas as pd
from typing import Optional
from datetime import datetime, timedelta

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


class DataLoader:
    """Classe pour charger les données de marché."""
    
    @staticmethod
    def load_from_yahoo(
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = '1h'
    ) -> pd.DataFrame:
        """
        Charge les données depuis Yahoo Finance.
        
        Args:
            symbol: Symbole du ticker (ex: 'GC=F' pour l'or, 'EURUSD=X' pour EUR/USD)
            start_date: Date de début (format 'YYYY-MM-DD')
            end_date: Date de fin (format 'YYYY-MM-DD')
            interval: Intervalle ('1m', '5m', '15m', '1h', '1d', etc.)
            
        Returns:
            DataFrame avec colonnes ['open', 'high', 'low', 'close', 'volume']
        """
        if not YFINANCE_AVAILABLE:
            raise ImportError("yfinance is not installed. Install it with: pip install yfinance")
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"Loading data for {symbol} from {start_date} to {end_date}...")
        
        ticker = yf.Ticker(symbol)
        data = ticker.history(start=start_date, end=end_date, interval=interval)
        
        if data.empty:
            raise ValueError(f"No data found for {symbol}")
        
        # Renommer les colonnes en minuscules
        data.columns = [col.lower() for col in data.columns]
        
        # Garder seulement les colonnes nécessaires
        columns_to_keep = ['open', 'high', 'low', 'close', 'volume']
        available_columns = [col for col in columns_to_keep if col in data.columns]
        data = data[available_columns]
        
        print(f"Loaded {len(data)} bars")
        
        return data
    
    @staticmethod
    def load_from_csv(
        filepath: str,
        date_column: str = 'timestamp',
        parse_dates: bool = True
    ) -> pd.DataFrame:
        """
        Charge les données depuis un fichier CSV.
        
        Args:
            filepath: Chemin vers le fichier CSV
            date_column: Nom de la colonne de dates
            parse_dates: Parser les dates automatiquement
            
        Returns:
            DataFrame avec les données
        """
        print(f"Loading data from {filepath}...")
        
        if parse_dates:
            data = pd.read_csv(filepath, parse_dates=[date_column], index_col=date_column)
        else:
            data = pd.read_csv(filepath)
        
        # Renommer les colonnes en minuscules
        data.columns = [col.lower() for col in data.columns]
        
        print(f"Loaded {len(data)} rows")
        
        return data
    
    @staticmethod
    def generate_sample_data(
        start_date: str = '2024-01-01',
        end_date: str = '2024-12-31',
        freq: str = '1H',
        initial_price: float = 2000.0,
        volatility: float = 0.02
    ) -> pd.DataFrame:
        """
        Génère des données de prix simulées pour les tests.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            freq: Fréquence ('1H', '15min', '1D', etc.)
            initial_price: Prix initial
            volatility: Volatilité (écart-type des rendements)
            
        Returns:
            DataFrame avec données simulées
        """
        print(f"Generating sample data from {start_date} to {end_date}...")
        
        # Créer l'index temporel
        dates = pd.date_range(start=start_date, end=end_date, freq=freq)
        
        # Générer les rendements aléatoires
        import numpy as np
        returns = pd.Series(index=dates).apply(lambda x: np.random.normal(0, volatility))
        
        # Générer les prix de clôture
        close = initial_price * (1 + returns).cumprod()
        
        # Générer OHLC
        import numpy as np
        high = close * (1 + pd.Series(index=dates).apply(lambda x: abs(np.random.normal(0, volatility/2))))
        low = close * (1 - pd.Series(index=dates).apply(lambda x: abs(np.random.normal(0, volatility/2))))
        open_price = close.shift(1).fillna(initial_price)
        
        # Générer le volume
        volume = pd.Series(index=dates).apply(lambda x: int(np.random.uniform(1000, 10000)))
        
        # Créer le DataFrame
        data = pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
        
        print(f"Generated {len(data)} bars")
        
        return data
    
    @staticmethod
    def resample_data(
        data: pd.DataFrame,
        timeframe: str = '4H'
    ) -> pd.DataFrame:
        """
        Ré-échantillonne les données vers un timeframe différent.
        
        Args:
            data: DataFrame source
            timeframe: Nouveau timeframe ('5min', '1H', '4H', '1D', etc.)
            
        Returns:
            DataFrame ré-échantillonné
        """
        print(f"Resampling data to {timeframe}...")
        
        resampled = data.resample(timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        print(f"Resampled to {len(resampled)} bars")
        
        return resampled
