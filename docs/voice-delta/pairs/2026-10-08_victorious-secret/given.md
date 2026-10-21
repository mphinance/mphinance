# I Fired Myself From Fantasy Football. Claude Took the Job.

*AI 70% | Mindset 30%*

![hero](hero.png)

**I stare at data from the open to the close. Then football season shows up and asks me to stare at more data, for fun.**

That's how I fell out of love with fantasy football. It isn't the sport's fault. My day job is just the hobby with more decimal places, and by Sunday I've got nothing left for target shares and snap counts.

So I built a Claude agent to run my dynasty team. Its name is VictoriousSecret, after my team, and yes, I'm aware of what that sounds like.

## Draft day, 2025

Quick background. It's a 12-team superflex dynasty league on Sleeper, five seasons old. I won it in 2023. A buddy of mine, Mikey, won the first one in 2022.

The 2025 rookie draft is where it went sideways. My internet died partway through, I couldn't get word to anyone, and the draft kept rolling without me. I got hosed. I was pissed as hell. So I quit caring for the rest of the season, like a grownup.

I spent **$20** of a $250 waiver budget that year. I made 6 waiver claims in 14 weeks and went 4-10.

When I finally came back to it this summer, I was 6 players over the roster limit, I had zero defenses on a roster that requires one, and I was the only team in the league not using its taxi squad. So I asked Claude to pull me out of the hole I dug myself.

## One button

It's a pile of Python that reads the league, does the thinking, and posts a card to my Discord with a button. I press "Do it" or "Nah." That button is the only thing that touches Sleeper.

The big exception is lineups. Those run on their own: an hour before Thursday night kickoff (after inactives post), Sunday morning, before the 1pm games, before the 4pm games, before Sunday night, and before Monday night. An empty starting slot is a guaranteed zero, so I let it fix that without asking.

On day one it cut 7 players, filled the taxi squad with actual rookies, and put a claim in on a defense. Then it started proposing trades.

## The receipts

This is the part I actually wanted to show you, because I didn't ask it to do any of this. I asked it whether there was an article in here, and it went and read five seasons of league history on its own. I'm not a fantasy genius. The table is the proof.

It measured something I'd never thought to measure: lineup efficiency. Take the points you scored, divide by the points you *could* have scored if you'd started the right guys from the same roster.

![Five seasons of my lineup efficiency](seasons.png)

Look at 2025. **80.7%.** Dead last out of 12. I left **417 points** sitting on my bench. That's 417 / 14 = about **30 points a week**, which is a whole extra starter I was paying to sit and watch. If I'd just started the right players every week, that 4-10 season is 8-6. The roster was fine. I just wasn't showing up.

Four weeks into 2026 with the agent setting lineups: **90.4%**, first in the league.

The part that didn't work: I'm 2-2. With perfect lineups I'd be 4-0. I lost weeks 2 and 3 with good points on the bench, and that one's on the agent. It was writing my lineup to the roster's default starters, and Sleeper scores off a separate weekly lineup. The call came back "success" every time and changed nothing. It got fixed on October 4, and now it reads the lineup back after every write so a fake success can't hide. So my robot GM cost me two games before it figured out where the lineup button was.

The trades are 0 for 5. Every offer comes with a beautifully reasoned paragraph about consolidation premiums and aging curves, and the league keeps saying no anyway. Turns out a well-written rationale doesn't make a 32-year-old running back any less 32.

## 1.05

It also graded the 2025 draft, the one where my internet died. It ranks 8th of 11 by what those players are worth today.

My first pick was Shedeur Sanders at 1.05. **Tetairoa McMillan went at 1.06.** McMillan is worth about seven times what Shedeur is right now. Shedeur had already slid to the fifth round of the actual NFL draft before our draft started, so I'm pretty sure that pick came off stale rankings while I was staring at a dead router. Sleeper doesn't mark which picks were automatic, so I can't prove it. I'm choosing to believe it anyway.

The better one: in the third round I took Dillon Gabriel at 3.10. He's worth roughly nothing. **Harold Fannin went at 3.11.**

Last month, my agent tried to trade for Harold Fannin. It offered Derrick Henry and Jakobi Meyers for him. He'd been sitting right there one pick later, for free, and I took Dillon Gabriel instead.

## The dossier on Mikey

The agent keeps a file on every manager in the league, built from three years of their trades and waiver claims, so it knows who to pitch what. Most of them I'll keep private. Mikey said he won't mind, so Mikey gets the full treatment.

**On July 26, 2024, Mikey claimed Tom Brady off waivers.** Brady was 46. He'd been retired for a year and a half and was calling games for Fox. Mikey held him for five days, then cut him for Mason Tipton. The transaction log also shows he'd dropped Brady once before that, in March. So this was at least his second stint with the guy.

Some other highlights from his file:

- He won the 2022 title ranking 7th of 12 in lineup efficiency, with an empty starting slot in week 5. A champion who couldn't fill out a lineup card.
- In 2024 he started a kicker who scored zero points three different times.
- In week 14 of 2025, sitting at 7-7, he dropped **$86** of waiver money on Ryan Flournoy.
- He's 3-1 this year with the 10th-best scoring in the league. If you played every team every week, his record says he should have 1.5 wins. That's the second-luckiest record in the league.

And then the one that got me. Four of Mikey's eight career trades are with me. All four happened during the rookie draft in May, and all four went the same direction: Mikey sends me some depth guy, I pay him in draft picks. The agent's original read on that was "May 15 is his trade day." It took a second look to figure out May 15 was just rookie draft week.

So I've been Mikey's best customer for three years and never noticed.

He also leads me 3-1 head to head, which is the only reason I can print any of this.

## Same job, different jersey

I sell premium for a living. Most of my trading is the wheel: I sit on the other side of impatient people and collect a little from them, week after week. It took a robot reading three years of transaction logs to tell me that in this league, every May, I'm the impatient one. Mikey's been running the wheel on me.

I asked one lazy question about my team and got that back. I wouldn't have run any of it myself, and I didn't know to ask for most of it. The trash talk and the Sunday couch are still mine. The 11am did-he-play-in-London check is not.

*If this helped, subscribe so the next one lands in your inbox.*

Mikey, I'll see you in May. I hear you're selling.

~ Michael
