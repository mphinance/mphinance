#!/usr/bin/env python3
"""
Revenue Transparency — Full Stripe + TastyTrade data for landing page.

Produces the rich schema expected by landing/index.html:
  - Stripe audit (charges, fees, refunds, payouts, subscriptions, monthly P&L)
  - Allocation (brokerage 50%, paycheck 20%, tax 30%)
  - TastyTrade brokerage (positions, premiums, cost basis, wash sales)

Outputs to landing/data/revenue_stats.json.

Usage:
    STRIPE_SECRET_KEY=sk_live_... TASTYTRADE_REFRESH_TOKEN=... python3 dossier/fetch_revenue.py
"""

import os
import json
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "landing" / "data" / "revenue_stats.json"

# ──────────────────────────────────────────────
# STRIPE
# ──────────────────────────────────────────────

def fetch_stripe_data():
    """Fetch full Stripe revenue data."""
    try:
        import stripe
    except ImportError:
        print("[WARN] stripe not installed, skipping Stripe data")
        return None

    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe.api_key:
        try:
            from gcp.secrets import get_secret
            stripe.api_key = get_secret("STRIPE_SECRET_KEY")
        except Exception:
            pass

    if not stripe.api_key:
        print("[WARN] STRIPE_SECRET_KEY not set, skipping Stripe data")
        return None

    print("📊 Fetching Stripe data...")

    # ── Charges ──
    all_charges = []
    params = {"limit": 100}
    while True:
        charges = stripe.Charge.list(**params)
        all_charges.extend(charges.data)
        if not charges.has_more:
            break
        params["starting_after"] = charges.data[-1].id

    succeeded = [c for c in all_charges if c.status == "succeeded"]
    refunded = [c for c in all_charges if c.refunded]

    gross = sum(c.amount / 100 for c in succeeded)
    fees_total = 0
    platform_fees = 0
    for c in succeeded:
        if c.balance_transaction:
            try:
                bt = stripe.BalanceTransaction.retrieve(c.balance_transaction)
                fees_total += bt.fee / 100
            except Exception:
                fees_total += c.amount * 0.029 / 100 + 0.30  # estimate

    refund_amount = sum(c.amount_refunded / 100 for c in refunded)
    refund_count = len(refunded)
    net_revenue = gross - fees_total - refund_amount

    # ── Payouts ──
    all_payouts = []
    params = {"limit": 100}
    while True:
        payouts = stripe.Payout.list(**params)
        all_payouts.extend(payouts.data)
        if not payouts.has_more:
            break
        params["starting_after"] = payouts.data[-1].id

    paid_payouts = [p for p in all_payouts if p.status == "paid"]
    net_payouts = sum(p.amount / 100 for p in paid_payouts)
    last_payout = paid_payouts[0] if paid_payouts else None

    # ── Balance ──
    try:
        balance = stripe.Balance.retrieve()
        available = sum(b.amount / 100 for b in balance.available)
        pending = sum(b.amount / 100 for b in balance.pending)
    except Exception:
        available, pending = 0, 0

    # ── Subscriptions ──
    try:
        active_subs = stripe.Subscription.list(status="active", limit=100)
        canceled_subs = stripe.Subscription.list(status="canceled", limit=100)
        active_count = len(active_subs.data)
        canceled_count = len(canceled_subs.data)
        total_subs = active_count + canceled_count
        churn_rate = round(canceled_count / total_subs * 100, 1) if total_subs > 0 else 0
        mrr = sum(s.plan.amount / 100 for s in active_subs.data if s.plan) if active_subs.data else 0
    except Exception:
        active_count, canceled_count, churn_rate, mrr = 0, 0, 0, 0

    # ── Monthly breakdown ──
    monthly = defaultdict(lambda: {"gross": 0, "fees": 0, "net": 0, "count": 0})
    for c in succeeded:
        dt = datetime.fromtimestamp(c.created)
        key = dt.strftime("%Y-%m")
        amt = c.amount / 100
        monthly[key]["gross"] += amt
        monthly[key]["count"] += 1

    # Distribute fees proportionally
    for key in monthly:
        ratio = monthly[key]["gross"] / gross if gross > 0 else 0
        monthly[key]["fees"] = round(fees_total * ratio, 2)
        monthly[key]["net"] = round(monthly[key]["gross"] - monthly[key]["fees"], 2)
        monthly[key]["gross"] = round(monthly[key]["gross"], 2)

    # ── API calls log ──
    api_calls = [
        f'<span style="color:#00ff88">→</span> stripe.Charge.list() <span style="color:#555">// {len(all_charges)} charges</span>',
        f'<span style="color:#00ff88">→</span> stripe.Payout.list() <span style="color:#555">// {len(paid_payouts)} payouts</span>',
        f'<span style="color:#00ff88">→</span> stripe.Balance.retrieve() <span style="color:#555">// ${available + pending:.2f}</span>',
        f'<span style="color:#00ff88">→</span> stripe.Subscription.list() <span style="color:#555">// {active_count} active</span>',
    ]

    stripe_data = {
        "stripe_audit": {
            "gross_charges": round(gross, 2),
            "charge_count": len(succeeded),
            "stripe_fees": round(fees_total, 2),
            "platform_fees": round(platform_fees, 2),
            "refunds": round(refund_amount, 2),
            "refund_count": refund_count,
            "fee_refunds": round(refund_amount * 0.1, 2),  # approximate fee recovery
            "net_revenue": round(net_revenue, 2),
            "fee_rate_pct": round(fees_total / gross * 100, 1) if gross > 0 else 0,
        },
        "gross_revenue": round(gross, 2),
        "subscription_count": len(succeeded),
        "net_payouts": round(net_payouts, 2),
        "payout_count": len(paid_payouts),
        "stripe_balance": {
            "available": round(available, 2),
            "pending": round(pending, 2),
            "total": round(available + pending, 2),
            "last_payout": {
                "amount": round(last_payout.amount / 100, 2) if last_payout else 0,
                "date": datetime.fromtimestamp(last_payout.created).strftime("%Y-%m-%d") if last_payout else "",
                "destination": "Relay",
            } if last_payout else None,
        },
        "subscriptions": {
            "active": active_count,
            "canceled": canceled_count,
            "churn_rate": churn_rate,
            "mrr": round(mrr, 2),
            "arr": round(mrr * 12, 2),
        },
        "monthly": dict(sorted(monthly.items())),
        "api_calls": api_calls,
    }

    # ── Allocation (50/20/30 split) ──
    total_net = net_payouts
    brokerage_target = round(total_net * 0.50, 2)
    paycheck_target = round(total_net * 0.20, 2)
    tax_target = round(total_net * 0.30, 2)

    # Load previous allocation actuals if they exist (manual overrides persist)
    prev = {}
    if OUTPUT_FILE.exists():
        try:
            prev = json.load(open(OUTPUT_FILE)).get("allocation", {})
        except Exception:
            pass

    stripe_data["allocation"] = {
        "brokerage": {
            "actual": prev.get("brokerage", {}).get("actual", brokerage_target),
            "target": brokerage_target,
            "pct_actual": round(prev.get("brokerage", {}).get("actual", brokerage_target) / total_net * 100, 1) if total_net > 0 else 0,
            "pct_target": 50,
            "delta": round(prev.get("brokerage", {}).get("actual", brokerage_target) - brokerage_target, 2),
        },
        "paychecks": {
            "actual": prev.get("paychecks", {}).get("actual", paycheck_target),
            "target": paycheck_target,
            "pct_actual": round(prev.get("paychecks", {}).get("actual", paycheck_target) / total_net * 100, 1) if total_net > 0 else 0,
            "pct_target": 20,
            "delta": round(prev.get("paychecks", {}).get("actual", paycheck_target) - paycheck_target, 2),
        },
        "tax_savings": {
            "actual": prev.get("tax_savings", {}).get("actual", tax_target),
            "target": tax_target,
            "pct_actual": round(prev.get("tax_savings", {}).get("actual", tax_target) / total_net * 100, 1) if total_net > 0 else 0,
            "pct_target": 30,
            "delta": round(prev.get("tax_savings", {}).get("actual", tax_target) - tax_target, 2),
        },
        "unallocated": {
            "amount": round(total_net - prev.get("brokerage", {}).get("actual", brokerage_target) 
                       - prev.get("paychecks", {}).get("actual", paycheck_target)
                       - prev.get("tax_savings", {}).get("actual", tax_target), 2),
            "pct": round((total_net - prev.get("brokerage", {}).get("actual", brokerage_target)
                         - prev.get("paychecks", {}).get("actual", paycheck_target)
                         - prev.get("tax_savings", {}).get("actual", tax_target)) / total_net * 100, 1) if total_net > 0 else 0,
        },
    }

    print(f"  ✓ Stripe: ${gross:,.2f} gross, ${net_payouts:,.2f} net, {active_count} active subs")
    return stripe_data


