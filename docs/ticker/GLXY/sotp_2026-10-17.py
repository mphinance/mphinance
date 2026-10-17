# GLXY sum-of-the-parts, $B. Inputs from Q2'26 8-K/10-Q + call; see notes.
SH = 0.3914          # B shares: 194.8M Class A + 196.6M Class B (LP units)
PX = 16.14
RENT_MW = 0.320/133  # Phase I: ~$80M/qtr on 133 MW critical IT
MARGIN, TAX, ESC = 0.90, 0.10, 0.02
phases = [  # (MW, first-year-fraction schedule {year: share of full rent})
    (133, {2026: 0.5}),             # rent from Q3'26 (half year)
    (260, {2027: 0.25}),            # deliveries begin Q2'27
    (133, {2028: 0.5}),             # Phase III online through 2028
]
start = {0: 2026, 1: 2027, 2: 2028}
capex = {2026: 1.2, 2027: 3.0, 2028: 1.6}   # ~$5.8B left: Ph II ~$4.1B (3.507/0.85) + Ph III ~$2.1B, less spent
DC_LIAB = 1.548       # Data Centers segment liabilities at 6/30 (Ph I financing)

def helios(r, rent_haircut=0.0, term_mult=5.0):
    pv = 0.0
    for i, (mw, ramp) in enumerate(phases):
        y0 = start[i]
        for k in range(16):
            y = y0 + k
            frac = ramp.get(y, 1.0) if k < 15 else 0.0
            rev = mw * RENT_MW * (1 + ESC) ** k * frac * (1 - rent_haircut)
            cf = rev * MARGIN * (1 - TAX)
            if k == 15:  # residual: re-lease / extension options
                cf = mw * RENT_MW * (1 + ESC) ** 14 * MARGIN * (1 - rent_haircut) * term_mult
            pv += cf / (1 + r) ** (y - 2026 + 0.5)
    pv -= sum(c / (1 + r) ** (y - 2026 + 0.5) for y, c in capex.items())
    return pv - DC_LIAB

# Other segments (equity allocation ~36/36/28 of $2.72B total equity)
DA_BOOK = 0.36 * 2.72          # Digital Assets segment (trading, lending, AM)
TC_BOOK = 0.28 * 2.72          # Treasury & Corporate (net crypto + investments, corp notes)
scen = {
    #        r,    haircut, DA x book, crypto MTM, pipeline option
    'Bear':  (0.14, 0.30,   0.7,       0.20,       0.0),
    'Base':  (0.11, 0.00,   1.0,       0.30,       0.5),
    'Bull':  (0.09, 0.00,   1.5,       0.45,       2.0),
}
print(f"Phase I EBITDA run-rate: ${0.320*MARGIN*1000:.0f}M/yr | stabilized 526MW rev: ${526*RENT_MW:.2f}B")
for n, (r, h, dax, mtm, opt) in scen.items():
    hel = helios(r, h)
    da, tc = DA_BOOK * dax, TC_BOOK + mtm
    tot = hel + da + tc + opt
    print(f"{n:5} r={r:.0%} haircut={h:.0%} | Helios eq {hel:5.2f} | DA {da:4.2f} | T&C {tc:4.2f} | pipeline {opt:3.1f} | "
          f"total ${tot:5.2f}B = ${tot/SH:5.2f}/sh ({tot/SH/PX-1:+.0%})")
# Implied discount rate on Helios at today's price, holding base for everything else
target = PX * SH - (DA_BOOK + TC_BOOK + 0.30)
lo, hi = 0.05, 0.40
for _ in range(60):
    mid = (lo + hi) / 2
    (lo, hi) = (mid, hi) if helios(mid) > target else (lo, mid)
print(f"Mkt cap ${PX*SH:.2f}B; implied Helios equity ${target:.2f}B -> implied discount rate {mid:.1%} (zero pipeline value)")
for hc in (0.3, 0.5):
    print(f"  at 11% w/ {hc:.0%} rent cut in a CRWV restructuring: Helios eq ${helios(0.11, hc):.2f}B")
print(f"Book/sh (total equity / all units): ${2.72/SH:.2f}  | +MTM: ${(2.72+0.30)/SH:.2f}")
