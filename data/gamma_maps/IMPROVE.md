# Tomorrow's Map: nightly improvement backlog

The 21:00 cron (`37c6eec1`) ships ONE improvement per night from this list (or one it
found in that night's run), announces it in the note's "What changed", and moves it
to Done with the date. Add new ideas to the bottom of Candidates as they come up.

Rules: never lower MIN_GRADED, never change the grader to make the record look better,
never undo a SKILL.md rule. If a change touches grading, say so in the changelog
plainly. Small and correct beats big and clever. Skipping a night is fine if nothing
on the list is safe to ship in ~20 minutes; say so in the thread.

## Candidates
- RANGE road is ungraded: the ledger `pin` is the API magnet, not the chart pin. Store the chart pin in the entry so RANGE can be scored.
- Report the non-round-level split (`record.nonRound`) in the thread every night, so we can see if gamma beats round numbers on non-round strikes before it is publishable.
- TradingView's flip disagrees with TDPro's by ~3 points. Log both in the ledger each night so the gap is measured, not guessed.
- Note caption: when the last session was graded, add one plain line on how last night's map did (hit/miss by level, on the close).
- Road weighting: track which road price took vs. which the map leaned toward, once there are 10+ live sessions.

## Done
- 2026-10-12: the note says the map has run since Sep 23 and the record restarted Oct 8 (it used to read "since day one").
