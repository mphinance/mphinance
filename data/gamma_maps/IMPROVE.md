# Tomorrow's Map: nightly improvement backlog

The 21:00 cron (`37c6eec1`) ships ONE improvement per night from this list (or one it
found in that night's run), announces it in the note's "What changed", and moves it
to Done with the date. Add new ideas to the bottom of Candidates as they come up.

Rules: never lower MIN_GRADED, never change the grader to make the record look better,
never undo a SKILL.md rule. If a change touches grading, say so in the changelog
plainly. Small and correct beats big and clever. Skipping a night is fine if nothing
on the list is safe to ship in ~20 minutes; say so in the thread.

## Candidates
- Report the non-round-level split (`record.nonRound`) in the thread every night, so we can see if gamma beats round numbers on non-round strikes before it is publishable.
- TradingView's flip disagrees with TDPro's by ~3 points. Log both in the ledger each night so the gap is measured, not guessed.
- Note caption: when the last session was graded, add one plain line on how last night's map did (hit/miss by level, on the close).
- Road weighting: track which road price took vs. which the map leaned toward, once there are 10+ live sessions.
- The TraderMatrix port (`backend/src/services/share/tomorrowMap.ts`, other repo) now differs on the ELSE band. Sync it next time that repo is open.
- The DOWN road can now lead with the cushion or the put wall. Check the waypoint label does not collide with the road line when the trigger is also the first drawn dot.
- The UP trigger has the mirror of tonight's bug waiting in it: if `brake` and `gate` are both null, `upTrigger` is null and `rangeHi` falls back to the pin/flip. Give it the same named-level fallback chain.

## Done
- 2026-10-14: the RANGE wave amplitude is capped by the pin's distance to the nearer band edge, not just half the band. Widening the band tonight made it swing a full typical day and draw outside its own box.
- 2026-10-14: the DOWN trigger is the first level the road actually names (shelf, else cushion, else put wall) instead of `Math.floor(spot)`. The old fallback printed "IF it goes below 778" with spot at 778.01 and squeezed the ELSE band to 778-780. Caption/band only; grading reads `e.shelf`/`e.cushion` directly and is untouched.
- 2026-10-14: the RANGE road is graded (`chartPin` in the ledger) and was already shipped; candidate removed.
- 2026-10-12: the ELSE band is now the gap between the two IF triggers, so the three roads are exhaustive and the band always contains spot. It used to come from the pin and the flip and excluded spot tonight.
- 2026-10-12: the note says the map has run since Sep 23 and the record restarted Oct 8 (it used to read "since day one").
