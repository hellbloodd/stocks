# Trade Republic Stock Tracker

A system to track all Trade Republic stocks and sort them by profit/loss performance.

## Features
- Import trades from Trade Republic
- Calculate profit/loss per stock
- Sort stocks by performance (best to worst)
- View detailed trade history
- Export reports

## Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
pip install -r requirements.txt
```

### Usage

```bash
python main.py
```

## Project Structure

```
├── main.py                 # Entry point
├── config.py              # Configuration
├── data/
│   ├── trades.json        # Trade history
│   └── portfolio.json     # Current portfolio state
├── src/
│   ├── portfolio.py       # Portfolio management
│   ├── trade.py           # Trade data model
│   └── analytics.py       # Profit/loss calculations
└── tests/
    └── test_analytics.py  # Unit tests
```

## API Integration

Currently supports manual trade import. Trade Republic API integration coming soon.
