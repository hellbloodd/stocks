#!/usr/bin/env python3

from src.portfolio import Portfolio
from src.analytics import PortfolioAnalytics
from tabulate import tabulate
from datetime import datetime
import json

def display_portfolio_summary(portfolio: Portfolio, analytics: PortfolioAnalytics):
    """Display overall portfolio summary."""
    summary = analytics.get_portfolio_summary()
    print("\n" + "="*60)
    print("PORTFOLIO SUMMARY")
    print("="*60)
    print(f"Total Invested: ${summary['total_invested']:,.2f}")
    print(f"Total Profit/Loss: ${summary['total_profit_loss']:,.2f}")
    print(f"Total Return: {summary['total_profit_loss_percent']:.2f}%")
    print(f"Total Trades: {summary['trade_count']}")
    print(f"Stocks: {summary['symbol_count']}")
    print("="*60 + "\n")

def display_stocks_by_performance(analytics: PortfolioAnalytics):
    """Display stocks sorted by profit/loss performance."""
    sorted_stocks = analytics.get_sorted_by_performance(ascending=False)
    
    table_data = []
    for symbol, data in sorted_stocks:
        table_data.append([
            symbol,
            f"${data['profit_loss']:,.2f}",
            f"{data['profit_loss_percent']:.2f}%",
            data['trade_count'],
            f"${data['total_invested']:,.2f}"
        ])
    
    print("\nSTOCKS SORTED BY PROFIT/LOSS (Best to Worst)\n")
    headers = ['Symbol', 'Profit/Loss', 'Return %', 'Trades', 'Invested']
    print(tabulate(table_data, headers=headers, tablefmt='grid'))
    print()

def load_sample_data():
    """Load sample trades for demonstration."""
    sample_trades = [
        {
            'symbol': 'AAPL',
            'quantity': 10,
            'entry_price': 150.0,
            'entry_date': '2024-01-01T10:00:00',
            'exit_price': 165.0,
            'exit_date': '2024-06-01T10:00:00'
        },
        {
            'symbol': 'GOOGL',
            'quantity': 5,
            'entry_price': 2800.0,
            'entry_date': '2024-02-01T10:00:00',
            'exit_price': 2900.0,
            'exit_date': '2024-05-01T10:00:00'
        },
        {
            'symbol': 'MSFT',
            'quantity': 20,
            'entry_price': 300.0,
            'entry_date': '2024-03-01T10:00:00',
            'exit_price': None,
            'exit_date': None
        },
        {
            'symbol': 'TSLA',
            'quantity': 3,
            'entry_price': 250.0,
            'entry_date': '2024-01-15T10:00:00',
            'exit_price': 200.0,
            'exit_date': '2024-04-01T10:00:00'
        }
    ]
    
    with open('data/trades.json', 'w') as f:
        json.dump(sample_trades, f, indent=2)
    print("Sample data loaded to data/trades.json")

def main():
    print("\n🚀 Trade Republic Stock Tracker\n")
    
    # Load portfolio
    portfolio = Portfolio('data/trades.json')
    analytics = PortfolioAnalytics(portfolio)
    
    # Set current prices for open positions (example)
    portfolio.set_current_price('MSFT', 320.0)
    
    # Display results
    display_portfolio_summary(portfolio, analytics)
    display_stocks_by_performance(analytics)
    
    print("For detailed trade history, check data/trades.json")

if __name__ == '__main__':
    # Uncomment to load sample data
    # load_sample_data()
    
    main()
