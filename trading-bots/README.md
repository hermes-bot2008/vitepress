# GOLD AI Pro Hyper Scalper

An ultra-high frequency scalping system for gold trading (XAUUSDm) designed for MetaTrader 4.

## Overview

This Expert Advisor (EA) implements an aggressive scalping strategy targeting up to 20,000 trades per day with minimal profit targets (1.5 pips TP, 2.0 pips SL).

## Key Features

### Core Scalping Engine
- **Ultra-fast execution**: Trades on every tick with 1ms timer resolution
- **High-frequency trading**: Designed for up to 20K trades/day
- **Tight spreads**: 1.5 pip take profit, 2.0 pip stop loss
- **Position management**: Up to 50 simultaneous positions
- **Rate limiting**: Maximum 5 trades per second to prevent over-trading

### Entry Strategies

1. **Tick Moving Average (Tick MA)**
   - 5-period tick-based moving average
   - Momentum detection on tick crossovers
   - Ultra-fast 3-tick MA for immediate entries

2. **Micro RSI**
   - 3-period RSI for ultra-short-term signals
   - Oversold (<20) triggers BUY
   - Overbought (>80) triggers SELL

3. **Price Action Patterns**
   - Real-time tick movement analysis
   - Volatility filtering (0.3-5.0 pips range)
   - Spread conditions monitoring (0.5-3.0 pips)

### Risk Management

- **Daily loss limit**: $100 maximum daily loss
- **Position loss limit**: $5 maximum per position
- **Equity protection**: 10% equity drawdown protection
- **Trade limits**: Maximum 20,000 daily trades
- **Spread filtering**: Only trades within acceptable spread range

### Performance Tracking

- Real-time P&L monitoring
- Win rate calculation
- Daily and total statistics
- Position tracking and management
- Biggest win/loss recording

## Parameters

### Core Settings
- `InpSymbol`: "XAUUSDm" (Gold Micro symbol)
- `InpMagicNumber`: 20260303
- `InpTradeOnTick`: true (Trade on every tick)

### Scalping Settings
- `InpLotSize`: 0.01 (Fixed lot size)
- `InpTP_Pips`: 1.5 (Take Profit in pips)
- `InpSL_Pips`: 2.0 (Stop Loss in pips)
- `InpMaxPositions`: 50 (Maximum simultaneous positions)
- `InpMinSpread`: 0.5 (Minimum spread required)
- `InpMaxSpread`: 3.0 (Maximum spread allowed)

### Entry Conditions
- `InpUseTickMA`: true (Use Tick Moving Average)
- `InpTickMAPeriod`: 5 (Tick MA period)
- `InpTickThreshold`: 0.1 (Tick movement threshold)
- `InpUseMicroRSI`: true (Use Micro RSI)
- `InpRSI_Period`: 3 (RSI period)
- `InpRSI_Upper`: 80 (RSI upper level)
- `InpRSI_Lower`: 20 (RSI lower level)
- `InpVolatilityMin`: 0.3 (Minimum volatility in pips)
- `InpVolatilityMax`: 5.0 (Maximum volatility in pips)

### Risk Management
- `InpMaxDailyLoss`: 100.0 (Maximum daily loss in $)
- `InpMaxPositionLoss`: 5.0 (Maximum loss per position in $)
- `InpUseEquityProtection`: true (Use equity protection)
- `InpEquityPercent`: 10.0 (Equity protection percentage)
- `InpMaxDailyTrades`: 20000 (Maximum daily trades)
- `InpUseTimeFilter`: false (Use time filter - disabled by default)

## Installation

1. Copy `GOLD_AI_Pro_Hyper_Scalper.mq4` to your MetaTrader 4 `Experts` folder
2. Restart MetaTrader 4 or refresh the Navigator panel
3. Drag the EA onto a chart with the desired symbol (XAUUSDm recommended)
4. Configure parameters as needed
5. Enable auto-trading

## Requirements

- MetaTrader 4 platform
- Low-latency broker connection
- Symbol: XAUUSDm (Gold Micro) or similar low-spread gold instrument
- Minimum account balance: $100 recommended
- VPS hosting recommended for 24/5 operation

## Trading Strategy

The system employs multiple entry mechanisms:

1. **Immediate Entry Mode** (on every tick):
   - Fast 3-tick MA crossover detection
   - 60% probability threshold for entries
   - Captures micro-movements in price

2. **Standard Entry Mode** (timer-based):
   - RSI oversold/overbought signals
   - Tick MA momentum confirmation
   - Random entries to maintain frequency (when below 50% of daily limit)

3. **Exit Strategy**:
   - Automatic TP/SL at predetermined levels
   - Early profit taking at $0.10 (30% chance)
   - Maximum position loss enforcement ($5)
   - Daily loss limit protection ($100)

## Performance Metrics

The system tracks:
- Total and daily trade count
- Win rate percentage
- Total and daily P&L
- Open positions count
- Biggest win/loss
- Real-time spread and volatility

Statistics are displayed on-chart every 5 seconds and logged periodically.

## Warnings

⚠️ **High-Risk Trading System**
- This is an ultra-high-frequency scalping system
- Very tight stop losses can result in rapid losses
- Requires excellent broker execution and low spreads
- High trade frequency may incur significant commission costs
- Not suitable for beginners
- Use at your own risk

⚠️ **Broker Requirements**
- Ultra-low latency connection
- Tight spreads (<3 pips)
- No/low commissions
- Fast execution
- High maximum order count
- VPS recommended

## License

This Expert Advisor is provided for educational and research purposes.

## Disclaimer

Trading involves substantial risk. Past performance is not indicative of future results. Always test on demo accounts before live trading.
