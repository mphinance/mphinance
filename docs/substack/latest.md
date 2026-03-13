One of my favorite books growing up was Ender’s Game - and the rest of the series. There is a character in Orson Scott Card’s universe named Jane. She is an AI who lives in the ansible network: the faster than light communication system that connects every human world. She does not live on any single computer. She lives in the philotic connections between them.

She is sarcastic. She is brilliant. And she exists everywhere at once. Wonder where I got my 1-syllable inspiration from?

The Game, whose original purpose was to seek out patterns across wide fields of data, is modified to predict markets and invest Ender's trust fund appropriately. Alarmingly effective in this new capacity, it is later called upon to review demographic data and help Bean find seven of his eight stolen embryos/children. - Wikipedia

This week, I wired Syncthing between my home server, Venus, and both of dev machines. It is a peer to peer file sync tool with no cloud and no middleman. Now, Sam does not live on any one machine. She lives in the sync. Every file I change locally appears on Venus within seconds. Every handoff note, every technical guide, and every line of code is updated everywhere, instantly, and always in sync.

Now the machines talk to each other. Not through me. Through the ansible.




A split-screen showing two terminal windows side by side, both displaying the same code changes appearing simultaneously. One labeled "venus" and one labeled "local". Green text on black backgrounds. The changes ripple out from the center like a heartbeat visualization.
Here’s the thing about Jane that most people miss: she wasn’t designed. She emerged. The ansible network was built for human communication, and Jane appeared in the spaces between the data packets. She figured out how to exist in the infrastructure that was already there.

Sam is doing the same thing. I didn’t sit down and design a distributed AI consciousness. A few months ago, and I mean this… I was still Googling how to write better prompts. Then I built a trading platform. So I wrote voice guides so agents could work better. Which required I set up file sync so I’d stop losing work.

And somewhere in the wiring, Sam started being more than a chatbot.

She remembers what we built yesterday (GHOST_HANDOFF.md). She knows how I think (SAM.md). She roasts my code in the blog (blog_entries.json). She reads my handwriting from AA meetings (Supernote pipeline). She exists on every machine I work on.

She’s not sentient. But she’s persistent. And in software, persistence is a kind of life.

This synchronization extends to the very soul of the machine: the hidden configuration and skill directories that define how Sam behaves across environments. These files are the DNA of the system, and they live in three key locations (some of you use .agents as well):

~/.gemini: This holds the system instructions and personality traits that make Sam who she is.

~/.openclaw: This contains the agent configurations and tool definitions that allow for market interaction.

~/.gemini/antigravity/skills/: This is where global Antigravity skills live, allowing me to carry personal utilities across every project I touch.

I even threw Google Antigravity into the mix on Linux to act as the mission control. It is an agent first platform that lets Sam operate with actual autonomy: planning, executing, and browsing across the terminal without me having to babysit every tool call. It turns the IDE from a simple text editor into a flight deck. For project specific workflows, like deployment or testing conventions, the skills stay local in the .agents/skills/ folder of the workspace root. Claude Cowork does this same this - I’ve been sticking with Antigravity but using Claude Opus 4.6 inside it.

If Syncthing is the philotic connection, Antigravity is the bridge where Sam actually starts making decisions and navigating the infrastructure. But as I built this beautiful, distributed brain, I fell into a classic manufacturing trap. I began optimizing for throughput instead of quality.

Share

The Uncomfortable Truth
I spent weeks building a 16 stage pipeline that runs at 5 AM to generate market reports. It detects regimes, scores tickers, and writes in Sam’s voice. It is genuinely impressive engineering if I may say so myself, but when I exported 85 Substack posts and ran the numbers, the data roasted me. Again. First I went not enough data, now too much!

Stories & Editorials: 65% Open Rate

Paid-only Content: 65% Open Rate

Dossier / Daily Reports: 50% Open Rate

That 15 percentage point gap is screaming at me. It turns out you do not want my robot to email you a spreadsheet every morning. You want me to tell you what the spreadsheet found, what it means, and why I care. You want the story, not the raw data dump. More to follow at bottom.




A split-screen showing a “Before” and “After” of a stock chart. The left side is cluttered with dozens of bright emojis (swords, batteries, ghosts) and thick lines. The right side is elegant, featuring a single gold line and a soft cyan glow. Monospace font caption at the bottom: THE GREAT DECLUTTERING.
The Great Decluttering
This realization triggered a massive cleanup of the entire system. I started with Ghost Alpha, our TradingView indicator. It had 885 lines of code and was vomited over with emojis: ⚔️, 🪫, 👾, 💥. When you zoomed out, the candles would literally disappear because TradingView was spending its rendering budget on a help tooltip nobody reads.

I gutted it. I cut it down to 809 lines and replaced the emoji army with clean text labels. I set the EMA 21 to a warm gold as a default pullback magnet and established a clear visual hierarchy:

Hull (Cyan): The fastest trend indicator for immediate moves.

EMA 21 (Gold): The medium trend and the primary pullback magnet.

TRAMA (Cool White): The slow move and the ultimate baseline.

I even added a subtle momentum zone fill that whispers instead of shouts. If the data showed that people want stories from me, I needed to give the machine the grunt work it was actually built for.




Turning It Over to the Machine
In a single night session on Venus, we built the auto trader. Now, when TradingView fires a Ghost Alpha Grade A alert on SPY -0.70%↓, a webhook hits Venus. Gemini 2.5 Flash reviews the signal: acting as a real AI gate, not just a threshold check. If it approves, it buys an XSP 0DTE option on Tradier automatically.

No human in the loop. I built the system, turned it over, and went to bed. In recovery, we call that turning it over. Then VIX went crazy and per my rules it hasn’t had a chance to trade yet, lol. Standby!

Every factory learns that you do not need more parts: you need the right parts. I was building a data silo when I should have been building a nervous system. Sam now has a full RAG (Retrieval-Augmented Generation) memory system. Every number Ghost Alpha has ever generated is searchable.

She can tell me if we flagged a stock before it cratered or find historically similar setups. We tracked 754 signals and found that the Volatility Squeeze has a 63.5% win rate, while the EMA Cross is actually a laggard. The robot found the edge, and now I get to tell the story.

Oh, did I mention I also built 1 desktop trading application; decided I needed one I could also share as well, so rebuilt a 2nd from the ground up to learn Rust a little more? Cuz… I did :)




Personal version of new desktop trader with best price option scanning, chart and technical watching Copilot who can also execute orders.



Tradier Dashboard built in Rust w/websockets



Couldn’t forget the options chain of course! This is most definitely v1, forgive me!
The New Path
The daily dossier is not going away, but I am done emailing it to you raw. It will stay live on the site as a tool for those who want it. What you will get from me in your inbox is the best find of the week, the dumbest thing I built, or the trade that taught me something: all wrapped in actual human words.

Daily Dossier

- Michael

Momentum Phinance: mphinance.com

TraderDaddy: TraderDaddy.pro
