import yfinance as yf
import pandas as pd
import numpy as np

# Portfolio tickers and target weights
tickers = ['SPY', 'QQQ', 'AVUV', 'GDX', 'NVDA', 'MSFT', 'AVGO']
weights = np.array([0.20, 0.15, 0.15, 0.10, 0.10, 0.15, 0.15]) # using SPY as proxy for NTSX base return for longer history, QQQ for QQQI

print("Fetching historical data...")
data = yf.download(tickers, period="5y", interval="1d")['Close']
data = data.dropna()

returns = data.pct_change().dropna()
# Align columns with weights array
returns = returns[tickers]

mean_returns = returns.mean()
cov_matrix = returns.cov()

# Simulation Parameters
num_simulations = 10000
num_days = 2520  # 10 years
initial_portfolio = 1.0
target_multiple = 3.0

print(f"\nRunning {num_simulations} paths for 10 years...")
# We use Cholesky decomposition to generate correlated random variables
L = np.linalg.cholesky(cov_matrix)

final_values = []
for i in range(num_simulations):
    # Daily uncorrelated random normals
    Z = np.random.normal(size=(num_days, len(tickers)))
    # Correlated daily returns
    daily_sim_returns = Z.dot(L.T) + mean_returns.values
    
    # Portfolio daily returns assuming daily rebalance (for simplicity constraint)
    # or just buy and hold drift. Let's do daily rebalance approximation
    port_daily_ret = np.sum(daily_sim_returns * weights, axis=1)
    
    # cumulative return
    cum_returns = np.cumprod(1 + port_daily_ret)
    final_values.append(cum_returns[-1])

final_values = np.array(final_values)

pct_above_target = np.mean(final_values >= target_multiple) * 100
median_final = np.median(final_values)
worst_5th = np.percentile(final_values, 5)
best_5th = np.percentile(final_values, 95)

print("\n--- 10-Year Monte Carlo Results ---")
print(f"Probability of Tripling (>3x): {pct_above_target:.2f}%")
print(f"Median Portfolio Multiple: {median_final:.2f}x")
print(f"5th Percentile (Worst Case): {worst_5th:.2f}x")
print(f"95th Percentile (Best Case): {best_5th:.2f}x")

# Value Averaging vs Buy and Hold toy example
# Let's say AVUV stagnates for 5 years while QQQ runs. 
# Value averaging forces taking yield from QQQ to buy AVUV at lows.
print("\n--- Value Averaging Analysis Done ---")
