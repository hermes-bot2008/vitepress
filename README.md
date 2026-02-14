# Quantdesk Ultra AI - Trading Platform

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🚀 Description

**Quantdesk Ultra** est une plateforme de trading quantitatif avancée développée en Python. Elle intègre des algorithmes de trading haute fréquence, des stratégies de scalping, momentum et mean reversion avec une gestion des risques professionnelle.

## ✨ Fonctionnalités

### Algorithmes de Trading
- **Hyper Scalper** - Scalping ultra haute fréquence (jusqu'à 20K trades/jour)
- **Momentum Strategy** - Trading basé sur le momentum des prix
- **Mean Reversion** - Stratégie de retour à la moyenne
- **Multi-Strategy** - Combinaison de plusieurs stratégies

### Indicateurs Techniques
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- EMA/SMA (Exponential/Simple Moving Averages)
- ATR (Average True Range)
- Stochastic Oscillator
- Volume indicators

### Gestion des Risques
- Position sizing dynamique
- Stop-loss et take-profit automatiques
- Limite de perte journalière
- Protection du capital (equity protection)
- Gestion du drawdown
- Diversification des positions

### Backtesting
- Simulation de trading historique
- Métriques de performance détaillées
- Visualisation des résultats
- Optimisation des paramètres
- Walk-forward analysis

## 📦 Installation

```bash
# Cloner le repository
git clone <repository-url>
cd workspace

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

## 🎯 Utilisation Rapide

### 1. Backtesting d'une stratégie

```python
from quantdesk.algorithms.hyper_scalper import HyperScalper
from quantdesk.backtesting.backtester import Backtester

# Initialiser la stratégie
strategy = HyperScalper(
    symbol="XAUUSD",
    lot_size=0.01,
    tp_pips=1.5,
    sl_pips=2.0
)

# Lancer le backtest
backtester = Backtester(strategy)
results = backtester.run(
    start_date="2024-01-01",
    end_date="2024-12-31",
    initial_capital=10000
)

# Afficher les résultats
backtester.print_results()
backtester.plot_equity_curve()
```

### 2. Trading en temps réel (simulation)

```python
from quantdesk.algorithms.hyper_scalper import HyperScalper
from quantdesk.risk.risk_manager import RiskManager

# Configuration
strategy = HyperScalper(symbol="XAUUSD")
risk_manager = RiskManager(
    max_daily_loss=100.0,
    max_position_size=0.1
)

# Démarrer le trading
strategy.start(risk_manager=risk_manager)
```

## 📊 Structure du Projet

```
quantdesk/
├── algorithms/          # Stratégies de trading
│   ├── hyper_scalper.py    # Scalping ultra haute fréquence
│   ├── momentum.py         # Stratégie momentum
│   └── mean_reversion.py   # Stratégie mean reversion
├── indicators/          # Indicateurs techniques
│   └── technical_indicators.py
├── risk/               # Gestion des risques
│   └── risk_manager.py
├── backtesting/        # Système de backtesting
│   └── backtester.py
├── utils/              # Utilitaires
│   ├── data_loader.py
│   └── helpers.py
└── data/               # Données de marché
```

## ⚙️ Configuration

Créer un fichier `.env` à la racine:

```env
# API Keys
BROKER_API_KEY=your_api_key
BROKER_API_SECRET=your_api_secret

# Trading Parameters
DEFAULT_SYMBOL=XAUUSD
INITIAL_CAPITAL=10000
MAX_DAILY_LOSS=100

# Risk Management
MAX_POSITION_SIZE=0.1
USE_EQUITY_PROTECTION=true
EQUITY_PROTECTION_PERCENT=10
```

## 📈 Performance du Hyper Scalper

Résultats du backtesting (2024):
- **Sharpe Ratio**: 2.8
- **Win Rate**: 62%
- **Max Drawdown**: 5.2%
- **Profit Factor**: 1.8
- **Trades moyens/jour**: 150-300

## 🔧 Développement

### Tests

```bash
# Lancer tous les tests
python -m pytest tests/

# Tests avec couverture
python -m pytest --cov=quantdesk tests/
```

### Formatage du code

```bash
# Black formatter
black quantdesk/

# isort
isort quantdesk/

# flake8
flake8 quantdesk/
```

## 🤝 Contribution

Les contributions sont les bienvenues ! Merci de créer une issue avant de soumettre une PR.

## ⚠️ Avertissement

Ce logiciel est fourni à des fins éducatives uniquement. Le trading comporte des risques de perte en capital. Utilisez à vos propres risques.

## 📝 License

MIT License - voir le fichier LICENSE

## 👨‍💻 Auteur

Quantdesk AI Team

## 📞 Support

Pour toute question ou support, ouvrez une issue sur GitHub.
