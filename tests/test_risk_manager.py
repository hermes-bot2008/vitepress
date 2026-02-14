"""
Tests for Risk Manager
======================
"""

import pytest
from quantdesk.risk.risk_manager import RiskManager


class TestRiskManager:
    """Tests for RiskManager class."""
    
    def test_initialization(self):
        """Test risk manager initialization."""
        risk_manager = RiskManager(
            initial_capital=10000.0,
            max_daily_loss=100.0,
            max_position_size=0.1
        )
        
        assert risk_manager.initial_capital == 10000.0
        assert risk_manager.current_capital == 10000.0
        assert risk_manager.max_daily_loss == 100.0
        assert risk_manager.max_position_size == 0.1
        assert risk_manager.trading_enabled == True
    
    def test_can_open_position(self):
        """Test position opening validation."""
        risk_manager = RiskManager(
            initial_capital=10000.0,
            max_open_positions=5
        )
        
        can_open, reason = risk_manager.can_open_position(
            current_positions=3,
            proposed_lot_size=0.01
        )
        
        assert can_open == True
        assert "allowed" in reason.lower()
    
    def test_max_positions_limit(self):
        """Test maximum positions limit."""
        risk_manager = RiskManager(
            initial_capital=10000.0,
            max_open_positions=5
        )
        
        can_open, reason = risk_manager.can_open_position(
            current_positions=5,
            proposed_lot_size=0.01
        )
        
        assert can_open == False
        assert "max positions" in reason.lower()
    
    def test_daily_loss_limit(self):
        """Test daily loss limit."""
        risk_manager = RiskManager(
            initial_capital=10000.0,
            max_daily_loss=100.0
        )
        
        # Simulate a loss
        risk_manager.daily_loss = -100.0
        
        can_open, reason = risk_manager.can_open_position(
            current_positions=1,
            proposed_lot_size=0.01
        )
        
        assert can_open == False
        assert "daily loss" in reason.lower()
    
    def test_calculate_drawdown(self):
        """Test drawdown calculation."""
        risk_manager = RiskManager(initial_capital=10000.0)
        
        # Simulate profit then loss
        risk_manager.max_equity = 12000.0
        risk_manager.equity = 11000.0
        
        drawdown = risk_manager.calculate_drawdown()
        
        assert drawdown > 0
        assert drawdown < 10  # Should be around 8.33%
    
    def test_update_equity(self):
        """Test equity update."""
        risk_manager = RiskManager(initial_capital=10000.0)
        
        initial_equity = risk_manager.equity
        
        # Update with profit
        risk_manager.update_equity(100.0)
        
        assert risk_manager.equity > initial_equity
        assert risk_manager.daily_profit == 100.0
    
    def test_position_size_calculation(self):
        """Test position size calculation."""
        risk_manager = RiskManager(
            initial_capital=10000.0,
            max_risk_per_trade=1.0
        )
        
        entry_price = 2000.0
        stop_loss = 1998.0
        
        position_size = risk_manager.calculate_position_size(
            entry_price=entry_price,
            stop_loss=stop_loss
        )
        
        assert position_size > 0
        assert position_size <= risk_manager.max_position_size
    
    def test_emergency_stop(self):
        """Test emergency stop."""
        risk_manager = RiskManager(initial_capital=10000.0)
        
        assert risk_manager.trading_enabled == True
        
        risk_manager.emergency_stop("Test emergency")
        
        assert risk_manager.trading_enabled == False
    
    def test_reset(self):
        """Test risk manager reset."""
        risk_manager = RiskManager(initial_capital=10000.0)
        
        # Simulate some trading
        risk_manager.update_equity(500.0)
        risk_manager.daily_trades = 10
        
        # Reset
        risk_manager.reset()
        
        assert risk_manager.current_capital == risk_manager.initial_capital
        assert risk_manager.daily_trades == 0
        assert risk_manager.trading_enabled == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
