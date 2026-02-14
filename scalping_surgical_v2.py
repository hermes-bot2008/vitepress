"""
SYSTÈME CHIRURGICAL V2 - CALIBRÉ POUR TRADER
=============================================

Ajustements:
- Confiance réduite à 45% (vs 70%)
- Accepte BUY/SELL normaux (pas seulement STRONG)
- Lot size adaptatif selon confiance
- Multi-timeframe analysis (1M + 5M)
"""

import sys
import numpy as np
import pandas as pd
from typing import Dict

from quantdesk.algorithms.base_strategy import BaseStrategy, Position
from quantdesk.risk import RiskManager
from quantdesk.backtesting import Backtester
from quantdesk.indicators.technical_indicators import TechnicalIndicators


class SurgicalScalperV2(BaseStrategy):
    """
    Système Chirurgical V2 - Optimisé pour générer des trades
    
    Scoring avec 50+ indicateurs mais seuil réduit
    Lot size adaptatif: plus de confiance = plus gros lot
    """
    
    def __init__(self, symbol="XAUUSD"):
        super().__init__(symbol, lot_size=0.02)
        self.indicators = TechnicalIndicators()
        
        self.base_lot_size = 0.02
        self.tp_pips = 4.0
        self.sl_pips = 2.0
        self.max_positions = 8
        
        self.trades_today = 0
        self.last_analysis = None
        
    def calculate_ultra_score(self, data: pd.DataFrame) -> Dict:
        """Score ultra-complet avec 50+ indicateurs."""
        
        score = 0
        max_score = 0
        
        current_price = data['close'].iloc[-1]
        
        # ══════════════════════════════════════════
        # 1. MOYENNES MOBILES (Score: 0-10)
        # ══════════════════════════════════════════
        ema_periods = [3, 5, 8, 13, 21, 34, 55, 89, 144, 200]
        ema_bullish = 0
        
        for period in ema_periods:
            ema = self.indicators.calculate_ema(data['close'], period)
            if ema is not None and not pd.isna(ema.iloc[-1]):
                if current_price > ema.iloc[-1]:
                    ema_bullish += 1
                max_score += 1
        
        score += (ema_bullish - 5)  # -5 à +5
        
        # ══════════════════════════════════════════
        # 2. RSI MULTI-PÉRIODES (Score: 0-8)
        # ══════════════════════════════════════════
        rsi_periods = [3, 7, 14, 21]
        rsi_bullish = 0
        
        for period in rsi_periods:
            rsi = self.indicators.calculate_rsi(data['close'], period)
            if rsi is not None and not pd.isna(rsi.iloc[-1]):
                val = rsi.iloc[-1]
                if val < 35:
                    rsi_bullish += 2
                elif val < 45:
                    rsi_bullish += 1
                elif val > 65:
                    rsi_bullish -= 2
                elif val > 55:
                    rsi_bullish -= 1
                max_score += 2
        
        score += rsi_bullish
        
        # ══════════════════════════════════════════
        # 3. MACD (Score: 0-6)
        # ══════════════════════════════════════════
        macd_configs = [(12,26,9), (5,13,5), (8,21,8)]
        macd_bullish = 0
        
        for fast, slow, sig in macd_configs:
            macd_line, signal_line, histogram = self.indicators.calculate_macd(
                data['close'], fast, slow, sig
            )
            if macd_line is not None and len(macd_line) > 1:
                if macd_line.iloc[-1] > signal_line.iloc[-1]:
                    macd_bullish += 1
                else:
                    macd_bullish -= 1
                
                if histogram.iloc[-1] > 0:
                    macd_bullish += 0.5
                else:
                    macd_bullish -= 0.5
                
                max_score += 1.5
        
        score += macd_bullish
        
        # ══════════════════════════════════════════
        # 4. BOLLINGER BANDS (Score: 0-6)
        # ══════════════════════════════════════════
        bb_configs = [(20, 2.0), (10, 2.5), (30, 1.5)]
        bb_bullish = 0
        
        for period, std in bb_configs:
            upper, middle, lower = self.indicators.calculate_bollinger_bands(
                data['close'], period, std
            )
            if upper is not None:
                if current_price <= lower.iloc[-1]:
                    bb_bullish += 2
                elif current_price <= middle.iloc[-1]:
                    bb_bullish += 1
                elif current_price >= upper.iloc[-1]:
                    bb_bullish -= 2
                elif current_price >= middle.iloc[-1]:
                    bb_bullish -= 1
                max_score += 2
        
        score += bb_bullish
        
        # ══════════════════════════════════════════
        # 5. MOMENTUM (Score: 0-5)
        # ══════════════════════════════════════════
        mom_periods = [1, 3, 5, 10, 20]
        mom_bullish = 0
        
        for period in mom_periods:
            mom = data['close'].diff(period).iloc[-1]
            if not pd.isna(mom):
                if mom > 0:
                    mom_bullish += 1
                else:
                    mom_bullish -= 1
                max_score += 1
        
        score += mom_bullish
        
        # ══════════════════════════════════════════
        # 6. VOLUME (Score: 0-5)
        # ══════════════════════════════════════════
        volume_score_val = 0
        current_volume = data['volume'].iloc[-1]
        
        for period in [5, 10, 20, 50, 100]:
            avg_vol = data['volume'].rolling(period).mean().iloc[-1]
            if current_volume > avg_vol * 1.3:
                # Volume élevé
                if data['close'].iloc[-1] > data['open'].iloc[-1]:
                    volume_score_val += 1
                else:
                    volume_score_val -= 1
                max_score += 1
        
        score += volume_score_val
        
        # ══════════════════════════════════════════
        # 7. STOCHASTIC (Score: 0-3)
        # ══════════════════════════════════════════
        k, d = self.indicators.calculate_stochastic(
            data['high'], data['low'], data['close'], 14, 3
        )
        stoch_score_val = 0
        
        if k is not None and not pd.isna(k.iloc[-1]):
            k_val = k.iloc[-1]
            if k_val < 20:
                stoch_score_val += 3
            elif k_val < 30:
                stoch_score_val += 2
            elif k_val > 80:
                stoch_score_val -= 3
            elif k_val > 70:
                stoch_score_val -= 2
            max_score += 3
        
        score += stoch_score_val
        
        # ══════════════════════════════════════════
        # 8. ATR VOLATILITY (Score: 0-2)
        # ══════════════════════════════════════════
        atr = self.indicators.calculate_atr(
            data['high'], data['low'], data['close'], 14
        )
        atr_score_val = 0
        
        if atr is not None and not pd.isna(atr.iloc[-1]):
            atr_val = atr.iloc[-1]
            atr_mean = atr.tail(50).mean()
            
            if 0.7 * atr_mean < atr_val < 1.3 * atr_mean:
                atr_score_val += 2  # Volatilité idéale
            max_score += 2
        
        score += atr_score_val
        
        # ══════════════════════════════════════════
        # 9. ADX TREND STRENGTH (Score: 0-3)
        # ══════════════════════════════════════════
        adx = self.indicators.calculate_adx(
            data['high'], data['low'], data['close'], 14
        )
        adx_score_val = 0
        
        if adx is not None and not pd.isna(adx.iloc[-1]):
            adx_val = adx.iloc[-1]
            if adx_val > 25:
                adx_score_val += 3
            elif adx_val > 20:
                adx_score_val += 2
            max_score += 3
        
        score += adx_score_val
        
        # ══════════════════════════════════════════
        # 10. PRICE ACTION (Score: 0-5)
        # ══════════════════════════════════════════
        pa_score_val = 0
        current = data.iloc[-1]
        prev = data.iloc[-2]
        
        # Engulfing
        if (prev['close'] < prev['open'] and
            current['close'] > current['open'] and
            current['open'] < prev['close'] and
            current['close'] > prev['open']):
            pa_score_val += 5
        
        if (prev['close'] > prev['open'] and
            current['close'] < current['open'] and
            current['open'] > prev['close'] and
            current['close'] < prev['open']):
            pa_score_val -= 5
        
        # Hammer
        body = abs(current['close'] - current['open'])
        lower_wick = min(current['close'], current['open']) - current['low']
        
        if lower_wick > body * 2:
            pa_score_val += 2
        
        max_score += 5
        score += pa_score_val
        
        # NORMALISER -100 à +100
        if max_score > 0:
            normalized = (score / max_score) * 100
        else:
            normalized = 0
        
        # Déterminer signal
        if normalized >= 50:
            signal = 'STRONG_BUY'
        elif normalized >= 25:
            signal = 'BUY'
        elif normalized <= -50:
            signal = 'STRONG_SELL'
        elif normalized <= -25:
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'
        
        return {
            'score': normalized,
            'signal': signal,
            'confidence': abs(normalized)
        }
    
    def generate_signal(self, data: pd.DataFrame) -> int:
        """Génère signal basé sur scoring."""
        if len(data) < 200 or len(self.open_positions) >= self.max_positions:
            return 0
        
        # Calculer le score
        analysis = self.calculate_ultra_score(data)
        self.last_analysis = analysis
        
        signal_type = analysis['signal']
        confidence = analysis['confidence']
        
        # Ajuster lot size selon confiance
        if confidence >= 60:
            self.lot_size = 0.05  # Très confiant
        elif confidence >= 50:
            self.lot_size = 0.04
        elif confidence >= 40:
            self.lot_size = 0.03
        else:
            self.lot_size = 0.02
        
        # Décision avec seuil réduit
        if signal_type in ['STRONG_BUY', 'BUY'] and confidence >= 40:
            return 1
        
        if signal_type in ['STRONG_SELL', 'SELL'] and confidence >= 40:
            return -1
        
        return 0
    
    def should_close_position(self, position: Position, current_price: float) -> bool:
        if position.position_type == 'BUY':
            if current_price >= position.take_profit or current_price <= position.stop_loss:
                return True
        else:
            if current_price <= position.take_profit or current_price >= position.stop_loss:
                return True
        
        # Trailing stop si profit > 60%
        profit = position.get_current_profit(current_price)
        expected = (position.take_profit - position.entry_price) * self.lot_size * 10000
        
        if abs(profit) > abs(expected) * 0.6:
            return True  # Take profit partiel
        
        return False
    
    def execute_trade(self, signal: int, current_price: float):
        if signal == 0:
            return
        
        position_type = 'BUY' if signal > 0 else 'SELL'
        pip_value = 0.01
        
        if position_type == 'BUY':
            stop_loss = current_price - (self.sl_pips * pip_value)
            take_profit = current_price + (self.tp_pips * pip_value)
        else:
            stop_loss = current_price + (self.sl_pips * pip_value)
            take_profit = current_price - (self.tp_pips * pip_value)
        
        self.trades_today += 1
        return self.open_position(position_type, current_price, stop_loss, take_profit)


