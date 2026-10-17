# Michael's protégé, as a phone line

A LiveKit voice agent that has read everything Michael published and quotes
him. It is not a clone and says so first on every call. The character lives in
[`agents/michael/`](../agents/michael/); this folder is the plumbing.

**Status: scaffolded, not yet run end to end.** The session that wrote this
could reach PyPI but not LiveKit, ElevenLabs, or Deepgram, so the code is
written against the installed `livekit-agents==1.8.8` API and import-checked,
and the retrieval, meeting parser, and persona loader have offline tests in
`tests/test_livekit_corpus.py`. The first real call happens on Venus with real
keys. Expect to touch the model strings once.

## What is in here

| File | Job |
|---|---|
| `agent.py` | The LiveKit agent. Loads the persona, wires STT, Claude, TTS, and the tools. |
| `persona.py` | Builds the system prompt from `SOUL.md` + `IDENTITY.md` + `USER.md` and appends spoken-mode rules. |
| `corpus.py` | BM25 search over the AfterHour archive and the Substack articles. Stdlib only. |
| `meetings.py` | Parses `recovery/district/meetings.md` and answers "next meeting." Stdlib only. |
| `sip/` | Dispatch rule (and an optional bring-your-own-number trunk) for the LiveKit CLI. |
| `Dockerfile`, `docker-compose.yml` | Venus deploy, same pattern as alpha-momentum. |

## Tools the agent can call

- `search_michael(query, pure_only)`: three best-dated snippets. `pure_only` keeps to posts before 2026-01-31, the last zero-AI day per VOICE.md.
- `michael_on_ticker(ticker)`: his latest posts tagging a symbol.
- `next_meeting(city)`: next District 12 meetings from the scraped list.
- `crisis_resources()`: 988 and the SAMHSA line, read back plainly. SOUL.md boundary 3.
- Everything on the TDPro MCP, when `TDPRO_MCP_URL` is set.

## Run it

```bash
# 1. deps (Python 3.12)
python -m venv .venv && . .venv/bin/activate
pip install -r livekit/requirements.txt

# 2. keys, from VaultGuard
cp livekit/.env.example livekit/.env   # fill it in

# 3. local test with your mic, no room, no phone
cd livekit && python agent.py console

# 4. connect to your LiveKit Cloud project
python agent.py dev
```

`console` mode is the fastest way to hear whether the persona holds. Ask it
if it is Michael. Ask it about GLXY. Ask it something he never wrote about.
Those three answers tell you whether the soul is working before you spend a
phone minute.

## Phone number

1. LiveKit Cloud dashboard, Telephony, get the one free US number on the Build
   tier. That creates the inbound trunk for you. Copy its trunk id.
2. Put the trunk id in `sip/dispatch-rule.json` and create the rule:

   ```bash
   lk sip dispatch create sip/dispatch-rule.json
   ```

   Explicit dispatch by `agent_name` is what LiveKit recommends for SIP. If
   your `lk` version wants the file wrapped in a `dispatch_rule` key, wrap it.
3. Only if you bring your own carrier (Twilio, Telnyx): edit
   `sip/inbound-trunk.json` and run `lk sip inbound create sip/inbound-trunk.json`
   first, then use that trunk id in step 2.

## Deploy to Venus

```bash
rsync -avz --exclude='.git' --exclude='.venv' ./ venus:/home/mph/mphinance/
ssh venus "cd /home/mph/mphinance && docker compose -f livekit/docker-compose.yml up -d --build"
```

## Cost, roughly

Build tier: one free number, about 1,000 agent minutes a month, a small
inference credit. Past that, the pricing calculator example lands near eight
cents a minute with STT, LLM, and TTS. Claude is billed to your Anthropic key
on top. Numbers from livekit.com/pricing as of October 2026; check the page.

## The rules that do not move

They are in [`agents/michael/SOUL.md`](../agents/michael/SOUL.md), section
"Boundaries." The code enforces the ones it can: the disclosure is the first
thing said and is not interruptible; there is no broker tool; the crisis tool
exists. The rest is the model following the soul, which is why you test it in
`console` mode before it gets a phone number.
