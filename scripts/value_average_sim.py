import numpy as np

def simulate_investment(months=120, monthly_contribution=1000, initial_investment=100000):
    # Simulate a 2-asset portfolio: Asset A (High Growth, Volatile), Asset B (Steady Dividend/Value)
    # Target: 50% / 50%
    np.random.seed(42)
    
    # Asset A: 15% CAGR, 30% Volatility
    # Asset B: 8% CAGR, 12% Volatility
    
    # Monthly returns
    mu_a = 0.15 / 12
    vol_a = 0.30 / np.sqrt(12)
    mu_b = 0.08 / 12
    vol_b = 0.12 / np.sqrt(12)
    
    returns_a = np.random.normal(mu_a, vol_a, months)
    returns_b = np.random.normal(mu_b, vol_b, months)
    
    # Scenario 1: Standard DCA (50/50 every month regardless of drift)
    balance_a_dca = initial_investment / 2
    balance_b_dca = initial_investment / 2
    
    # Scenario 2: Fidelity Basket Value Averaging (Cash directed to underweight asset)
    balance_a_va = initial_investment / 2
    balance_b_va = initial_investment / 2
    
    for month in range(months):
        # Apply market returns
        balance_a_dca *= (1 + returns_a[month])
        balance_b_dca *= (1 + returns_b[month])
        
        balance_a_va *= (1 + returns_a[month])
        balance_b_va *= (1 + returns_b[month])
        
        # Standard DCA Additions
        balance_a_dca += monthly_contribution / 2
        balance_b_dca += monthly_contribution / 2
        
        # Value Averaging Additions (Fidelity Basket Logic)
        total_va = balance_a_va + balance_b_va
        target_a = total_va * 0.50
        target_b = total_va * 0.50
        
        # Who is furthest behind their target in dollar terms?
        deficit_a = target_a - balance_a_va
        deficit_b = target_b - balance_b_va
        
        # Allocate the contribution solely to the lagging asset if the gap is large enough
        if deficit_a > 0 and deficit_b <= 0:
            balance_a_va += monthly_contribution
        elif deficit_b > 0 and deficit_a <= 0:
            balance_b_va += monthly_contribution
        else:
            # If both are below target (rare, only if massive market drop exceeds contribution)
            # or neither (impossible), default to 50/50
            if deficit_a > deficit_b:
                balance_a_va += monthly_contribution
            else:
                balance_b_va += monthly_contribution
                
    total_dca = balance_a_dca + balance_b_dca
    total_va = balance_a_va + balance_b_va
    
    # Calculate portfolio volatility over the period (rough estimate of risk alignment to target)
    print("--- 10-Year Value Averaging vs Standard DCA Simulation ---")
    print(f"Standard DCA Final Balance: ${total_dca:,.2f}")
    print(f"Standard DCA Final Spread: Asset A {balance_a_dca/total_dca:.1%} | Asset B {balance_b_dca/total_dca:.1%}")
    print(f"Value Average Final Balance: ${total_va:,.2f}")
    print(f"Value Average Final Spread: Asset A {balance_a_va/total_va:.1%} | Asset B {balance_b_va/total_va:.1%}")
    print(f"VA Outperformance (Absolute): +${total_va - total_dca:,.2f}")
    
    # Tax Drag avoided: If we had to rebalance DCA to 50/50, we'd sell the winner.
    print(f"Tax Events Triggered by VA: 0 (All rebalancing handled by cash flow sweep)")

if __name__ == '__main__':
    simulate_investment()
