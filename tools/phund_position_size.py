#!/usr/bin/env python3
"""R-based position sizing for the Phund trade-rule block, replacing the flat
~$50/4%-of-book size with Van Tharp's risk-to-stop formula:

    position size = (dollars willing to risk) / (dollar risk per unit)
    risk$ = risk_pct * netliq

For stock: dollar risk per unit = entry - stop (a real stop order).
For a long option: risk is already capped at the premium by definition, so
the "stop" is either the full premium (you're willing to lose the whole
debit) or a chosen soft-exit fraction of it (e.g. bail at -50%, sized so a
real loss stays inside your risk budget, same discipline argument Tharp
makes for stock: a loss worse than your planned R is a discipline failure,
not the market's).

Portfolio heat (sum of risk-if-stopped across all open positions, as % of
equity) and a hard max-position-value cap both sit on top of the per-trade
risk math — on a small account either a tight-stop expensive stock or a
single options contract can R-size past what's sane for one name.

Source material: mph's own paraphrased Tharp position-sizing notes at
tharp/summaries/definitive-guide-position-sizing.md and
tharp/summaries/systems-development-workbook.md (same formulas already
ingested into Arya's knowledge base — this is the calculator that was never
built for it).

  python3 tools/phund_position_size.py stock --symbol SCHW --entry 108 --stop 104.50 \
      --netliq 1619 --risk-pct 2
  python3 tools/phund_position_size.py option --symbol RKLB --premium 2.80 \
      --netliq 1619 --risk-pct 2 --stop-loss-pct 50

A far-OTM option is often unsizeable at today's price (see above) but decays
fast — a resting limit order at the price it WOULD trade if the underlying
pulls back to a structural support level, same "buy the dip, not the pop"
logic as the stock entries. `project` estimates that price with Black-Scholes
off the contract's current IV, so you can find the entry (and date window)
where it's actually cheap enough to size properly instead of being either a
0-contract non-starter today or worthless mush by expiry:

  python3 tools/phund_position_size.py project --strike 85 --expiry 2026-10-16 \
      --iv 0.7544 --spot 60 --asof 2026-09-25
"""
import argparse
import math
import sys
from datetime import date