# ──────────────────────────────────────────────
# TASTYTRADE
# ──────────────────────────────────────────────

def fetch_tastytrade_data():
    """Fetch TastyTrade portfolio data using OAuth refresh token."""
    refresh_token = os.environ.get("TASTYTRADE_REFRESH_TOKEN", "")
    client_id = os.environ.get("TASTYTRADE_CLIENT_ID", "")
    client_secret = os.environ.get("TASTYTRADE_CLIENT_SECRET", "")

    if not refresh_token:
        # Try VaultGuard
        try:
            from gcp.secrets import get_secret
            refresh_token = get_secret("TASTYTRADE_REFRESH_TOKEN")
            client_id = client_id or get_secret("TASTYTRADE_CLIENT_ID")
            client_secret = client_secret or get_secret("TASTYTRADE_CLIENT_SECRET")
        except Exception:
            pass

    if not refresh_token:
        print("[WARN] TASTYTRADE_REFRESH_TOKEN not set, skipping brokerage data")
        return None

    print("📊 Fetching TastyTrade data...")

    BASE = "https://api.tastytrade.com"

    # ── Get access token ──
    try:
        token_resp = requests.post(
            f"{BASE}/oauth/token",
            json={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/json"},
            timeout=15,
        )

        if token_resp.status_code != 200:
            print(f"  [ERR] TastyTrade OAuth failed: {token_resp.status_code} {token_resp.text[:200]}")
            return None

        auth_data = token_resp.json()
        token = auth_data.get("access_token", "")
        if not token:
            print(f"  [ERR] No access_token in response: {list(auth_data.keys())}")
            return None

    except Exception as e:
        print(f"  [ERR] TastyTrade auth failed: {e}")
        return None

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # ── Get accounts ──
    try:
        accts = requests.get(f"{BASE}/customers/me/accounts", headers=headers, timeout=10).json()
        account_number = accts["data"]["items"][0]["account"]["account-number"]
        print(f"  Account: {account_number}")
    except Exception as e:
        print(f"  [ERR] TastyTrade accounts failed: {e}")
        return None

    # ── Get balances ──
    try:
        bal = requests.get(f"{BASE}/accounts/{account_number}/balances", headers=headers, timeout=10).json()
        bal_data = bal["data"]
        net_liq = float(bal_data.get("net-liquidating-value", 0))
        cash = float(bal_data.get("cash-balance", 0))
    except Exception as e:
        print(f"  [ERR] TastyTrade balances failed: {e}")
        net_liq, cash = 0, 0

    # ── Get positions ──
    try:
        pos_resp = requests.get(f"{BASE}/accounts/{account_number}/positions", headers=headers, timeout=10).json()
        positions_raw = pos_resp["data"]["items"]
    except Exception as e:
        print(f"  [ERR] TastyTrade positions failed: {e}")
        positions_raw = []

    # ── Get transactions for premium income ──
    premium_by_symbol = defaultdict(float)
    total_deposited = 0
    total_withdrawn = 0
    realized_losses = 0
    transactions = []

    try:
        # Fetch recent transactions
        txn_resp = requests.get(
            f"{BASE}/accounts/{account_number}/transactions",
            headers=headers,
            params={"per-page": 250},
            timeout=15,
        ).json()
        transactions = txn_resp.get("data", {}).get("items", [])

        for txn in transactions:
            txn_type = txn.get("transaction-type", "")
            sub_type = txn.get("transaction-sub-type", "")
            amount = float(txn.get("net-value", 0))
            symbol = txn.get("underlying-symbol", txn.get("symbol", ""))

            # Premium income from selling options
            if txn_type == "Trade" and sub_type in ("Sell to Open", "Buy to Close"):
                if sub_type == "Sell to Open":
                    premium_by_symbol[symbol] += abs(amount)
                elif sub_type == "Buy to Close":
                    premium_by_symbol[symbol] -= abs(amount)  # cost to close

            # Deposits/withdrawals
            if txn_type == "Money Movement":
                if amount > 0:
                    total_deposited += amount
                else:
                    total_withdrawn += abs(amount)

            # Realized losses
            if txn_type == "Trade" and sub_type == "Sell to Close" and amount < 0:
                realized_losses += amount

    except Exception as e:
        print(f"  [WARN] TastyTrade transactions failed: {e}")

    # ── Build positions with premiums ──
    positions_out = []
    top_positions = []
    wheel_symbols = set()
    total_premium = sum(max(0, v) for v in premium_by_symbol.values())
    unrealized_pnl = 0

    for pos in positions_raw:
        symbol = pos.get("underlying-symbol", pos.get("symbol", ""))
        qty = int(float(pos.get("quantity", 0)))
        direction = pos.get("quantity-direction", "Long")
        inst_type = pos.get("instrument-type", "Equity")

        if inst_type != "Equity" or qty == 0:
            continue

        cost = float(pos.get("average-open-price", 0))
        mkt = float(pos.get("mark-price", pos.get("close-price", cost)))
        pnl = round((mkt - cost) * qty, 2) if direction == "Long" else round((cost - mkt) * qty, 2)
        unrealized_pnl += pnl
        premium = round(premium_by_symbol.get(symbol, 0), 2)
        net_pnl = round(pnl + premium, 2)

        has_premium = premium > 0
        strategy = "Wheel (assigned + calls)" if has_premium else "Long equity"
        if has_premium:
            wheel_symbols.add(symbol)

        pos_entry = {
            "symbol": symbol,
            "qty": abs(qty),
            "cost_basis": round(cost, 2),
            "mkt": round(mkt, 2),
            "stock_pnl": pnl,
            "premium": max(0, premium),
            "net_pnl": net_pnl,
            "strategy": strategy,
        }
        positions_out.append(pos_entry)
        top_positions.append({
            "symbol": symbol,
            "qty": abs(qty),
            "cost": round(cost, 2),
            "mkt": round(mkt, 2),
            "pnl": pnl,
        })

    top_positions.sort(key=lambda x: abs(x["pnl"]), reverse=True)
    positions_out.sort(key=lambda x: abs(x["net_pnl"]), reverse=True)

    # ── Load wash sales from previous data (needed for closed position P&L cross-check) ──
    wash_sales = []
    if OUTPUT_FILE.exists():
        try:
            prev = json.load(open(OUTPUT_FILE))
            wash_sales = prev.get("brokerage", {}).get("wash_sales", [])
            today = datetime.now()
            wash_sales = [w for w in wash_sales
                         if datetime.strptime(w["wash_sale_end"], "%Y-%m-%d") > today]
        except Exception:
            pass

    # ── Add CLOSED positions that had premium income ──
    current_symbols = {p["symbol"] for p in positions_out}
    for symbol, prem in premium_by_symbol.items():
        if symbol in current_symbols or prem <= 0:
            continue
        # This is a closed position with premium collected (e.g., BITF)
        # Find buy/sell details from transactions to compute actual realized P&L
        total_buy_cost = 0  # total spent buying shares
        total_sale_proceeds = 0  # total received selling shares
        sale_qty = 0

        for txn in transactions:
            tsym = txn.get("underlying-symbol", txn.get("symbol", ""))
            if tsym != symbol:
                continue
            txn_type = txn.get("transaction-type", "")
            sub = txn.get("transaction-sub-type", "")
            amt = float(txn.get("net-value", 0))

            if txn_type != "Trade":
                continue

            # Stock trades (not options — those are tracked in premium_by_symbol)
            inst = txn.get("instrument-type", "")
            if inst == "Equity":
                if sub in ("Buy to Open", "Buy"):
                    total_buy_cost += abs(amt)
                elif sub in ("Sell to Close", "Sell"):
                    total_sale_proceeds += abs(amt)
                    sale_qty += abs(int(float(txn.get("quantity", 0))))

        # Realized stock P&L = proceeds - cost
        realized_stock_pnl = round(total_sale_proceeds - total_buy_cost, 2)

        # Cross-check with wash sale data if available
        for ws in wash_sales:
            if ws.get("symbol") == symbol and ws.get("realized_loss"):
                realized_stock_pnl = ws["realized_loss"]
                break

        pos_entry = {
            "symbol": symbol,
            "qty": 0,
            "qty_sold": sale_qty or 0,
            "cost_basis": round(total_buy_cost / sale_qty, 2) if sale_qty else 0,
            "sale_price": round(total_sale_proceeds / sale_qty, 2) if sale_qty else 0,
            "mkt": 0,
            "stock_pnl": realized_stock_pnl,
            "premium": round(prem, 2),
            "net_pnl": round(realized_stock_pnl + prem, 2),
            "strategy": "Wheel (closed)",
            "closed": True,
        }
        positions_out.append(pos_entry)
        wheel_symbols.add(symbol)

    # wash_sales already loaded above

    adjusted_pnl = round(unrealized_pnl + total_premium + realized_losses, 2)

    brokerage = {
        "account": account_number,
        "net_liquidating_value": round(net_liq, 2),
        "cash_balance": round(cash, 2),
        "total_deposited": round(total_deposited, 2),
        "total_withdrawn": round(total_withdrawn, 2),
        "net_deposited": round(total_deposited - total_withdrawn, 2),
        "pnl_dollars": round(net_liq - (total_deposited - total_withdrawn), 2),
        "pnl_pct": round((net_liq / (total_deposited - total_withdrawn) - 1) * 100, 1)
            if (total_deposited - total_withdrawn) > 0 else 0,
        "position_count": len(positions_out),
        "top_positions": top_positions[:9],
        "total_premium_income": round(total_premium, 2),
        "wheel_symbols": sorted(list(wheel_symbols)),
        "positions_with_premiums": positions_out,
        "unrealized_stock_pnl": round(unrealized_pnl, 2),
        "realized_losses": round(realized_losses, 2),
        "total_premium_collected": round(total_premium, 2),
        "adjusted_pnl": adjusted_pnl,
        "wash_sales": wash_sales,
    }

    print(f"  ✓ TastyTrade: ${net_liq:,.2f} NLV, {len(positions_out)} positions, ${total_premium:,.2f} premium")
    return brokerage


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def fetch_stripe_revenue():
    """Main entry point — merges Stripe + TastyTrade into full revenue stats."""
    print("═══ Revenue Transparency — Full Refresh ═══\n")

    stats = {"updated": datetime.now().strftime("%Y-%m-%d %H:%M")}

    # Stripe data
    stripe_data = fetch_stripe_data()
    if stripe_data:
        stats.update(stripe_data)
    else:
        # Preserve existing Stripe data if we can't refresh
        if OUTPUT_FILE.exists():
            try:
                prev = json.load(open(OUTPUT_FILE))
                for k in ["stripe_audit", "gross_revenue", "subscription_count", "net_payouts",
                           "payout_count", "stripe_balance", "subscriptions", "allocation",
                           "monthly", "api_calls"]:
                    if k in prev:
                        stats[k] = prev[k]
                print("  ⚠️ Using cached Stripe data")
            except Exception:
                pass

    # TastyTrade data
    tt_data = fetch_tastytrade_data()
    if tt_data:
        stats["brokerage"] = tt_data
        # Update API calls log
        if "api_calls" not in stats:
            stats["api_calls"] = []
        stats["api_calls"].extend([
            f'<span style="color:#00ff88">→</span> tastyworks.balances() <span style="color:#555">// ${tt_data["net_liquidating_value"]:,.2f} NLV</span>',
            f'<span style="color:#00ff88">→</span> tastyworks.positions() <span style="color:#555">// {tt_data["position_count"]} positions</span>',
            f'<span style="color:#00ff88">→</span> tastyworks.transactions() <span style="color:#555">// ${tt_data["total_premium_income"]:,.2f} premium</span>',
            f'<span style="color:#00ff88">→</span> tastyworks.wash_sales() <span style="color:#555">// {len(tt_data["wash_sales"])} active</span>',
        ])
    else:
        # Preserve existing TastyTrade data
        if OUTPUT_FILE.exists():
            try:
                prev = json.load(open(OUTPUT_FILE))
                if "brokerage" in prev:
                    stats["brokerage"] = prev["brokerage"]
                    print("  ⚠️ Using cached TastyTrade data")
            except Exception:
                pass

    print(f"\n{'═' * 50}")
    print(f"  Revenue stats updated: {stats['updated']}")
    print(f"{'═' * 50}")

    return stats


def main():
    stats = fetch_stripe_revenue()
    if not stats or len(stats) <= 1:  # only 'updated' key
        print("[ERR] No data fetched from any source")
        sys.exit(1)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\n✅ Revenue stats saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
