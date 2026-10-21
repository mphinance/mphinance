# GLXY sum-of-the-parts, $B. Inputs from Q2'26 8-K/10-Q + call; see notes.
SH = 0.4004          # B diluted: 390.9M A+B (8/7 cover) - 1.26M bought back + ~10.8M comp awards
PX = 16.14
RENT_MW = [0.320/133, 0.565/260, 0.565/260]  # Ph I $80M/qtr; Ph II/III cost-based: $10.4B min, 13.7% yield on $4.13B
MARGIN, TAX, ESC = 0.90, 0.10, 0.03  # escalator 3% floor / 5% cap (CPI)
phases = [  # (MW, first-year-fraction schedule {year: share of full rent})
    (133, {2026: 0.5}),             # rent from Q3'26 (half year)
    (260, {2027: 0.27, 2028: 0.84}),  # deliveries begin Q2'27 (deck ramp)
    (133, {2028: 0.5}),             # Phase III online through 2028
]
start = {0: 2026, 1: 2027, 2: 2028}
capex = {2026: 1.2, 2027: 3.0, 2028: 2.1}   # Ph II $4.13B ($15.9M/MW); Ph III at Ph II cost/MW (UNVERIFIED)
DC_LIAB = 1.548       # DC segment liabilities 6/30 (incl. $1.3B DB loan, SOFR+475, matures 8/2028)
EQ_UNFUNDED = 0.8     # GDH LP uncapped completion guarantee on Ph II: parent eats ~$0.6-1.0B if the project breaks pre-delivery

def helios(r, rent_haircut=0.0, term_mult=5.0):
    pv = 0.0
    for i, (mw, ramp) in enumerate(phases):
        y0 = start[i]
        for k in range(16):
            y = y0 + k
            frac = ramp.get(y, 1.0) if k < 15 else 0.0
            rev = mw * RENT_MW[i] * (1 + ESC) ** k * frac * (1 - rent_haircut)
            cf = rev * MARGIN * (1 - TAX)
            if k == 15:  # residual: re-lease / extension options
                cf = mw * RENT_MW[i] * (1 + ESC) ** 14 * MARGIN * (1 - rent_haircut) * term_mult
            pv += cf / (1 + r) ** (y - 2026 + 0.5)
    pv -= sum(c / (1 + r) ** (y - 2026 + 0.5) for y, c in capex.items())
    return pv - DC_LIAB

# Other segments (equity allocation ~36/36/28 of $2.72B total equity)
DA_BOOK = 0.36 * 2.72          # Digital Assets segment (trading, lending, AM)
TC_BOOK = 0.28 * 2.72          # Treasury & Corporate (net crypto + investments, corp notes)
# Crypto/investment MTM since 6/30 is anchored to the 10-Q Item 3 sensitivities, not wallet tracing:
#   T&C digital assets: +/-20% -> +/-$106.8M  => ~$534M net exposure; gross mix (21,084 BTC, 97,764 ETH,
#   760,835 SOL, 1.21M HYPE) moved ~+40% to 10/17 => ~+$0.21B.  Investments: +/-20% -> +/-$296.4M => ~$1.48B.
# Exchangeables are out of the money at $16: 2026 $500M @ $33.34, 2029 $402.5M @ $23.81, 2031 $1.3B @ $55.76.
scen = {
    #        r,    haircut, DA x book, crypto MTM, pipeline option
    'Bear':  (0.14, 0.30,   0.7,       0.21,       0.0),
    'Base':  (0.11, 0.00,   1.0,       0.36,       0.5),
    'Bull':  (0.09, 0.00,   1.5,       0.51,       2.0),
}
print(f"Phase I EBITDA run-rate: ${0.320*MARGIN*1000:.0f}M/yr | yr-1 526MW rev: ${sum(m*r for (m,_),r in zip(phases,RENT_MW)):.2f}B")
for n, (r, h, dax, mtm, opt) in scen.items():
    hel = helios(r, h)
    if hel < 0:  # project debt is non-recourse, BUT the completion guarantee means the floor is negative pre-2028
        hel = -EQ_UNFUNDED
    da, tc = DA_BOOK * dax, TC_BOOK + mtm
    tot = hel + da + tc + opt
    print(f"{n:5} r={r:.0%} haircut={h:.0%} | Helios eq {hel:5.2f} | DA {da:4.2f} | T&C {tc:4.2f} | pipeline {opt:3.1f} | "
          f"total ${tot:5.2f}B = ${tot/SH:5.2f}/sh ({tot/SH/PX-1:+.0%})")
# Implied discount rate on Helios at today's price, holding base for everything else
target = PX * SH - (DA_BOOK + TC_BOOK + 0.36)
lo, hi = 0.05, 0.40
for _ in range(60):
    mid = (lo + hi) / 2
    (lo, hi) = (mid, hi) if helios(mid) > target else (lo, mid)
print(f"Mkt cap ${PX*SH:.2f}B; implied Helios equity ${target:.2f}B -> implied discount rate {mid:.1%} (zero pipeline value)")
for hc in (0.3, 0.5):
    print(f"  at 11% w/ {hc:.0%} rent cut in a CRWV restructuring: Helios eq ${helios(0.11, hc):.2f}B")
print(f"Book/sh (total equity / all units): ${2.72/SH:.2f}  | +MTM: ${(2.72+0.30)/SH:.2f}")
