# Wheel Strategy teardown: scrapped 2026-10-04

Tried to reverse-engineer wheelstrategy.substack.com's weekly 15 with the TraderMatrix
Blue-Chip Wheel preset. Dead: the original overlap claims were circular (pool built from his own
lists, strikes never predicted). Measured honestly it hit 18% of his September names and 3/15 on
the 10/04 post. The full teardown and old scripts are in git history (commit 596de195 and
earlier, before the scrap commit).

Kept: `data/his_lists.json`, his published picks for 19 weeks (Jun-Oct 2026; free 5 per week,
paid names only for Sept and 10/04, 10/04 paid names inferred from his text).

Worth borrowing from his method: hard "expires before earnings" rule, 12+ names with max 2 per
ticker, calm low-IV-percentile names, ~5-8% cushion at ~25-46 DTE, ETFs allowed.
