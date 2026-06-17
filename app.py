from flask import Flask, jsonify, request
from flask_cors import CORS
from src.portfolio import Portfolio
from src.analytics import PortfolioAnalytics
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Initialize portfolio
portfolio = Portfolio('data/trades.json')
analytics = PortfolioAnalytics(portfolio)

@app.route('/api/portfolio/summary', methods=['GET'])
def get_portfolio_summary():
    """Get overall portfolio summary."""
    summary = analytics.get_portfolio_summary()
    return jsonify(summary)

@app.route('/api/stocks/performance', methods=['GET'])
def get_stocks_performance():
    """Get all stocks sorted by profit/loss (best to worst)."""
    sorted_stocks = analytics.get_sorted_by_performance(ascending=False)
    result = []
    for symbol, data in sorted_stocks:
        result.append({
            'symbol': symbol,
            'profit_loss': round(data['profit_loss'], 2),
            'profit_loss_percent': round(data['profit_loss_percent'], 2),
            'trade_count': data['trade_count'],
            'total_invested': round(data['total_invested'], 2)
        })
    return jsonify(result)

@app.route('/api/stocks/<symbol>', methods=['GET'])
def get_stock_details(symbol):
    """Get detailed info for a specific stock."""
    trades = portfolio.get_trades_by_symbol(symbol.upper())
    if not trades:
        return jsonify({'error': 'Stock not found'}), 404
    
    result = []
    for i, trade in enumerate(trades):
        current_price = portfolio.current_prices.get(symbol.upper(), trade.exit_price)
        result.append({
            'index': i,
            'symbol': trade.symbol,
            'quantity': trade.quantity,
            'entry_price': trade.entry_price,
            'entry_date': trade.entry_date.isoformat(),
            'exit_price': trade.exit_price,
            'exit_date': trade.exit_date.isoformat() if trade.exit_date else None,
            'is_open': trade.is_open,
            'cost_basis': round(trade.cost_basis, 2),
            'profit_loss': round(trade.profit_loss(current_price), 2) if current_price else 0,
            'profit_loss_percent': round(trade.profit_loss_percent(current_price), 2) if current_price else 0
        })
    
    return jsonify(result)

@app.route('/api/stocks', methods=['GET'])
def get_all_stocks():
    """Get all unique symbols in portfolio."""
    symbols = sorted(list(set(t.symbol for t in portfolio.trades)))
    return jsonify({'symbols': symbols})

@app.route('/api/trades', methods=['POST'])
def add_trade():
    """Add a new trade to the portfolio."""
    from src.trade import Trade
    
    data = request.json
    try:
        trade = Trade(
            symbol=data['symbol'].upper(),
            quantity=float(data['quantity']),
            entry_price=float(data['entry_price']),
            entry_date=datetime.fromisoformat(data['entry_date']),
            exit_price=float(data['exit_price']) if data.get('exit_price') else None,
            exit_date=datetime.fromisoformat(data['exit_date']) if data.get('exit_date') else None
        )
        portfolio.add_trade(trade)
        return jsonify({'message': 'Trade added successfully'}), 201
    except (KeyError, ValueError) as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/prices/<symbol>', methods=['POST'])
def set_price(symbol):
    """Set current price for a stock."""
    data = request.json
    try:
        price = float(data['price'])
        portfolio.set_current_price(symbol.upper(), price)
        return jsonify({'message': f'Price set for {symbol}'}), 200
    except (KeyError, ValueError) as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
