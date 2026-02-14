"""
Tests for Trading Strategies
=============================
"""

import pytest
import pandas as pd
import numpy as np
from quantdesk.algorithms.hyper_scalper import HyperScalper
from quantdesk.algorithms.momentum import MomentumStrategy
from quantdesk.algorithms.mean_reversion import MeanReversionStrategy


@pytest.fixture
def sample_data():
    """Fixture: Sample market data."""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=200, freq='5min')
    close = 2000 + np.cumsum(np.random.randn(200) * 0.5)
    high = close + np.abs(np.random.randn(200) * 0.5)
    low = close - np.abs(np.random.randn(200) * 0.5)
    open_price = close + np.random.randn(200) * 0.3
    volume = np.random.randint(1000, 10000, 200)
    
    return pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)


class TestHyperScalper:
    """Tests for HyperScalper strategy."""
    
    def test_initialization(self):
        """Test strategy initialization."""
        strategy = HyperScalper(
            symbol="XAUUSD",
            lot_size=0.01,
            tp_pips=1.5,
            sl_pips=2.0
        )
        
        assert strategy.symbol == "XAUUSD"
        assert strategy.lot_size == 0.01
        assert strategy.tp_pips == 1.5
        assert strategy.sl_pips == 2.0
        assert strategy.total_trades == 0
    
    def test_generate_signal(self, sample_data):
        """Test signal generation."""
        strategy = HyperScalper(symbol="XAUUSD")
        
        signal = strategy.generate_signal(sample_data)
        
        # Signal should be -1, 0, or 1
        assert signal in [-1, 0, 1]
    
    def test_execute_trade(self, sample_data):
        """Test trade execution."""
        strategy = HyperScalper(symbol="XAUUSD", lot_size=0.01)
        
        current_price = sample_data['close'].iloc[-1]
        strategy.update_market_data(sample_data)
        
        initial_trades = strategy.total_trades
        strategy.execute_trade(signal=1, current_price=current_price)
        
        assert strategy.total_trades == initial_trades + 1
        assert len(strategy.open_positions) == 1
    
    def test_calculate_sl_tp(self):
        """Test SL/TP calculation."""
        strategy = HyperScalper(tp_pips=1.5, sl_pips=2.0)
        
        entry_price = 2000.0
        sl, tp = strategy.calculate_sl_tp(entry_price, 'BUY')
        
        assert sl < entry_price  # SL should be below entry for BUY
        assert tp > entry_price  # TP should be above entry for BUY


class TestMomentumStrategy:
    """Tests for Momentum strategy."""
    
    def test_initialization(self):
        """Test strategy initialization."""
        strategy = MomentumStrategy(
            symbol="EURUSD",
            lot_size=0.01
        )
        
        assert strategy.symbol == "EURUSD"
        assert strategy.lot_size == 0.01
        assert strategy.total_trades == 0
    
    def test_generate_signal(self, sample_data):
        """Test signal generation."""
        strategy = MomentumStrategy(symbol="EURUSD")
        
        signal = strategy.generate_signal(sample_data)
        
        assert signal in [-1, 0, 1]


class TestMeanReversionStrategy:
    """Tests for Mean Reversion strategy."""
    
    def test_initialization(self):
        """Test strategy initialization."""
        strategy = MeanReversionStrategy(
            symbol="GBPUSD",
            lot_size=0.01
        )
        
        assert strategy.symbol == "GBPUSD"
        assert strategy.lot_size == 0.01
        assert strategy.total_trades == 0
    
    def test_generate_signal(self, sample_data):
        """Test signal generation."""
        strategy = MeanReversionStrategy(symbol="GBPUSD")
        
        signal = strategy.generate_signal(sample_data)
        
        assert signal in [-1, 0, 1]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
