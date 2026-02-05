//+------------------------------------------------------------------+
//|                                               GOLD_AI_Pro_Hyper_Scalper.mq4 |
//|                 Ultra High Frequency Scalping System 20K/day     |
//+------------------------------------------------------------------+
#property copyright "GOLD AI Pro - Hyper Scalper"
#property link      ""
#property version   "1.0"
#property strict

//+------------------------------------------------------------------+
//| PARAMÈTRES ULTRA FRÉQUENTS                                      |
//+------------------------------------------------------------------+
extern string   __Core__ = "=== CORE SETTINGS ===";
extern string   InpSymbol        = "XAUUSDm";      // Gold Micro
extern int      InpMagicNumber   = 20260303;       // Magic Number
extern bool     InpTradeOnTick   = true;           // Trade on every tick

extern string   __Scalping__ = "=== HYPER SCALPING ===";
extern double   InpLotSize       = 0.01;           // Lot size fixe
extern double   InpTP_Pips       = 1.5;            // Take Profit (1.5 pips)
extern double   InpSL_Pips       = 2.0;            // Stop Loss (2.0 pips)
extern int      InpMaxPositions  = 50;             // Positions simultanées max
extern double   InpMinSpread     = 0.5;            // Spread minimum requis
extern double   InpMaxSpread     = 3.0;            // Spread maximum autorisé

extern string   __Entry_Conditions__ = "=== ENTRY CONDITIONS ===";
extern bool     InpUseTickMA     = true;           // Use Tick Moving Average
extern int      InpTickMAPeriod  = 5;              // Tick MA Period
extern double   InpTickThreshold = 0.1;            // Tick movement threshold
extern bool     InpUseMicroRSI   = true;           // Use Micro RSI
extern int      InpRSI_Period    = 3;              // RSI Period ultra-court
extern int      InpRSI_Upper     = 80;             // RSI Upper level
extern int      InpRSI_Lower     = 20;             // RSI Lower level
extern bool     InpUsePriceAction= true;           // Use Price Action patterns
extern double   InpVolatilityMin = 0.3;            // Min volatility (pips)
extern double   InpVolatilityMax = 5.0;            // Max volatility (pips)

extern string   __Risk_Management__ = "=== RISK MANAGEMENT ===";
extern double   InpMaxDailyLoss  = 100.0;          // Max daily loss ($)
extern double   InpMaxPositionLoss = 5.0;          // Max loss per position ($)
extern bool     InpUseEquityProtection = true;     // Use equity protection
extern double   InpEquityPercent = 10.0;           // Equity protection %
extern int      InpMaxDailyTrades = 20000;         // Max daily trades (20K)
extern bool     InpUseTimeFilter = false;          // Use time filter (off)

//+------------------------------------------------------------------+
//| STRUCTURES                                                       |
//+------------------------------------------------------------------+
struct TickData {
    double bid;
    double ask;
    datetime time;
    double spread;
};

struct PositionInfo {
    int ticket;
    double entryPrice;
    int type;
    datetime openTime;
    double stopLoss;
    double takeProfit;
    double currentProfit;
};

//+------------------------------------------------------------------+
//| VARIABLES GLOBALES                                               |
//+------------------------------------------------------------------+
// Tick tracking
TickData g_lastTicks[100];
int g_tickIndex = 0;
double g_lastBid = 0;
double g_lastAsk = 0;
double g_tickMA = 0;

// Position tracking
PositionInfo g_positions[];
int g_positionCount = 0;
int g_dailyTrades = 0;
double g_dailyProfit = 0;
datetime g_lastTradeDay = 0;
int g_totalTrades = 0;
double g_totalProfit = 0;

// Performance metrics
int g_winningTrades = 0;
int g_losingTrades = 0;
double g_biggestWin = 0;
double g_biggestLoss = 0;

// Risk management
double g_maxEquity = 0;
double g_minEquity = 0;
bool g_tradingEnabled = true;

