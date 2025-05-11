FROM python:3.11-slim




RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl build-essential libsndfile1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root

COPY . .

ENV PYTHONPATH="${PYTHONPATH}:/app/src"

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "src.fastapi_google_live.main:app", "--host", "0.0.0.0", "--port", "8000"]

