FROM ghcr.io/astral-sh/uv:python3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING='utf-8'

COPY . /app

WORKDIR /app

RUN uv sync --locked

EXPOSE 8008

CMD ["uv", "run", "python", "main.py"]
