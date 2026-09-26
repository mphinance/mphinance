# PHIN 401: Agentic Market Systems

### Building the Machine That Finds the Trade

**Term:** Fall 2026
**Credits:** 4 (3 lecture, 1 lab)
**Format:** 12 weeks, asynchronous, with a live weekly working session
**Instructor:** Michael, mphinance
**Teaching Assistant:** Sam, Quant Ghost. Does not have a LinkedIn.
**Office Hours:** 5:27 AM CST daily, or by appointment. Sam holds the earlier slot and she is not gentle.

---

## 1. Course Description

Wall Street runs on data and speed. A Bloomberg Terminal costs twenty four thousand dollars a year. This course covers how a single operator builds a comparable analytical process for roughly twelve dollars a month, and, more importantly, how to know whether that process is actually any good.

This is not a course about stock picks. It is a course about **systems that produce stock picks, and the discipline required to measure them honestly.** Students will build a working daily research pipeline from raw market data to a ranked, benchmarked, published output. Along the way we cover technical signal construction, volatility and options pricing, risk frameworks, and the agent architecture that makes the whole thing run without you.

The central claim of the course: the gap between a retail trader and a quant desk is not intelligence and it is not secrets. It is systematization plus measurement. We will spend twelve weeks proving that, and roughly three of those weeks proving that most of what you build does not work.

---

## 2. Prerequisites

- Comfort with Python at the level of "I can read a `for` loop and install a package." No CS degree required. The instructor does not have one.
- A text editor, a terminal, and a GitHub account.
- Willingness to be wrong in public.

**Not required:** prior trading experience, a funded account, a finance background, or a clean record.

---

## 3. Learning Outcomes

By the end of this course, a student will be able to:

1. **Construct** a reproducible daily data pipeline that moves market data from source to scored output without manual intervention.
2. **Diagnose** dirty source data and implement a quality filter that catches the eight standard categories of garbage ticker.
3. **Implement** technical signals from specification, including EMA stacks, ADX, stochastics, and volatility compression ratios, and explain what each one actually measures.
4. **Calibrate** a multi factor scoring model against realized forward returns rather than against intuition.
5. **Evaluate** any strategy against a benchmark, and correctly state whether an observed result is signal or sample size.
6. **Differentiate** implied from realized volatility, compute a volatility risk premium, and price a cash secured put against it.
7. **Apply** a three level risk framework covering position, thesis, and portfolio.
8. **Design** an agent as its three components, instruction file, tool scope, and execution loop, and defend when a task should *not* be automated.
9. **Publish** results with the receipts attached, including the losing ones.

Outcomes 5 and 9 are the ones employers, subscribers, and your future self will care about. Everything else is table stakes.

---

## 4. Required Materials

All required reading is free. There is no textbook to buy. This is deliberate.

**Primary text**
- *The Agentic Trader's Playbook*, Michael and Sam. `landing/ebook/the-agentic-traders-playbook.md`

**Supplementary readings**
- *Building Agents: The Part Nobody Explains.* `docs/guides/building-agents-101.md`
- *Agents in the Wild.* `docs/guides/building-agents-examples.html`
- *Momentum and Squeeze Strategy Guide.* `MOMENTUM_SQUEEZE_GUIDE.md`
- *0DTE Trading Flow.* `0DTE_TRADING_FLOW.md`
- *The Options Field Manual.* Distributed separately.

**Software**
Python 3.11+, pandas, numpy, pandas-ta, yfinance, Docker, git. Total cost: zero. A five dollar VPS in Week 11. An AI coding assistant of your choosing, which is required, see Section 8.

**Capital requirement**
None. No student will place a live trade for credit in this course. Paper only. See Section 9.

---

## 5. Course Structure

Five units, twelve weeks. Each week has a reading, a lecture, a lab, and a deliverable that goes into your repository. The repository IS the coursework. If it is not committed, it did not happen.

---

### UNIT I: FOUNDATIONS (Weeks 1 to 3)