// Timing
datetime g_lastTradeTime = 0;
int g_tradesThisSecond = 0;
datetime g_currentSecond = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("=== GOLD AI PRO HYPER SCALPER ===");
   Print("Version: Ultra High Frequency - 20K trades/day");
   Print("Symbol: ", InpSymbol);
   
   // Initialize symbol info
   int digits = (int)MarketInfo(InpSymbol, MODE_DIGITS);
   double point = MarketInfo(InpSymbol, MODE_POINT);
   double spread = MarketInfo(InpSymbol, MODE_SPREAD) * point;
   
   Print("Digits: ", digits);
   Print("Point: ", point);
   Print("Current Spread: ", spread);
   Print("Account Balance: $", AccountBalance());
   Print("Account Equity: $", AccountEquity());
   
   // Initialize arrays
   ArrayResize(g_positions, 0);
   ArrayInitialize(g_lastTicks, 0);
   
   // Initialize performance metrics
   g_winningTrades = 0;
   g_losingTrades = 0;
   g_biggestWin = 0;
   g_biggestLoss = 0;
   
   // Initialize risk management
   g_maxEquity = AccountEquity();
   g_minEquity = AccountEquity() * (1 - InpEquityPercent/100);
   
   // Initialize day tracking
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   dt.hour = 0; dt.min = 0; dt.sec = 0;
   g_lastTradeDay = StructToTime(dt);
   
   // Set timer for 1ms for ultra-fast processing
   EventSetMillisecondTimer(1);
   
   Print("=== SYSTEM INITIALIZED ===");
   Print("Maximum Daily Trades: ", InpMaxDailyTrades);
   Print("Maximum Positions: ", InpMaxPositions);
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   
   Print("=== SYSTEM DEINITIALIZED ===");
   Print("Total Trades: ", g_totalTrades);
   Print("Daily Trades: ", g_dailyTrades);
   Print("Total Profit: $", g_totalProfit);
   
   // Calculate win rate
   double winRate = 0;
   if(g_totalTrades > 0) {
      winRate = (double)g_winningTrades / g_totalTrades * 100;
      Print("Win Rate: ", DoubleToString(winRate, 1), "%");
   } else {
      Print("Win Rate: 0%");
   }
   
   Print("Winning Trades: ", g_winningTrades);
   Print("Losing Trades: ", g_losingTrades);
   Print("Biggest Win: $", g_biggestWin);
   Print("Biggest Loss: $", g_biggestLoss);
}

//+------------------------------------------------------------------+
//| MILLISECOND TIMER                                                |
//+------------------------------------------------------------------+
void OnTimer()
{
   // Check for new day
   CheckNewDay();
   
   ProcessTick();
   ManageOpenPositions();
   CheckRiskLimits();
   UpdateTickMA();
   CheckEntryConditions();
   CleanClosedPositions();
   
   // Update stats every 100ms
   static int timerCount = 0;
   timerCount++;
   if(timerCount % 100 == 0) {
      UpdateStats();
   }
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   if(!InpTradeOnTick) return;
   
   ProcessTick();
   
   // Quick entry on every tick (if enabled)
   if(CanOpenNewPosition()) {
      CheckImmediateEntry();
   }
}

//+------------------------------------------------------------------+
//| PROCESS TICK DATA                                                |
//+------------------------------------------------------------------+
void ProcessTick()
{
   double currentBid = MarketInfo(InpSymbol, MODE_BID);
   double currentAsk = MarketInfo(InpSymbol, MODE_ASK);
   double currentSpread = (currentAsk - currentBid) / MarketInfo(InpSymbol, MODE_POINT);
   
   // Store tick data
   g_lastTicks[g_tickIndex].bid = currentBid;
   g_lastTicks[g_tickIndex].ask = currentAsk;
   g_lastTicks[g_tickIndex].time = TimeCurrent();
   g_lastTicks[g_tickIndex].spread = currentSpread;
   
   g_tickIndex = (g_tickIndex + 1) % 100;
   
   // Check for significant tick movement
   if(g_lastBid > 0 && g_lastAsk > 0) {
      double bidMovement = MathAbs(currentBid - g_lastBid) / MarketInfo(InpSymbol, MODE_POINT);
      double askMovement = MathAbs(currentAsk - g_lastAsk) / MarketInfo(InpSymbol, MODE_POINT);
      
      // Update last prices
      g_lastBid = currentBid;
      g_lastAsk = currentAsk;
   } else {
      g_lastBid = currentBid;
      g_lastAsk = currentAsk;
   }
}