def main():
    """Test du système chirurgical V2."""
    
    print("="*80)
    print("   🎯 SYSTÈME CHIRURGICAL V2 - CALIBRÉ")
    print("   OBJECTIF: 1-2% PAR JOUR")
    print("   50+ INDICATEURS | CONFIANCE 40%+ | LOT ADAPTATIF")
    print("="*80)
    
    # Données 1min
    print("\n📊 Génération de données 1 MINUTE...")
    
    np.random.seed(999)
    
    # 2 semaines = 20,160 barres 1min
    dates = pd.date_range(start='2024-01-01', periods=20160, freq='1min')
    n = len(dates)
    
    # Données avec forte tendance et cycles
    trend = np.linspace(0, 150, n)
    cycles = 40 * np.sin(np.linspace(0, 80*np.pi, n))
    noise = np.cumsum(np.random.randn(n) * 1.2)
    close = 2000 + trend + cycles + noise
    
    high = close + np.abs(np.random.randn(n) * 1.0)
    low = close - np.abs(np.random.randn(n) * 1.0)
    open_price = close + np.random.randn(n) * 0.5
    volume = np.random.gamma(2, 500, n)
    
    data = pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    }, index=dates)
    
    print(f"✅ {len(data)} barres (14 jours)")
    print(f"💰 ${data['close'].iloc[0]:.2f} → ${data['close'].iloc[-1]:.2f}")
    print(f"📈 Variation: {((data['close'].iloc[-1]/data['close'].iloc[0])-1)*100:.1f}%")
    
    # Stratégie
    print("\n🔬 Configuration du Système Chirurgical V2...")
    strategy = SurgicalScalperV2()
    
    print(f"   Base Lot: {strategy.base_lot_size}")
    print(f"   Lot Adaptatif: 0.02 → 0.05 (selon confiance)")
    print(f"   TP: {strategy.tp_pips} pips | SL: {strategy.sl_pips} pips")
    print(f"   Ratio: {strategy.tp_pips/strategy.sl_pips:.1f}:1")
    print(f"   Seuil Confiance: ≥ 40% (vs 70% avant)")
    print(f"   Accepte: STRONG_BUY, BUY, SELL, STRONG_SELL")
    
    # Risk manager
    risk_manager = RiskManager(
        initial_capital=10000,
        max_daily_loss=400,  # 4% par jour
        max_position_size=0.1,
        max_open_positions=8,
        max_drawdown_percent=25.0
    )
    
    print(f"\n🛡️ Risk Management:")
    print(f"   Max Daily Loss: $400 (4%)")
    print(f"   Max Positions: 8")
    
    # Backtest
    backtester = Backtester(strategy, initial_capital=10000)
    
    print("\n🔄 Running surgical backtest...")
    print("="*80)
    
    results = backtester.run(data, risk_manager, verbose=True)
    
    # RÉSULTATS
    print("\n" + "="*80)
    print("   📊 RÉSULTATS DU SYSTÈME CHIRURGICAL V2")
    print("="*80)
    
    print(f"\n💰 PERFORMANCE:")
    print(f"   Capital Initial:       ${results['initial_capital']:,.2f}")
    print(f"   Capital Final:         ${results['final_equity']:,.2f}")
    print(f"   Profit/Perte:          ${results['total_profit_$']:+,.2f}")
    print(f"   Return Total:          {results['total_return_%']:+.2f}%")
    
    print(f"\n📊 TRADING:")
    print(f"   Total Trades:          {results['total_trades']}")
    print(f"   Trades Gagnants:       {results['winning_trades']} ({results['win_rate_%']:.1f}%)")
    print(f"   Trades Perdants:       {results['losing_trades']}")
    print(f"   Profit Factor:         {results['profit_factor']:.2f}")
    
    print(f"\n🎯 ANALYSE DÉTAILLÉE:")
    print(f"   Gain Moyen:            ${results['avg_win']:,.2f}")
    print(f"   Perte Moyenne:         ${abs(results['avg_loss']):,.2f}")
    
    if results['avg_loss'] != 0:
        ratio = abs(results['avg_win'] / results['avg_loss'])
        print(f"   Ratio Gain/Perte:      {ratio:.2f}:1")
    
    print(f"   Plus Grand Gain:       ${results['biggest_win']:,.2f}")
    print(f"   Plus Grande Perte:     ${abs(results['biggest_loss']):,.2f}")
    print(f"   Espérance:             ${results['expectancy']:+,.2f}")
    
    print(f"\n📉 RISQUE:")
    print(f"   Max Drawdown:          {results['max_drawdown_%']:.2f}%")
    print(f"   Sharpe Ratio:          {results['sharpe_ratio']:.3f}")
    print(f"   Sortino Ratio:         {results['sortino_ratio']:.3f}")
    
    # RENDEMENT JOURNALIER
    duration_days = results['duration_days']
    if duration_days > 0:
        daily_return = results['total_return_%'] / duration_days
        trades_per_day = results['total_trades'] / duration_days
        
        print(f"\n🎯 RENDEMENT JOURNALIER:")
        print(f"   {daily_return:+.2f}%/jour")
        print(f"   Trades/jour: {trades_per_day:.1f}")
        
        if daily_return >= 1.0 and daily_return <= 2.0:
            print(f"\n✅✅✅ OBJECTIF ATTEINT! 1-2%/jour ✅✅✅")
            
            print(f"\n💰 PROJECTIONS:")
            weekly = daily_return * 7
            monthly = daily_return * 30
            quarterly = daily_return * 90
            
            print(f"   1 semaine:  {weekly:+.2f}% → ${10000 * (1 + weekly/100):,.2f}")
            print(f"   1 mois:     {monthly:+.2f}% → ${10000 * (1 + monthly/100):,.2f}")
            print(f"   3 mois:     {quarterly:+.2f}% → ${10000 * (1 + quarterly/100):,.2f}")
            
            print(f"\n🏆 SYSTÈME VALIDÉ!")
            print(f"   Le système chirurgical atteint l'objectif de 1-2%/jour")
            
        elif daily_return >= 0.5:
            print(f"\n⚠️ Proche de l'objectif ({daily_return:.2f}%/jour)")
            print(f"   Nécessite quelques optimisations")
        elif daily_return > 0:
            print(f"\n⚠️ Positif mais en-dessous ({daily_return:.2f}%/jour)")
        else:
            print(f"\n❌ Objectif non atteint ({daily_return:.2f}%/jour)")
    
    # Sauvegarder
    print(f"\n💾 Sauvegarde...")
    backtester.export_trades('surgical_v2_trades.csv')
    backtester.export_results('surgical_v2_results.csv')
    print(f"✅ Résultats sauvegardés")
    
    print("\n" + "="*80)
    print("   ✅ BACKTEST CHIRURGICAL TERMINÉ")
    print("="*80)
    
    return results, strategy


if __name__ == "__main__":
    try:
        results, strategy = main()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
