"""
Tests for Technical Indicators
===============================
"""

import pytest
import pandas as pd
import numpy as np
from quantdesk.indicators.technical_indicators import TechnicalIndicators


@pytest.fixture
def sample_prices():
    """Fixture: Sample price data."""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    return pd.Series(prices, index=dates)


@pytest.fixture
def sample_ohlc():
    """Fixture: Sample OHLC data."""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
    close = 100 + np.cumsum(np.random.randn(100) * 0.5)
    high = close + np.abs(np.random.randn(100) * 0.2)
    low = close - np.abs(np.random.randn(100) * 0.2)
    open_price = close + np.random.randn(100) * 0.1
    
    return pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close
    }, index=dates)


class TestTechnicalIndicators:
    """Tests for TechnicalIndicators class."""
    
    def test_calculate_sma(self, sample_prices):
        """Test SMA calculation."""
        indicators = TechnicalIndicators()
        sma = indicators.calculate_sma(sample_prices, period=20)
        
        assert sma is not None
        assert len(sma) == len(sample_prices)
        assert not sma.iloc[-1] == 0  # Last value should not be zero
    
    def test_calculate_ema(self, sample_prices):
        """Test EMA calculation."""
        indicators = TechnicalIndicators()
        ema = indicators.calculate_ema(sample_prices, period=20)
        
        assert ema is not None
        assert len(ema) == len(sample_prices)
    
    def test_calculate_rsi(self, sample_prices):
        """Test RSI calculation."""
        indicators = TechnicalIndicators()
        rsi = indicators.calculate_rsi(sample_prices, period=14)
        
        assert rsi is not None
        assert len(rsi) == len(sample_prices)
        
        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_calculate_macd(self, sample_prices):
        """Test MACD calculation."""
        indicators = TechnicalIndicators()
        macd_line, signal_line, histogram = indicators.calculate_macd(
            sample_prices, fast_period=12, slow_period=26, signal_period=9
        )
        
        assert macd_line is not None
        assert signal_line is not None
        assert histogram is not None
        
        assert len(macd_line) == len(sample_prices)
        assert len(signal_line) == len(sample_prices)
        assert len(histogram) == len(sample_prices)
    
    def test_calculate_bollinger_bands(self, sample_prices):
        """Test Bollinger Bands calculation."""
        indicators = TechnicalIndicators()
        upper, middle, lower = indicators.calculate_bollinger_bands(
            sample_prices, period=20, std_dev=2.0
        )
        
        assert upper is not None
        assert middle is not None
        assert lower is not None
        
        # Upper should be >= middle >= lower
        valid_idx = ~upper.isna() & ~middle.isna() & ~lower.isna()
        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (middle[valid_idx] >= lower[valid_idx]).all()
    
    def test_calculate_atr(self, sample_ohlc):
        """Test ATR calculation."""
        indicators = TechnicalIndicators()
        atr = indicators.calculate_atr(
            sample_ohlc['high'],
            sample_ohlc['low'],
            sample_ohlc['close'],
            period=14
        )
        
        assert atr is not None
        assert len(atr) == len(sample_ohlc)
        
        # ATR should be positive
        valid_atr = atr.dropna()
        assert (valid_atr >= 0).all()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
