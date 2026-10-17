FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY livekit/requirements.txt /app/livekit/requirements.txt
RUN pip install --no-cache-dir -r /app/livekit/requirements.txt

# Persona + corpus are read at startup from the repo layout, so copy exactly those.
COPY agents/michael /app/agents/michael
COPY data/afterhour/mphinance.json /app/data/afterhour/mphinance.json
COPY articles /app/articles
COPY docs/articles /app/docs/articles
COPY recovery/district/meetings.md /app/recovery/district/meetings.md
COPY livekit/*.py /app/livekit/

# Pre-download inference/turn-detector model files so cold starts are fast.
RUN cd /app/livekit && python agent.py download-files || true

WORKDIR /app/livekit
CMD ["python", "agent.py", "start"]