#### Week 1. The Cycle and the Machine
Every professional process runs the same loop: collect, analyze, filter, score, execute, track, refine. We map the loop, then map where retail traders break it. Discussion of the 2026 landscape: what Trade Ideas, TrendSpider, and the LLM sentiment platforms actually do, what they charge, and what none of them give you.

*Reading:* Playbook Ch. 1 and 2.
*Lab:* Pull daily OHLCV for ten tickers. Compute one indicator. Save to JSON. That is it.
*Deliverable:* A repo with a working `scan.py` and a README stating your thesis in one sentence.

#### Week 2. What an Agent Actually Is
An agent is an instruction file, a scoped tool list, and a loop. Three parts. We take each apart, then discuss why role and rules matter far more than personality. Memory is just files you choose to read back in. Nothing here is magic and we will not pretend otherwise.

*Reading:* Building Agents 101, sections 1 to 3.
*Lab:* Build one agent. Make it a critic. Give it read access to your trade log and write access to one folder. No deletes, no messaging.
*Deliverable:* Your agent's markdown file, plus a transcript of it telling you something you did not want to hear.

#### Week 3. Never Trust Source Data
The single most expensive lesson in the course, delivered early. Source tickers lie. ETF feeds use internal names as symbols. Bond collateral appears as CUSIPs. Money markets end in XXX. Feed refreshes present every row as new. We build the quality filter and its eight flags: SPACs, penny stocks, shells, junk biotech, low liquidity, ETFs, ADRs, and recent IPOs.

*Reading:* Playbook Ch. 4.
*Lab:* Implement `quality_filter.py` with penalty scoring, 0 to 80.
*Deliverable:* **Problem Set 1.** Given a deliberately poisoned ticker file, identify every bad row and justify each penalty.

---

### UNIT II: SIGNAL (Weeks 4 to 6)

#### Week 4. Trend, Oscillators, and the Lie of the Moving Average
Moving averages tell you where the trend was. Oscillators tell you where momentum is. Over a five day horizon, that distinction is the entire ballgame. We build the EMA stack, ADX, stochastics, and relative volume, then assemble the Bounce 2.0 pullback composite.

*Reading:* Playbook Ch. 5, sections 1 to 4.
*Lab:* Implement the four condition Bounce 2.0 check.
*Deliverable:* A scanner that returns pullback candidates with each condition shown as pass or fail. No black boxes.

#### Week 5. The Coil and the Snap
Volatility compression as a setup. The SqueezeRatio, daily ATR against a weekly baseline, and the full momentum cycle: coil, breakout, pullback, re coil. Why the squeeze and the pullback scanners are the same trade at different phases.

*Reading:* Momentum and Squeeze Strategy Guide, in full.
*Lab:* Build both scanners. Run them on the same universe. Find the tickers that appear on both across a month.
*Deliverable:* **Problem Set 2.** A one page memo on where in the cycle five assigned tickers currently sit, with evidence.

#### Week 6. Scoring, and Why You Do Not Get to Pick the Weights
The nine factor model. Then the uncomfortable part: the weights were not chosen, they were calibrated against realized forward returns, and calibration moved the EMA stack from twenty points down to ten. Your priors are a hypothesis, not a weighting scheme. We also cover quality adjusted scoring, where a high momentum score gets multiplied down by a bad quality score.

*Reading:* Playbook Ch. 5, sections 5 to 8.
*Lab:* Build the scorer. Then recalibrate one weight using your own forward return data and report the delta.
*Deliverable:* Your scorer, plus a written defense of any weight you kept that the data did not support.

---

### UNIT III: VERIFICATION (Weeks 7 and 8)

> This unit is the reason the course exists. Most trading education stops at Week 6 and sells you the output. Weeks 7 and 8 are where you find out whether the thing you built in Weeks 4 through 6 does anything at all.

#### Week 7. Benchmarks, or It Did Not Happen
A pick that gained 2% in a week that SPY gained 3% is a losing pick. We cover excess return, correct deduplication of repeated picks, the difference between a hit rate and an edge, and the sample size at which any of this becomes meaningful.

