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
- The RANGE wave is drawn around the pin even when the pin sits outside the ELSE band (tonight the pin 770 is near the band's low edge, 768). Check whether the pin should be clamped into the band or the band anchored on the pin.
- `brake` is only computed when `gate` exists, so a book with a long-gamma strike above spot but none heavy enough to be a ceiling yields no brake at all. Worth checking whether that is intended or an artifact of the gate-first ordering.
- Two of the last three sessions graded RANGE and the third was a trend day that missed both levels. Once there are 10 live sessions, check whether misses cluster on trend days, and whether `expected` (the typical-move yardstick) is too small after a gap.

- The DOWN road led with the put wall tonight because the book had no shelf and no cushion. That is the level SKILL.md says is a crowd, not a floor, and grading correctly does not score it, so the IF row quotes a number the record will never test. Worth deciding whether the caption should say that out loud.
- Three of the last four graded sessions had levels marked UNTESTED (2, 1, 2). If the levels the map names sit outside a typical day most nights, the band around spot may be too wide for the book being drawn.

- The UNTESTED rate is the thing to watch next: the 10-16 session graded 0/0 tested, meaning every level the map named was out of reach for the whole day. Count how often that happens; if it is common, the band around spot is drawing levels no session visits.
- The DOWN road's first waypoint and the RANGE pin can land on the same strike (tonight both 763), so the chart stacks "763 TRAPDOOR" and "763 PIN" with their notes as a four-line block. Readable tonight, but worth merging into one label when the strikes match.
- `triggerNote` fired on its first night. Track how often it fires: if it is most nights, the trigger-selection chain is picking levels too close to spot and the real fix is upstream of the caption.

## Done
- 2026-10-18: the chart and the note now flag when an IF trigger sits a rounding error from the close, or when the ELSE band is under half a typical day. The three roads are exhaustive but were presented as if they were comparable; tonight the DOWN trigger 763 sat 0.23 under a 763.23 close with a typical day of 11.01, so "IF it goes below 763" was already true at the bell and the 763-767 quiet range was the long shot, not the default. One amber line under the IF/ELSE block, plus `triggers`/`triggerNote` in the sidecar and a "Read the roads with this" line in the note. Caption and sidecar only; grading reads the named levels, never these triggers.
- 2026-10-16: two label fixes caught in tonight's render. The right-hand gutter is now sized from the last waypoint's actual tag and note instead of a flat 210px, so a long note ("31k calls, dealers buy into strength") no longer runs off the canvas. And the "beyond a typical day" band caption is deferred until the waypoint labels have claimed their rows: it tries the row above the dashed line, then the row below, and is dropped only if both are taken. Tonight it was drawn straight through the FLIP note. Caption/chart only; levels and grading untouched.
- 2026-10-14: the UP trigger now has the same named-level fallback chain as the DOWN side (brake, else ceiling, else accelerant, else the flip). With brake and gate both null it used to be null, so the IF row read "it goes higher" with no number and the ELSE band collapsed to ceil(spot). Tonight's book had brake and accel null and only the 780 gate standing between the map and that output. Also stopped the no-ceiling rule asserting "dealers brake" when there is no long-gamma strike above spot to brake at. Caption/band only; grading reads the named levels directly.
- 2026-10-14: the RANGE wave amplitude is capped by the pin's distance to the nearer band edge, not just half the band. Widening the band tonight made it swing a full typical day and draw outside its own box.
- 2026-10-14: the DOWN trigger is the first level the road actually names (shelf, else cushion, else put wall) instead of `Math.floor(spot)`. The old fallback printed "IF it goes below 778" with spot at 778.01 and squeezed the ELSE band to 778-780. Caption/band only; grading reads `e.shelf`/`e.cushion` directly and is untouched.
- 2026-10-14: the RANGE road is graded (`chartPin` in the ledger) and was already shipped; candidate removed.
- 2026-10-12: the ELSE band is now the gap between the two IF triggers, so the three roads are exhaustive and the band always contains spot. It used to come from the pin and the flip and excluded spot tonight.
- 2026-10-12: the note says the map has run since Sep 23 and the record restarted Oct 8 (it used to read "since day one").
