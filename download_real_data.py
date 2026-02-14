"""
Téléchargement de Données Réelles
==================================

Télécharge les données de marché réelles depuis Yahoo Finance.
"""

import sys

try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'yfinance', '--quiet'])
    import yfinance as yf

import pandas as pd
from datetime import datetime, timedelta


def download_market_data():
    """Télécharge les données réelles."""
    
    print("="*80)
    print("   📥 TÉLÉCHARGEMENT DE DONNÉES RÉELLES")
    print("="*80)
    
    symbols = {
        'GC=F': 'GOLD',      # Gold Futures
        'EURUSD=X': 'EURUSD',  # EUR/USD
        'GBPUSD=X': 'GBPUSD'   # GBP/USD
    }
    
    for yahoo_symbol, name in symbols.items():
        print(f"\n📊 Téléchargement: {name}...")
        print("-"*80)
        
        try:
            ticker = yf.Ticker(yahoo_symbol)
            
            # 1H data (2 ans)
            print(f"   1H data (2 ans)...", end=" ")
            try:
                data_1h = ticker.history(period="2y", interval="1h")
                if not data_1h.empty:
                    data_1h.to_csv(f'data/{name}_1h.csv')
                    print(f"✅ {len(data_1h)} barres")
                else:
                    print("⚠️ Vide")
            except Exception as e:
                print(f"❌ {e}")
            
            # 15M data (60 jours)
            print(f"   15M data (60 jours)...", end=" ")
            try:
                data_15m = ticker.history(period="60d", interval="15m")
                if not data_15m.empty:
                    data_15m.to_csv(f'data/{name}_15m.csv')
                    print(f"✅ {len(data_15m)} barres")
                else:
                    print("⚠️ Vide")
            except Exception as e:
                print(f"❌ {e}")
            
            # 5M data (60 jours)
            print(f"   5M data (60 jours)...", end=" ")
            try:
                data_5m = ticker.history(period="60d", interval="5m")
                if not data_5m.empty:
                    data_5m.to_csv(f'data/{name}_5m.csv')
                    print(f"✅ {len(data_5m)} barres")
                else:
                    print("⚠️ Vide")
            except Exception as e:
                print(f"❌ {e}")
            
            # 1M data (7 jours max sur Yahoo)
            print(f"   1M data (7 jours)...", end=" ")
            try:
                data_1m = ticker.history(period="7d", interval="1m")
                if not data_1m.empty:
                    data_1m.to_csv(f'data/{name}_1m.csv')
                    print(f"✅ {len(data_1m)} barres")
                else:
                    print("⚠️ Vide")
            except Exception as e:
                print(f"❌ {e}")
            
            print(f"✅ {name} téléchargé avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur pour {name}: {e}")
    
    print("\n" + "="*80)
    print("   ✅ TÉLÉCHARGEMENT TERMINÉ")
    print("="*80)
    
    # Lister les fichiers
    import os
    print("\n📁 Fichiers créés:")
    data_dir = 'data/'
    if os.path.exists(data_dir):
        files = os.listdir(data_dir)
        for f in sorted(files):
            filepath = os.path.join(data_dir, f)
            size = os.path.getsize(filepath) / 1024  # KB
            print(f"   ✅ {f:<25} ({size:.1f} KB)")
    
    print("\n💡 Utilisation:")
    print("   import pandas as pd")
    print("   data = pd.read_csv('data/GOLD_5m.csv', index_col=0, parse_dates=True)")


if __name__ == "__main__":
    try:
        download_market_data()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