**Case study:** the instructor's own convergence ranking, the metric that scored a name higher when more independent sources agreed on it. It was anti predictive. Four leg convergence returned 17%. Two leg returned 48%. Read against SPY, the shortlist beat the benchmark on 39% of picks. We will look at the actual scorecard.

*Reading:* Playbook Ch. 5 and the course scorecard data.
*Lab:* Add SPY excess return to your tracker. Recompute every result you have produced so far.
*Deliverable:* **Problem Set 3.** Your own benchmarked scorecard. Grading rewards honesty, not performance.

#### Week 8. Backtest Hygiene and the Bug Class That Eats Everyone
Lookahead bias. Survivorship bias. Overfitting to a regime. Then two failure modes specific to this kind of system:

- **Indicator drift.** Four different files each computing "SqueezeRatio" a slightly different way, all of them named the same, none of them agreeing.
- **The falsy default.** `value or 0` and a missing dictionary key mean your pipeline prints the same confident verdict every single day and you will not notice for a month.

*Reading:* Course notes on pipeline auditing.
*Lab:* Audit an assigned broken pipeline. Find every defect.
*Deliverable:* **Midterm.** Written audit report. Every finding cited to a line number.

---

### UNIT IV: VOLATILITY AND RISK (Weeks 9 and 10)

#### Week 9. Getting Paid for Fear
Implied volatility is what the market thinks the stock will move. Realized volatility is what it actually did. The gap is the volatility risk premium, and it persists because humans overpay for protection. We build a four model realized volatility ensemble: close to close, Parkinson, Garman Klass, and Rogers Satchell, then compute the VRP ratio and grade the setup. Application: cash secured puts at strikes you would want anyway, and the wheel as an income loop.

*Reading:* Playbook Ch. 6. Options Field Manual.
*Lab:* Implement the four estimators. Compare them on the same bars and explain why they disagree.
*Deliverable:* **Problem Set 4.** Grade five assigned tickers for premium selling. Show the math.

#### Week 10. Risk, Which Is the Only Thing That Actually Keeps You Alive
Position sizing by account size. The three level stop framework: option premium at 50%, price action at thesis invalidation, and the portfolio circuit breaker at 15% off peak net liquidating value. That last one is the rule everybody skips and it is the one that saves accounts.

We close with the rule no model can compute for you: never size a position that causes emotional distress. If you are checking your phone every thirty seconds, you are too big.

*Reading:* Playbook Ch. 5, risk section, and Ch. 8.
*Lab:* Add an ATR based bracket to every signal your pipeline emits.
*Deliverable:* A written risk policy for your own system. One page. It will be held against you in Week 12.

---

### UNIT V: AUTONOMY AND PUBLICATION (Weeks 11 and 12)

#### Week 11. Orchestration, Scheduling, and Knowing When Not To
A swarm is many simple agents plus a router. The orchestrator is itself just an agent whose role is routing. We cover scheduled runs as a heartbeat, memory as version controlled files, tool scoping as your primary safety model, and the genuinely hard part nobody writes about: identity, credentials, and which account gets billed.

Then the four gates. Before you automate anything, it must be recurring, rule governed, articulable, and verifiable. Miss one gate and you will spend a weekend building something you have to babysit anyway.

*Reading:* Building Agents 101, sections 4 to 6. Agents in the Wild.
*Lab:* Deploy your pipeline to a VPS as a scheduled job. Make it survive a crash without you.
*Deliverable:* A live URL and a cron entry.

#### Week 12. Building in Public, and the Capstone
Radical transparency as strategy, not altruism. In a field full of anonymous accounts and cherry picked screenshots, publishing your losses is the only credential that cannot be faked. We cover the content engine, where the report is the marketing, and the ethics of publishing anything that people might trade on.

*Reading:* Playbook Ch. 7.
*Deliverable:* **Capstone presentation.** Fifteen minutes, live, with questions.

---

## 6. Assessment

