# Fantasy autopilot post: fact sheet

Numbers only, no prose. Every figure was pulled from the Sleeper API on 2026-10-08.
League: All Elite Dynasty, 12-team superflex dynasty, PPR. Michael = VictoriousSecret22.
Mikey = WhoDatBayouBoys.

How the stats are measured
- **Lineup efficiency** = points actually scored ÷ the best lineup possible from that week's roster.
  Regular season only, recomputed from weekly box scores.
- **All-play** = your record if you played every team every week. "Luck" = actual wins minus all-play expected wins.

## The league's first two champions
| Season | Champ | Runner-up |
|---|---|---|
| 2022 | **Mikey** | bxphil |
| 2023 | **Michael** | Big_daddy_Phil |
| 2024 | eugene123412 | phallinan |
| 2025 | brp72 | phallinan |

## Michael by season
| Season | Record | Efficiency (league rank of 12) | Bench pts | Perfect-lineup record | Luck | FAAB |
|---|---|---|---|---|---|---|
| 2022 | 6-8 | 92.2% (**1st**) | 164 | 8-6 | -1.2 | $105 |
| 2023 | 9-5 **champ** | 88.9% (4th) | 278 | 12-2 | -1.8 | $189 |
| 2024 | 6-8 | 89.4% (4th) | 236 | 8-6 | -1.8 | $158 |
| 2025 | 4-10 | 80.7% (**12th, dead last**) | 417 | 8-6 | -0.8 | **$20** |
| 2026 (wk 1-4) | 2-2 | 90.4% (**1st**) | 66 | 4-0 | -0.5 | $55 |

- 2025 = the checked-out season. Last in efficiency, $20 of $250 FAAB spent, 6 waiver claims all year.
  With perfect lineups that 4-10 was 8-6.
- 2026: went from last in efficiency to first. The bot took over 2026-08-27.
- **Honest part:** the 2026 perfect-lineup record is 4-0, but the actual record is 2-2.
  Weeks 2 and 3 were lost with points sitting on the bench (Tre Tucker 22.9 on the bench in wk 2;
  Meyers 19.4 and Gordon 14.5 in wk 3). That was the lineup bug fixed on 10/4: the bot was setting
  the roster's default starters, not the week's matchup lineup. So the bot cost him two games before it got fixed.
- His luck has been negative every single season, five for five.

## The 2025 draft (the one where the internet died)
Michael's 2025 rookie haul ranks **8th of 11** by current value (6,830).
mph's picks next to the best player taken in the next 6 picks:
- **1.05 Shedeur Sanders** (761) → **Tetairoa McMillan went at 1.06** (5,203). Shedeur had already slid to round 5
  of the NFL draft by then, so this looks like an autopick off stale pre-draft rankings. *Sleeper's API
  doesn't flag autopicks, so this is inference, not proof.*
- **3.10 Dillon Gabriel** (55) → **Harold Fannin went at 3.11** (3,193). Last month the bot tried to buy
  Fannin by trading away Derrick Henry and Jakobi Meyers. He was available one pick later, for free.
- The one hit: **2.09 Luther Burden** (3,211), now one of two "never trade" players.
- 2026 draft (bot era is close): 2nd-best haul in the league, 8,597, a hair behind Mikey's 8,603.

## Mikey material
- **Signed Tom Brady off waivers on 2024-07-26.** Brady was 46, had been retired 18 months and was
  calling games for Fox. Kept him five days, then cut him for Mason Tipton. He'd also dropped Brady in March 2024,
  so this was at least his second stint. (JelloSubmarine also had him that spring. Two managers.)
- **Won the 2022 title ranked 7th in lineup efficiency**, with +1.5 wins of luck and an empty starting slot in week 5.
- 2023 week 13: three starters scored zero in the same week (McLaurin, Noah Brown, Justin Watson).
  Watson and Brown each laid two zeros that season.
- 2024: started a kicker who scored zero **three times** (Zuerlein, Lutz, Grupe).
- **2026: 3-1 with the 10th-best points in the league.** All-play says he should have 1.5 wins: +1.5 of pure luck,
  the 2nd-luckiest in the league. 9th in efficiency (81.0%). He started rookies Stribling and Loveland in week 1;
  both scored zero.
- Spends every FAAB dollar: $250/$250 in both 2024 and 2025. Paid $74 for Kareem Hunt (wk3 2024), and
  **$86 for Ryan Flournoy in week 14 of 2025** while sitting at 7-7.
- 4 of his 8 career trades are with Michael, all during the mid-May rookie draft, and all the same shape:
  Mikey ships depth (Perine, Musgrave, Zaccheaus, Sinnott and Horn), Michael pays in picks.
- Hoards WRs: first 5 rookie picks in 2026 were all WRs; he owns 10 WRs with real value and starts 3.
  His QBs in superflex: Darnold 29, Jones 29, Rodgers 42, Levis.
- But: 2022 champ, 2024 3rd place, 2026 rookie haul #1. He's good. That's why making fun of him is fun.

## Head to head
**Mikey leads 3-1 all-time.** 2022 wk 4 Mikey 164.7-120.4; 2023 wk 7 Mikey 167.3-124.1 (in Michael's
title year); 2024 wk 4 Michael 179.6-155.1; 2025 wk 10 Mikey 96.1-84.6, a 180-point game between two checked-out teams.
They haven't played yet in 2026.

## The AI-for-data-analysis angle
Everything above came from one prompt and about 20 minutes of the bot reading 5 seasons
of API data: lineup efficiency, all-play luck, draft regret, and the Brady transaction log.
The bot also produced a wrong lead before correcting itself: "May 15 is his trade day" was
really rookie-draft week. That's worth a line: the machine finds patterns, and someone still
has to ask why.