//+------------------------------------------------------------------+
//| UPDATE TICK MOVING AVERAGE                                       |
//+------------------------------------------------------------------+
void UpdateTickMA()
{
   if(g_tickIndex < InpTickMAPeriod) return;
   
   double sum = 0;
   int count = 0;
   
   for(int i = 0; i < InpTickMAPeriod; i++) {
      int index = (g_tickIndex - i - 1 + 100) % 100;
      if(g_lastTicks[index].bid > 0) {
         sum += g_lastTicks[index].bid;
         count++;
      }
   }
   
   if(count > 0) {
      g_tickMA = sum / count;
   }
}

//+------------------------------------------------------------------+
//| CHECK ENTRY CONDITIONS                                           |
//+------------------------------------------------------------------+
void CheckEntryConditions()
{
   if(!CanOpenNewPosition()) return;
   if(!CheckSpreadConditions()) return;
   
   // Check time filter (if enabled)
   if(InpUseTimeFilter) {
      if(!IsTradingTime()) return;
   }
   
   // Check volatility
   double volatility = CalculateVolatility();
   if(volatility < InpVolatilityMin || volatility > InpVolatilityMax) return;
   
   // Check equity protection
   if(InpUseEquityProtection) {
      if(AccountEquity() < g_minEquity) {
         g_tradingEnabled = false;
         return;
      }
   }
   
   // Generate entry signal
   int signal = GenerateEntrySignal();
   
   if(signal != 0) {
      OpenPosition(signal);
   }
}

//+------------------------------------------------------------------+
//| CHECK IMMEDIATE ENTRY                                            |
//+------------------------------------------------------------------+
void CheckImmediateEntry()
{
   if(!CanOpenNewPosition()) return;
   
   // Ultra-fast entry based on pure tick movement
   static double lastFastMA = 0;
   double currentBid = MarketInfo(InpSymbol, MODE_BID);
   
   if(lastFastMA == 0) lastFastMA = currentBid;
   
   // Very fast MA (3-tick)
   double fastMA = 0;
   int tickCount = 0;
   for(int i = 0; i < 3; i++) {
      int index = (g_tickIndex - i - 1 + 100) % 100;
      if(g_lastTicks[index].bid > 0) {
         fastMA += g_lastTicks[index].bid;
         tickCount++;
      }
   }
   if(tickCount > 0) fastMA /= tickCount;
   
   // Entry on tick MA crossover
   if(fastMA > lastFastMA && g_lastBid > fastMA) {
      // Bullish momentum
      if(MathRand() % 100 < 60) { // 60% probability
         OpenPosition(1);
      }
   } else if(fastMA < lastFastMA && g_lastBid < fastMA) {
      // Bearish momentum
      if(MathRand() % 100 < 60) { // 60% probability
         OpenPosition(-1);
      }
   }
   
   lastFastMA = fastMA;
}

//+------------------------------------------------------------------+
//| GENERATE ENTRY SIGNAL                                            |
//+------------------------------------------------------------------+
int GenerateEntrySignal()
{
   int signal = 0;
   double currentBid = MarketInfo(InpSymbol, MODE_BID);
   double currentAsk = MarketInfo(InpSymbol, MODE_ASK);
   
   // 1. Micro RSI signal
   if(InpUseMicroRSI) {
      double rsi = iRSI(InpSymbol, PERIOD_M1, InpRSI_Period, PRICE_CLOSE, 0);
      if(rsi < InpRSI_Lower) {
         signal = 1; // Oversold -> BUY
      } else if(rsi > InpRSI_Upper) {
         signal = -1; // Overbought -> SELL
      }
   }
   
   // 2. Tick MA momentum
   if(InpUseTickMA && g_tickMA > 0) {
      if(currentBid > g_tickMA * (1 + InpTickThreshold/10000)) {
         if(signal == 0) signal = 1;
      } else if(currentBid < g_tickMA * (1 - InpTickThreshold/10000)) {
         if(signal == 0) signal = -1;
      }
   }
   
   // 3. Random entry if no signal (for high frequency)
   if(signal == 0 && g_dailyTrades < InpMaxDailyTrades/2) {
      // Random entry to maintain trade frequency
      if(MathRand() % 1000 < 5) { // 0.5% chance per check
         signal = (MathRand() % 2 == 0) ? 1 : -1;
      }
   }
   
   return signal;
}

