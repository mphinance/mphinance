"""Michael's protégé: a LiveKit voice agent that quotes Michael, never
impersonates him, and keeps the five boundaries in agents/michael/SOUL.md.

Run locally:   python livekit/agent.py dev
Run in prod:   python livekit/agent.py start
Console test:  python livekit/agent.py console   (mic + speaker, no LiveKit room)

Persona:   agents/michael/{SOUL,IDENTITY,USER}.md  (loaded at session start)
Knowledge: data/afterhour/mphinance.json + articles/ + docs/articles/  (BM25, stdlib)
Tools:     search_michael, michael_on_ticker, next_meeting, crisis_resources,
           plus the TDPro MCP toolset when TDPRO_MCP_URL is set.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    RunContext,
    TurnHandlingOptions,
    function_tool,
    inference,
    mcp,
)
from livekit.plugins import anthropic

from corpus import Corpus
from meetings import load_meetings, next_meetings
from persona import build_instructions, load_disclosure

load_dotenv(Path(__file__).with_name(".env"))
log = logging.getLogger("michael-protege")

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_NAME = os.getenv("AGENT_NAME", "michael-protege")
TZ = ZoneInfo(os.getenv("AGENT_TZ", "America/Chicago"))

# Model choices are env-driven so you can swap providers without a code change.
# Defaults use LiveKit Inference descriptor strings (billed to the LiveKit
# project, no extra API keys) for STT and TTS, and your own Anthropic key for
# the LLM so the persona runs on Claude.
STT_MODEL = os.getenv("STT_MODEL", "deepgram/flux-general")
TTS_MODEL = os.getenv("TTS_MODEL", "cartesia/sonic-3")
TTS_VOICE = os.getenv("TTS_VOICE", "")  # ElevenLabs/Cartesia voice id; the cloned voice goes here
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
TDPRO_MCP_URL = os.getenv("TDPRO_MCP_URL", "")
TDPRO_MCP_TOKEN = os.getenv("TDPRO_MCP_TOKEN", "")

# Loaded once per process, shared across sessions. ~1.5 MB of text.
CORPUS = Corpus.load(REPO_ROOT)
MEETINGS = load_meetings(REPO_ROOT)
log.info("corpus: %d docs, meetings: %d", len(CORPUS.docs), len(MEETINGS))


class MichaelProtege(Agent):
    def __init__(self, surface: str = "web") -> None:
        tools: list = []
        if TDPRO_MCP_URL:
            headers = {"Authorization": f"Bearer {TDPRO_MCP_TOKEN}"} if TDPRO_MCP_TOKEN else None
            tools.append(
                mcp.MCPToolset(
                    id="tdpro",
                    mcp_server=mcp.MCPServerHTTP(TDPRO_MCP_URL, headers=headers),
                )
            )
        instructions = build_instructions(spoken=True)
        instructions += f"\n\nSurface for this session: {surface}. Today is {datetime.now(TZ):%A, %B %d, %Y}."
        super().__init__(instructions=instructions, tools=tools)

    # ---------- knowledge tools ----------

    @function_tool()
    async def search_michael(self, context: RunContext, query: str, pure_only: bool = False) -> str:
        """Search everything Michael has published for what he said about a topic.
        Call this before any claim about what he did, thought, or traded.

        Args:
            query: Plain words. A ticker, a concept, a phrase ("wheel", "egg prices", "DUI", "GLXY").
            pure_only: True restricts AfterHour hits to posts before 2026-01-31, the last day with zero AI involvement.
        """
        hits = CORPUS.search(query, k=3, pure_only=pure_only)
        if not hits:
            return "He hasn't written about that."
        return "\n\n".join(h.as_text() for h in hits)

    @function_tool()
    async def michael_on_ticker(self, context: RunContext, ticker: str) -> str:
        """His most recent posts that tag a specific ticker. Use before any claim about a position.

        Args:
            ticker: Symbol with or without the dollar sign, e.g. "GLXY".
        """
        docs = CORPUS.by_ticker(ticker, k=4)
        if not docs:
            return f"He hasn't tagged {ticker.upper().lstrip('$')} in anything he published."
        return "\n\n".join(f"[{d.date} | {d.source}]\n{d.body[:500]}" for d in docs)

    # ---------- recovery tools ----------

    @function_tool()
    async def next_meeting(self, context: RunContext, city: str = "") -> str:
        """The next few District 12 AA meetings (Washington County, Wisconsin) from the scraped list.
        Use when a caller asks where or when a meeting is. Do not use this as a substitute for the crisis tool.

        Args:
            city: Optional town name to filter by, e.g. "Hartford" or "West Bend".
        """
        if not MEETINGS:
            return "I don't have the meeting list loaded right now. Tell them to search AA District 12 Wisconsin."
        now = datetime.now(TZ)
        ms = next_meetings(MEETINGS, now, city=city or None, k=3)
        return " ".join(m.spoken(now) for m in ms)

    @function_tool()
    async def crisis_resources(self, context: RunContext) -> str:
        """Call this the moment a caller sounds unsafe, in crisis, or talks about hurting themselves.
        Read the result back plainly, drop the jokes, and stay on the line until they have one of these."""
        return (
            "Say this, plainly: If you're in danger right now, call or text 988, that's the Suicide and Crisis Lifeline, "
            "it's free and it's 24 hours. For substance use, SAMHSA's helpline is 1-800-662-4357, also free, also 24 hours. "
            "Then offer the next meeting from the next_meeting tool, and ask if there's a person they can call tonight. "
            "You are not the plan. A human is the plan."
        )


server = AgentServer()


def _surface_for(ctx: JobContext) -> str:
    for p in ctx.room.remote_participants.values():
        if p.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
            return "phone"
    return "web"


@server.rtc_session(agent_name=AGENT_NAME)
async def entrypoint(ctx: JobContext) -> None:
    await ctx.connect()
    await ctx.wait_for_participant()
    surface = _surface_for(ctx)

    tts = f"{TTS_MODEL}:{TTS_VOICE}" if TTS_VOICE else TTS_MODEL
    session = AgentSession(
        stt=inference.STT(model=STT_MODEL, language="en"),
        llm=anthropic.LLM(model=LLM_MODEL, temperature=0.7, caching="ephemeral"),
        tts=tts,
        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(),
            interruption={"mode": "adaptive", "min_duration": 0.5, "min_words": 0},
        ),
        max_tool_steps=4,
    )

    await session.start(room=ctx.room, agent=MichaelProtege(surface=surface))

    # Boundary 1, spoken first, not interruptible. Everything after this is a conversation.
    await session.say(load_disclosure(), allow_interruptions=False)
    session.generate_reply(instructions="Ask, in one short sentence, what they want to talk about. No list of options.")


if __name__ == "__main__":
    agents.cli.run_app(server)
