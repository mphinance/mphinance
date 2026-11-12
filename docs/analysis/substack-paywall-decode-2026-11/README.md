# Substack paywall decode (2026-11-11)

Experiment: find all-paid finance Substacks (like Dick Capital), take each one's 5 latest paid posts, and reconstruct the paywalled part from PUBLIC evidence only: free preview, author's free posts/X/Notes, press coverage, and post-publish price action. No logins, archives, or leaked copies.

Pubs: Dick Capital, Adam Mancini (Trade Companion), Potential Multibaggers, Citrini Research, Michael Burry (Cassandra Unchained). One file each.

- `scan.py` scans the Substack finance leaderboard for each pub's paid-only share.
- `grab.py <host> <outdir>` pulls the archive, free previews, and word counts.

## Findings
- What the paywall really hides is the trade ticket (size, stops, weights) and the timing. The thesis is mostly readable in the free preview.
- Mancini's free recap quotes yesterday's paid levels word for word, so his paid content leaks one session late.
- Citrini previews name zero tickers; the names come out in the press on day +1.
- Citrini effect, 5 posts, basket return minus SPY: day 0 +1.4%, **day +1 +3.6% (5/5 positive)**, **day +2 −1.3% (5/5 negative)**. n=5 and selection-biased; expand to the full archive before claiming anything.
- Citrini State of the Themes (11/4) AI pairs: about −7.8% equal-weight in the first week (long NVDA / short AMD −30 pts).