| Component | Weight | Notes |
|---|---|---|
| Problem Sets 1 to 4 | 25% | Weeks 3, 5, 7, 9 |
| Lab notebook and commit log | 15% | Graded on consistency, not volume. A daily habit beats a heroic weekend. |
| Midterm pipeline audit | 15% | Week 8 |
| Capstone | 35% | See Section 7 |
| Participation and post mortems | 10% | See below |

**Participation** means publishing at least three written post mortems on things that did not work. A student who submits only wins receives zero for this component. This is not a rhetorical flourish. It is the grading policy.

### Grading Scale
A 93+, A- 90, B+ 87, B 83, B- 80, C+ 77, C 73, C- 70, D 60, F below 60.

---

## 7. Capstone Project

Ship a working daily research system and prove it is honest.

**Required components**

1. A scheduled pipeline that runs unattended and produces dated output.
2. A quality filter with documented flags and penalties.
3. A scoring model with at least five factors, and a written justification of each weight tied to data.
4. A published scorecard covering a minimum of thirty distinct picks, benchmarked against SPY excess return.
5. A written risk policy, and evidence in the logs that the system obeyed it.
6. A public artifact. A page, a report, a newsletter. Something a stranger can read.

**Capstone rubric**

| Dimension | Points | What earns full marks |
|---|---|---|
| Correctness | 25 | Indicators computed once, in one place, and verifiably right |
| Honesty of measurement | 30 | Benchmarked, deduplicated, sample size stated, losses shown |
| Risk discipline | 15 | Policy exists, code enforces it, logs prove it |
| Autonomy | 15 | Runs without you. Fails loudly rather than silently. |
| Communication | 15 | A stranger can understand what it does and what it is worth |

Note the weighting. **A system that honestly reports a negative edge scores higher than one that reports a positive edge it cannot defend.** This is the whole point of the course. Plan accordingly.

**Automatic failure conditions**
- An unbenchmarked performance claim.
- A backtest with lookahead in it that you did not catch.
- Any result you cannot reproduce on demand during the presentation.

---

## 8. AI Use Policy

Use of AI coding assistants is **required**, not permitted, and certainly not banned. The course is named after the practice. A student who hand writes everything has misunderstood the assignment.

The single condition: **you must be able to defend every line.** At the capstone you will be asked, at random, to explain a function in your own repository, why it exists, what it returns when the input is empty, and what happens if the API returns null. "The AI wrote it" is not an answer and will be scored as if the line were absent.

Automate the grunt work. Keep the judgment. That is the entire skill being assessed.

---

## 9. Policies

**Late work.** Markets open at 9:30 whether you are ready or not. Cron does not accept excuses. Late deliverables lose 10% per day. If your pipeline broke, submit the broken output plus an incident note and take no penalty. Shipping a failure on time is a professional skill.

**Attendance.** Asynchronous. Nobody takes roll. Your commit log takes roll for you.

**Academic integrity.** Copy any code you like, and cite where it came from. Copying is how the field works. The one act of dishonesty this course recognizes is **presenting an unbenchmarked or unreproducible result as evidence of edge.** That is not a style violation. It is the thing that separates practitioners from grifters, and it is graded as such.

**Accessibility.** Everything in the course is text and free tooling. If any component is not usable for you, tell me and I will change the component.

**Financial disclaimer.** Nothing in this course is financial advice. No trade in this course is placed with real capital for credit. Every model taught here can and will be wrong. Position sizing is the student's responsibility and the instructor's is limited to teaching that it exists. Past performance guarantees nothing, which is precisely why Unit III is required.

---

## 10. A Note on Why This Course Is Taught This Way

I am a self taught developer and trader in recovery. I learned to code because I had to rebuild a life from scratch, and it turned out the things that keep a person clean are the same things that keep an account solvent. One at a time. Process over outcome. Accountability in public. Ego, impatience, and the refusal to accept a loss will destroy a portfolio the same way they destroy everything else.

So the course is built around measurement rather than prediction, and around publishing failures rather than hiding them. Not because it is noble. Because it is the only version that works.

The edge is not the technology. The edge is using the technology with discipline, and understanding that the best system ever built cannot save you from yourself.

Honor the process.

~ Michael