//+------------------------------------------------------------------+
//| OPEN POSITION                                                    |
//+------------------------------------------------------------------+
void OpenPosition(int direction)
{
   // Check rate limiting (max 5 trades per second)
   datetime now = TimeCurrent();
   if(now == g_currentSecond) {
      g_tradesThisSecond++;
      if(g_tradesThisSecond > 5) return;
   } else {
      g_currentSecond = now;
      g_tradesThisSecond = 1;
   }
   
   double lotSize = InpLotSize;
   double tpPoints = InpTP_Pips * MarketInfo(InpSymbol, MODE_POINT);
   double slPoints = InpSL_Pips * MarketInfo(InpSymbol, MODE_POINT);
   
   double price, sl, tp;
   color arrowColor;
   
   RefreshRates();
   
   if(direction > 0) {
      price = MarketInfo(InpSymbol, MODE_ASK);
      sl = NormalizeDouble(price - slPoints, (int)MarketInfo(InpSymbol, MODE_DIGITS));
      tp = NormalizeDouble(price + tpPoints, (int)MarketInfo(InpSymbol, MODE_DIGITS));
      arrowColor = clrGreen;
   } else {
      price = MarketInfo(InpSymbol, MODE_BID);
      sl = NormalizeDouble(price + slPoints, (int)MarketInfo(InpSymbol, MODE_DIGITS));
      tp = NormalizeDouble(price - tpPoints, (int)MarketInfo(InpSymbol, MODE_DIGITS));
      arrowColor = clrRed;
   }
   
   // Check stop level
   double stopLevel = MarketInfo(InpSymbol, MODE_STOPLEVEL) * MarketInfo(InpSymbol, MODE_POINT);
   if(MathAbs(price - sl) < stopLevel) {
      sl = (direction > 0) ? price - stopLevel : price + stopLevel;
   }
   if(MathAbs(price - tp) < stopLevel) {
      tp = (direction > 0) ? price + stopLevel : price - stopLevel;
   }
   
   string comment = StringFormat("HFS_%d_%d", g_dailyTrades+1, direction>0?1:0);
   
   int ticket = OrderSend(InpSymbol, direction>0?OP_BUY:OP_SELL, lotSize, 
                         price, 30, sl, tp, comment, InpMagicNumber, 0, arrowColor);
   
   if(ticket > 0) {
      // Record position
      int idx = g_positionCount;
      g_positionCount++;
      ArrayResize(g_positions, g_positionCount);
      
      g_positions[idx].ticket = ticket;
      g_positions[idx].entryPrice = price;
      g_positions[idx].type = direction>0?OP_BUY:OP_SELL;
      g_positions[idx].openTime = TimeCurrent();
      g_positions[idx].stopLoss = sl;
      g_positions[idx].takeProfit = tp;
      g_positions[idx].currentProfit = 0;
      
      g_totalTrades++;
      g_dailyTrades++;
      g_lastTradeTime = TimeCurrent();
      
      // Log trade
      if(g_totalTrades % 100 == 0) {
         Print("Trade #", g_totalTrades, " opened - Daily: ", g_dailyTrades);
      }
   } else {
      Print("OrderSend failed with error: ", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| MANAGE OPEN POSITIONS                                            |
//+------------------------------------------------------------------+
void ManageOpenPositions()
{
   double currentBid = MarketInfo(InpSymbol, MODE_BID);
   double currentAsk = MarketInfo(InpSymbol, MODE_ASK);
   
   for(int i = 0; i < g_positionCount; i++) {
      if(g_positions[i].ticket <= 0) continue;
      
      if(OrderSelect(g_positions[i].ticket, SELECT_BY_TICKET)) {
         double profit = OrderProfit() + OrderCommission();
         g_positions[i].currentProfit = profit;
         
         // Check max loss per position
         if(profit <= -InpMaxPositionLoss) {
            ClosePosition(g_positions[i].ticket);
            continue;
         }
         
         // Check if position is at TP or SL
         if(OrderType() == OP_BUY) {
            if(currentBid >= OrderTakeProfit() || currentBid <= OrderStopLoss()) {
               ClosePosition(g_positions[i].ticket);
            }
         } else if(OrderType() == OP_SELL) {
            if(currentAsk <= OrderTakeProfit() || currentAsk >= OrderStopLoss()) {
               ClosePosition(g_positions[i].ticket);
            }
         }
         
         // Quick close on small profit (scalping)
         if(profit >= 0.10) { // Close at +$0.10
            if(MathRand() % 100 < 30) { // 30% chance to close early
               ClosePosition(g_positions[i].ticket);
            }
         }
      }
   }
}

//+------------------------------------------------------------------+
//| CLOSE POSITION                                                   |
//+------------------------------------------------------------------+
void ClosePosition(int ticket)
{
   if(OrderSelect(ticket, SELECT_BY_TICKET)) {
      double closePrice;
      if(OrderType() == OP_BUY) {
         closePrice = MarketInfo(InpSymbol, MODE_BID);
      } else {
         closePrice = MarketInfo(InpSymbol, MODE_ASK);
      }
      
      if(OrderClose(ticket, OrderLots(), closePrice, 30, clrGray)) {
         double profit = OrderProfit() + OrderCommission();
         g_dailyProfit += profit;
         g_totalProfit += profit;
         
         if(profit > 0) {
            g_winningTrades++;
            if(profit > g_biggestWin) g_biggestWin = profit;
         } else {
            g_losingTrades++;
            if(profit < g_biggestLoss) g_biggestLoss = profit;
         }
      } else {
         Print("OrderClose failed with error: ", GetLastError());
      }
   }
}

//+------------------------------------------------------------------+
//| CLEAN CLOSED POSITIONS                                           |
//+------------------------------------------------------------------+
void CleanClosedPositions()
{
   // Remove closed positions from array
   int newCount = 0;
   PositionInfo tempArray[];
   ArrayResize(tempArray, g_positionCount);
   
   for(int i = 0; i < g_positionCount; i++) {
      if(g_positions[i].ticket > 0) {
         if(OrderSelect(g_positions[i].ticket, SELECT_BY_TICKET)) {
            if(OrderCloseTime() == 0) {
               // Position still open
               tempArray[newCount] = g_positions[i];
               newCount++;
            }
         }
      }
   }
   
   // Update array
   ArrayResize(g_positions, newCount);
   for(int i = 0; i < newCount; i++) {
      g_positions[i] = tempArray[i];
   }
   g_positionCount = newCount;
}

//+------------------------------------------------------------------+
//| CAN OPEN NEW POSITION                                            |
//+------------------------------------------------------------------+
bool CanOpenNewPosition()
{
   if(!g_tradingEnabled) return false;
   if(g_dailyTrades >= InpMaxDailyTrades) return false;
   if(g_positionCount >= InpMaxPositions) return false;
   if(g_dailyProfit <= -InpMaxDailyLoss) return false;
   
   // Check minimum time between trades (10ms)
   datetime currentTime = TimeCurrent();
   if(currentTime - g_lastTradeTime < 0.01) return false;
   
   return true;
}

//+------------------------------------------------------------------+
//| CHECK SPREAD CONDITIONS                                          |
//+------------------------------------------------------------------+
bool CheckSpreadConditions()
{
   double currentSpread = MarketInfo(InpSymbol, MODE_SPREAD) * MarketInfo(InpSymbol, MODE_POINT);
   double normalizedSpread = currentSpread / MarketInfo(InpSymbol, MODE_POINT);
   
   if(normalizedSpread < InpMinSpread) return false;
   if(normalizedSpread > InpMaxSpread) return false;
   
   return true;
}

//+------------------------------------------------------------------+
//| CALCULATE VOLATILITY                                             |
//+------------------------------------------------------------------+
double CalculateVolatility()
{
   if(g_tickIndex < 10) return 0;
   
   double high = 0;
   double low = 1000000;
   
   for(int i = 0; i < 10; i++) {
      int index = (g_tickIndex - i - 1 + 100) % 100;
      if(g_lastTicks[index].bid > 0) {
         if(g_lastTicks[index].bid > high) high = g_lastTicks[index].bid;
         if(g_lastTicks[index].bid < low) low = g_lastTicks[index].bid;
      }
   }
   
   if(low < 1000000 && high > 0) {
      return (high - low) / MarketInfo(InpSymbol, MODE_POINT);
   }
   
   return 0;
}

//+------------------------------------------------------------------+
//| CHECK RISK LIMITS                                                |
//+------------------------------------------------------------------+
void CheckRiskLimits()
{
   // Check daily loss limit
   if(g_dailyProfit <= -InpMaxDailyLoss) {
      if(g_tradingEnabled) {
         Print("Daily loss limit reached: $", g_dailyProfit);
         g_tradingEnabled = false;
         CloseAllPositions();
      }
      return;
   }
   
   // Check daily trade limit
   if(g_dailyTrades >= InpMaxDailyTrades) {
      if(g_tradingEnabled) {
         Print("Daily trade limit reached: ", g_dailyTrades);
         g_tradingEnabled = false;
      }
      return;
   }
   
   // Update equity protection
   if(InpUseEquityProtection) {
      double currentEquity = AccountEquity();
      if(currentEquity > g_maxEquity) g_maxEquity = currentEquity;
      g_minEquity = g_maxEquity * (1 - InpEquityPercent/100);
   }
}

//+------------------------------------------------------------------+
//| CLOSE ALL POSITIONS                                              |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
   for(int i = OrdersTotal()-1; i >= 0; i--) {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) {
         if(OrderSymbol() == InpSymbol && OrderMagicNumber() == InpMagicNumber) {
            ClosePosition(OrderTicket());
         }
      }
   }
}

//+------------------------------------------------------------------+
//| IS TRADING TIME                                                  |
//+------------------------------------------------------------------+
bool IsTradingTime()
{
   // Always true if time filter disabled
   if(!InpUseTimeFilter) return true;
   
   // Trading 24/5
   int dayOfWeek = TimeDayOfWeek(TimeCurrent());
   if(dayOfWeek == 0 || dayOfWeek == 6) return false; // No trading on weekends
   
   return true;
}

//+------------------------------------------------------------------+
//| UPDATE STATS                                                     |
//+------------------------------------------------------------------+
void UpdateStats()
{
   static datetime lastDisplay = 0;
   if(TimeCurrent() - lastDisplay >= 5) {
      DisplayStats();
      lastDisplay = TimeCurrent();
   }
}

//+------------------------------------------------------------------+
//| DISPLAY STATS                                                    |
//+------------------------------------------------------------------+
void DisplayStats()
{
   string stats = "\n=== GOLD AI PRO HYPER SCALPER ===";
   stats += "\nSymbol: " + InpSymbol;
   stats += "\nTime: " + TimeToString(TimeCurrent());
   stats += "\nPrice: " + DoubleToString(MarketInfo(InpSymbol, MODE_BID), 2);
   stats += "\n---";
   stats += "\nTotal Trades: " + IntegerToString(g_totalTrades);
   stats += "\nDaily Trades: " + IntegerToString(g_dailyTrades) + " / " + IntegerToString(InpMaxDailyTrades);
   stats += "\nOpen Positions: " + IntegerToString(g_positionCount) + " / " + IntegerToString(InpMaxPositions);
   stats += "\nDaily P&L: $" + DoubleToString(g_dailyProfit, 2);
   stats += "\nTotal P&L: $" + DoubleToString(g_totalProfit, 2);
   
   double winRate = 0;
   if(g_totalTrades > 0) {
      winRate = (double)g_winningTrades / g_totalTrades * 100;
   }
   stats += "\nWin Rate: " + DoubleToString(winRate, 1) + "%";
   
   stats += "\n---";
   stats += "\nTrading: " + (g_tradingEnabled?"ENABLED":"DISABLED");
   stats += "\nSpread: " + DoubleToString(MarketInfo(InpSymbol, MODE_SPREAD) * MarketInfo(InpSymbol, MODE_POINT), 2);
   stats += "\nTick MA: " + DoubleToString(g_tickMA, 2);
   
   Comment(stats);
}

//+------------------------------------------------------------------+
//| CHECK NEW DAY                                                    |
//+------------------------------------------------------------------+
void CheckNewDay()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   dt.hour = 0; dt.min = 0; dt.sec = 0;
   datetime today = StructToTime(dt);
   
   if(today != g_lastTradeDay) {
      Print("=== NEW TRADING DAY ===");
      Print("Previous Day - Trades: ", g_dailyTrades, " Profit: $", g_dailyProfit);
      
      g_lastTradeDay = today;
      g_dailyTrades = 0;
      g_dailyProfit = 0;
      g_tradingEnabled = true;
      g_maxEquity = AccountEquity();
      g_minEquity = AccountEquity() * (1 - InpEquityPercent/100);
   }
}

//+------------------------------------------------------------------+
//| CHART EVENT                                                      |
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
   if(id == CHARTEVENT_CLICK) {
      DisplayStats();
   }
}

//+------------------------------------------------------------------+
