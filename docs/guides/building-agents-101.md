# Building Agents: The Part Nobody Explains

Everyone glosses over the basics and then acts like the whole thing is magic. It's not. Here is what an agent actually is, in plain language.

Here's the one sentence version, then we'll pull it apart:

**An agent is a text file of instructions, plus a list of tools it's allowed to use, running in a loop against a model.**

That's it. Three parts. The instructions, the tools, the loop. Learn those three and you can build anything.

---

## 1. The file IS the agent

At the base level, an agent is a markdown file. That file is called the **system prompt**. It's the first thing the model reads before it does anything, and it's the only thing that makes "the market analyst" different from "the bug hunter." Same model underneath. Different file in front of it.

What goes in the file:

- **Role.** The job. "You review Pine Script for correctness and math errors." One sentence, front and center.
- **Rules.** The guardrails. "Never suggest code you haven't read. Always cite the line number. If the math is wrong, say so before you say anything nice."
- **Personality.** The flavor. Blunt vs polite, terse vs chatty. This matters less than you'd think, which we'll get to.
- **Context.** What it needs to know to do the job. File paths, house style, the definition of "done."

Most people describe an agent as "rules and personality." I'd flip the weight: role first, rules second, personality a distant third. I don't care if an agent is charming. I care that the quant-verifier catches a division-by-zero before it ships. The role and the rules do the work. Personality is seasoning.

If you take one thing from this section: the role IS the prompt. There's no deeper layer hiding underneath.

One more thing while we're here: memory is just more files. When people say an agent "remembers," they mean it reads a file of past notes, a rubric, prior corrections, before it starts. Nothing magical. Same idea as the system prompt, one folder over. The model itself forgets everything between runs, so "memory" is really just what you choose to read back in.

---

## 2. Tools are how it touches the world

A model on its own can only produce text. It can't read your files, hit an API, or run code. **Tools** are what you hand it to reach outside the chat.

A tool is just a function with a name and a description. "read_file: give it a path, it returns the contents." "run_screener: give it a ticker, it returns the flow data." The model reads your descriptions, decides which one it needs, and calls it. You wire the actual code behind it. The description is doing real work here: a vague description means the model picks the wrong tool, so write it like you're explaining it to a new hire.

This is the difference between a chatbot and an agent. A chatbot talks. An agent talks, then *does*: reads the file, calls the API, writes the result, checks its own work. When Sam pulls live options data before answering, that's a tool call. When nyx edits a file in a repo, tool call.

The thing most people miss: you decide exactly which tools each agent gets. The release-captain can deploy. The design-critic cannot. You scope the tools to the role. That's most of your safety right there.

---

## 3. The loop is the engine

This is the part that isn't in the file and isn't a tool, and it's the piece people skip right over.

The agent runs in a **loop**:

1. Read everything so far (system prompt, the task, any tool results so far).
2. Decide the next move. Either answer, or call a tool.
3. If it called a tool, run the tool, feed the result back in.
4. Go to step 1. Repeat until the job's done.

That loop is what makes it feel alive. It's not one question, one answer. It's read, act, check, act again, until the thing is actually finished. You don't write the loop yourself for most setups. The framework (Claude Code, the SDK, whatever) runs it for you. But knowing it's there is the difference between "I typed a prompt" and "I built an agent."

---

## 4. One agent vs a swarm

The first time you see a full agent team it looks complicated. It looks complicated because it's *many* of the simple thing, not one complicated thing.

- **One agent** is one file, its tools, the loop.
- **A swarm** is many of those, plus one more piece: an **orchestrator** that decides which agent handles what and passes work between them.

The orchestrator is itself just another agent whose *role* is routing. "Read the task. If it's a math problem, hand it to quant-verifier. If it's a UI problem, hand it to design-critic. Collect their answers, stitch them together." Turtles all the way down, but every turtle is the same three parts: file, tools, loop.

Each cell in a team matrix like mine is one agent's file pointed at one job. It's not 16 different technologies. It's 16 markdown files and a router.

---

## 5. The genuinely hard part

The hardest part isn't any of the above. It's the piece you *don't* see in any tutorial: splitting the accounts.

Everything above runs on a model account. The moment you want:

- a **shared** agent (the team's, that everyone uses),
- talking to **your private** agent,
- talking to a **teammate's private** agent,

now you've got several accounts that need to cooperate without stepping on each other or billing the wrong card. That's not an "agent" problem. That's plumbing. Identity, credentials, who-pays, who's-allowed-to-talk-to-who. It's the boring infrastructure part, and it's 80% of why a real multi-agent setup takes real work while a single agent takes an afternoon.

So: building *an* agent is genuinely a couple hours once you get the three parts. Building a *network* of them across accounts is where the sweat is. The "more" you sense is there is real. It's wiring, not intelligence.

---

## 6. When to even build one

Before you build anything, run the job through four gates. Pass all four and it's worth automating. Miss one and you'll spend a weekend building something you have to babysit anyway.

1. Is the job **recurring**? You'll do it again and again.
2. Is it **rule-governed**? There's a right and wrong way, not pure taste.
3. Can you **articulate the criteria**? If you can't write down what "good" looks like, the agent can't either.
4. Is the output **verifiable**? You can check whether it actually did the job.

Pass all four, build it. Miss one, wait. The clean version of this test comes from Karo and Dheeraj Sharma at *Product with Attitude*, and their post on making your first agent a critic is worth 10 minutes: [How to build your first agent](https://karozieminski.substack.com/p/how-to-build-your-first-ai-agent). Their line sticks: agentize the tasks, not the craft, and keep the human decision where judgment actually matters.

---

## Start here (do this today)

Don't build the swarm. Build one agent and feel the loop. Make it a critic. It's the easiest first job and it teaches everything.

1. Write one markdown file. Role: "You review my trade ideas and tell me what's wrong before you tell me what's right." Add 3 rules. Skip personality for now.
2. Give it one tool and lock the permissions down. Let it **read** your trade log, and let it **write** only to a `reviews/` folder. No deletes, no sending messages. Read-only plus one write path is the entire safety model at this stage.
3. Run it. Ask it something. Watch it read the file, then answer.

Once that clicks, once you *see* it read, decide, act, the matrix stops looking scary. It's just that, sixteen times, with a router on top.

Build that one agent. The rest is just scale.

---

Want to see all of this running in a real setup? [Agents in the Wild](building-agents-examples.html) walks through my actual three-agent mesh: the real agent files, how they share one brain through a git repo, and the scheduled runs that give them a heartbeat.

~ Michael