def _apply_caps(units, unit_cost, netliq, max_position_pct, cash_available):
    """Shared cap logic: risk-based `units` gets clipped by a max-position-value
    cap and/or actual settled cash (the Phund's real account is cash, no margin
    — buying power is bounded by cash on hand, which can be far below netliq
    once other positions are already holding capital). Returns (units, bind)
    where bind names whichever cap actually bit, or None if risk was already
    the tightest constraint."""
    bind = None
    if max_position_pct is not None:
        max_units = int((netliq * (max_position_pct / 100)) // unit_cost)
        if units > max_units:
            units, bind = max_units, f"{max_position_pct:.0f}% max-position-pct"
    if cash_available is not None:
        cash_units = int(cash_available // unit_cost)
        if units > cash_units:
            units, bind = cash_units, f"${cash_available:,.2f} cash available (cash account, no margin)"
    return units, bind


def size_stock(netliq, risk_pct, entry, stop, max_position_pct=None, cash_available=None):
    """Returns (risk_dollars, per_unit_risk, units, position_value, bind)."""
    per_unit_risk = entry - stop
    if per_unit_risk <= 0:
        raise ValueError("stop must be below entry (long-only sizing)")
    risk_dollars = netliq * (risk_pct / 100)
    units = int(risk_dollars // per_unit_risk)
    units, bind = _apply_caps(units, entry, netliq, max_position_pct, cash_available)
    return risk_dollars, per_unit_risk, units, units * entry, bind


def size_option(netliq, risk_pct, premium, stop_loss_pct=100.0, max_position_pct=None, cash_available=None):
    """Long option, one contract = 100 shares. per_unit_risk is the $ actually
    at risk per contract given the chosen soft-stop (100% = full premium)."""
    if premium <= 0:
        raise ValueError("premium must be positive")
    per_contract_debit = premium * 100
    per_unit_risk = per_contract_debit * (stop_loss_pct / 100)
    risk_dollars = netliq * (risk_pct / 100)
    contracts = int(risk_dollars // per_unit_risk)
    contracts, bind = _apply_caps(contracts, per_contract_debit, netliq, max_position_pct, cash_available)
    return risk_dollars, per_unit_risk, contracts, contracts * per_contract_debit, bind


def bs_call_price(spot, strike, years_to_expiry, iv, r=0.04):
    """Black-Scholes call estimate. Ignores dividends (fine for RKLB/most of
    the Phund's non-dividend names) and assumes IV stays constant, which is
    the biggest simplification here — a real pullback into support usually
    comes with some IV expansion (fear), so this tends to UNDERSTATE the
    premium you'd actually see on a real dip, not overstate it."""
    if years_to_expiry <= 0:
        return max(spot - strike, 0.0)
    d1 = (math.log(spot / strike) + (r + iv ** 2 / 2) * years_to_expiry) / (iv * math.sqrt(years_to_expiry))
    d2 = d1 - iv * math.sqrt(years_to_expiry)
    N = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    return spot * N(d1) - strike * math.exp(-r * years_to_expiry) * N(d2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)

    st = sub.add_parser("stock")
    st.add_argument("--symbol", required=True)
    st.add_argument("--entry", type=float, required=True, help="planned limit entry price")
    st.add_argument("--stop", type=float, required=True, help="stop price (must be below entry)")
    st.add_argument("--netliq", type=float, required=True)
    st.add_argument("--risk-pct", type=float, default=2.0)
    st.add_argument("--heat-pct", type=float, default=5.0)
    st.add_argument("--max-position-pct", type=float, default=25.0)
    st.add_argument("--cash-available", type=float, default=None,
                     help="settled cash on hand (cash account, no margin — this can bind tighter "
                          "than the risk math if capital is already tied up in other positions)")
    st.add_argument("--flat-dollar", type=float, default=50.0, help="the old flat-size comparison")

    op = sub.add_parser("option")
    op.add_argument("--symbol", required=True)
    op.add_argument("--premium", type=float, required=True, help="mid/ask debit per share (contract = x100)")
    op.add_argument("--netliq", type=float, required=True)
    op.add_argument("--risk-pct", type=float, default=2.0)
    op.add_argument("--stop-loss-pct", type=float, default=100.0,
                     help="%% of premium you'll actually let it lose before you exit (default 100%% = full debit)")
    op.add_argument("--heat-pct", type=float, default=5.0)
    op.add_argument("--max-position-pct", type=float, default=25.0)
    op.add_argument("--cash-available", type=float, default=None,
                     help="settled cash on hand (cash account, no margin)")
    op.add_argument("--flat-dollar", type=float, default=50.0, help="the old flat-size comparison")

    pr = sub.add_parser("project", help="estimate a future/pullback option price via Black-Scholes")
    pr.add_argument("--strike", type=float, required=True)
    pr.add_argument("--expiry", required=True, help="contract expiry, YYYY-MM-DD")
    pr.add_argument("--iv", required=True,
                     help="implied vol as a decimal (e.g. 0.75), or a comma-separated list to sweep "
                          "(e.g. 0.65,0.80,1.00) — DO NOT just pass today's IV if it's near an "
                          "annual low/high; check ivRank first and sweep a realistic range instead "
                          "of pretending vol holds still through the move you're projecting")
    pr.add_argument("--spot", type=float, required=True, help="hypothetical underlying price on --asof")
    pr.add_argument("--asof", required=True, help="the date you're pricing the contract as of, YYYY-MM-DD")
    pr.add_argument("--rate", type=float, default=0.04, help="risk-free rate assumption (default 4%%)")

    args = ap.parse_args()

    if args.mode == "project":
        expiry = date.fromisoformat(args.expiry)
        asof = date.fromisoformat(args.asof)
        days_left = (expiry - asof).days
        if days_left < 0:
            print("error: --asof is after --expiry", file=sys.stderr)
            sys.exit(1)
        ivs = sorted(float(v) for v in args.iv.split(","))
        print(f"${args.strike:.0f}c exp {args.expiry}, spot ${args.spot:.2f} on {args.asof} "
              f"({days_left}d to expiry)")
        for iv in ivs:
            price = bs_call_price(args.spot, args.strike, days_left / 365, iv, args.rate)
            print(f"  IV {iv * 100:5.1f}%  ->  ${price:.2f}/share = ${price * 100:6.2f}/contract")
        if len(ivs) == 1:
            print("  (single IV point — if that's today's reading and it's near a 52-week high or "
                  "low, this projection is fragile; rerun with a comma-separated range instead)")
        return

    try:
        if args.mode == "stock":
            risk_dollars, per_unit_risk, units, position_value, bind = size_stock(
                args.netliq, args.risk_pct, args.entry, args.stop,
                args.max_position_pct, args.cash_available
            )
        else:
            risk_dollars, per_unit_risk, units, position_value, bind = size_option(
                args.netliq, args.risk_pct, args.premium, args.stop_loss_pct,
                args.max_position_pct, args.cash_available
            )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    unit_label = "shares" if args.mode == "stock" else "contracts"

    if units < 1:
        note = (f"${per_unit_risk:.2f}/share risk" if args.mode == "stock"
                 else f"one contract alone risks ${per_unit_risk:.2f} at your {args.stop_loss_pct:.0f}% stop-loss")
        print(f"{args.symbol}: R-based size rounds to 0 {unit_label} at {args.risk_pct:.1f}% risk "
              f"(${risk_dollars:.2f} risk budget, {note}). "
              f"Widen risk-pct, loosen the stop-loss%, or skip the trade — do NOT round up to 1 "
              f"just to have a position, that silently blows the risk budget.")
        sys.exit(0)

    print(f"{args.symbol} — R-based sizing ({args.mode})")
    if args.mode == "stock":
        print(f"  entry ${args.entry:.2f} / stop ${args.stop:.2f} -> R = ${per_unit_risk:.2f}/share")
    else:
        print(f"  premium ${args.premium:.2f}/sh (${per_unit_risk / (args.stop_loss_pct / 100):.2f} full debit/contract), "
              f"{args.stop_loss_pct:.0f}% stop-loss -> R = ${per_unit_risk:.2f}/contract")
    print(f"  risk budget: {args.risk_pct:.1f}% of ${args.netliq:,.2f} netliq = ${risk_dollars:.2f}")

    if bind:
        print(f"  size: {units} {unit_label} (${position_value:,.2f}, {position_value / args.netliq * 100:.1f}% of book) "
              f"— CAPPED by {bind}; uncapped R-math wanted more")
        print(f"  actual risk taken at this capped size: -${units * per_unit_risk:.2f} "
              f"(-{units * per_unit_risk / args.netliq * 100:.2f}% of book, below the {args.risk_pct:.1f}% budget)")
    else:
        print(f"  size: {units} {unit_label} (${position_value:,.2f}, {position_value / args.netliq * 100:.1f}% of book)")
        print(f"  worst case at planned exit: -${units * per_unit_risk:.2f} "
              f"(-1R, -{args.risk_pct:.1f}% of book by design)")

    print()
    old_units = args.flat_dollar / (args.entry if args.mode == "stock" else args.premium * 100)
    old_label = "shares" if args.mode == "stock" else "contracts"
    print(f"  vs. the old flat ${args.flat_dollar:.0f} rule: ~{old_units:.2f} {old_label} "
          f"(${args.flat_dollar:.2f}, {args.flat_dollar / args.netliq * 100:.2f}% of book, "
          f"risk undefined — no stop-linked size)")
    print()
    print(f"  portfolio heat: this trade alone uses {args.risk_pct:.1f}% of the "
          f"{args.heat_pct:.1f}% heat cap (single-position book — full cap available).")


if __name__ == "__main__":
    main()
