const API_BASE = 'http://localhost:5000/api';

// Load portfolio summary
async function loadPortfolioSummary() {
    try {
        const response = await fetch(`${API_BASE}/portfolio/summary`);
        const data = await response.json();
        
        document.getElementById('totalInvested').textContent = formatCurrency(data.total_invested);
        document.getElementById('totalPL').textContent = formatCurrency(data.total_profit_loss);
        document.getElementById('returnPercent').textContent = formatPercent(data.total_profit_loss_percent);
        document.getElementById('stockCount').textContent = data.symbol_count;
        document.getElementById('tradeCount').textContent = data.trade_count;
    } catch (error) {
        console.error('Error loading portfolio summary:', error);
    }
}

// Load stocks performance
async function loadStocksPerformance() {
    try {
        const response = await fetch(`${API_BASE}/stocks/performance`);
        const stocks = await response.json();
        
        const tbody = document.getElementById('stocksTableBody');
        tbody.innerHTML = '';
        
        if (stocks.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">No trades yet. Add a trade to get started!</td></tr>';
            return;
        }
        
        stocks.forEach(stock => {
            const row = document.createElement('tr');
            const plClass = stock.profit_loss >= 0 ? 'positive' : 'negative';
            const plPercentClass = stock.profit_loss_percent >= 0 ? 'positive' : 'negative';
            
            row.innerHTML = `
                <td><strong>${stock.symbol}</strong></td>
                <td class="${plClass}">${formatCurrency(stock.profit_loss)}</td>
                <td class="${plPercentClass}">${formatPercent(stock.profit_loss_percent)}</td>
                <td>${stock.trade_count}</td>
                <td>${formatCurrency(stock.total_invested)}</td>
                <td><button class="btn btn-info" onclick="viewStockDetails('${stock.symbol}')">Details</button></td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading stocks performance:', error);
        document.getElementById('stocksTableBody').innerHTML = 
            '<tr><td colspan="6" class="loading">Error loading stocks</td></tr>';
    }
}

// View stock details
async function viewStockDetails(symbol) {
    try {
        const response = await fetch(`${API_BASE}/stocks/${symbol}`);
        const trades = await response.json();
        
        const modal = document.getElementById('detailsModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');
        
        modalTitle.textContent = `${symbol} - Trade Details`;
        
        let html = '';
        trades.forEach((trade, index) => {
            html += `
                <div class="trade-detail">
                    <div>
                        <label>Trade #${index + 1}</label>
                        <span class="value">${trade.symbol}</span>
                    </div>
                    <div>
                        <label>Quantity</label>
                        <span class="value">${trade.quantity}</span>
                    </div>
                    <div>
                        <label>Entry Price</label>
                        <span class="value">${formatCurrency(trade.entry_price)}</span>
                    </div>
                    <div>
                        <label>Entry Date</label>
                        <span class="value">${formatDate(trade.entry_date)}</span>
                    </div>
                    <div>
                        <label>Cost Basis</label>
                        <span class="value">${formatCurrency(trade.cost_basis)}</span>
                    </div>
                    <div>
                        <label>Status</label>
                        <span class="value">${trade.is_open ? '🔵 Open' : '✅ Closed'}</span>
                    </div>
                    ${trade.exit_price ? `
                        <div>
                            <label>Exit Price</label>
                            <span class="value">${formatCurrency(trade.exit_price)}</span>
                        </div>
                        <div>
                            <label>Exit Date</label>
                            <span class="value">${formatDate(trade.exit_date)}</span>
                        </div>
                    ` : ''}
                    <div>
                        <label>Profit/Loss</label>
                        <span class="value ${trade.profit_loss >= 0 ? 'positive' : 'negative'}">${formatCurrency(trade.profit_loss)}</span>
                    </div>
                    <div>
                        <label>Return %</label>
                        <span class="value ${trade.profit_loss_percent >= 0 ? 'positive' : 'negative'}">${formatPercent(trade.profit_loss_percent)}</span>
                    </div>
                </div>
            `;
        });
        
        modalBody.innerHTML = html;
        modal.style.display = 'block';
    } catch (error) {
        console.error('Error loading stock details:', error);
        alert('Error loading stock details');
    }
}

// Add trade
document.getElementById('addTradeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const tradeData = {
        symbol: document.getElementById('symbol').value,
        quantity: parseFloat(document.getElementById('quantity').value),
        entry_price: parseFloat(document.getElementById('entryPrice').value),
        entry_date: document.getElementById('entryDate').value,
        exit_price: document.getElementById('exitPrice').value ? parseFloat(document.getElementById('exitPrice').value) : null,
        exit_date: document.getElementById('exitDate').value || null
    };
    
    try {
        const response = await fetch(`${API_BASE}/trades`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(tradeData)
        });
        
        if (response.ok) {
            alert('Trade added successfully!');
            document.getElementById('addTradeForm').reset();
            loadPortfolioSummary();
            loadStocksPerformance();
        } else {
            alert('Error adding trade');
        }
    } catch (error) {
        console.error('Error adding trade:', error);
        alert('Error adding trade');
    }
});

// Refresh button
document.getElementById('refreshBtn').addEventListener('click', () => {
    loadPortfolioSummary();
    loadStocksPerformance();
});

// Modal close
document.querySelector('.close').addEventListener('click', () => {
    document.getElementById('detailsModal').style.display = 'none';
});

window.addEventListener('click', (event) => {
    const modal = document.getElementById('detailsModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
});

// Utility functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function formatPercent(value) {
    return (value >= 0 ? '+' : '') + value.toFixed(2) + '%';
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Load data on page load
window.addEventListener('DOMContentLoaded', () => {
    loadPortfolioSummary();
    loadStocksPerformance();
    
    // Set default date to now
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('entryDate').value = now.toISOString().slice(0, 16);
});
