# Stage 1: Builder
FROM python:3.13-alpine AS builder

WORKDIR /app

# تثبيت أدوات البناء الضرورية
RUN apk add --no-cache \
    build-base \
    python3-dev \
    libffi-dev \
    openssl-dev \
    bash \
    git \
    curl

RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Stage 2: Runner
FROM python:3.13-alpine AS runner

WORKDIR /app

COPY --from=builder /app/venv venv
COPY main.py main.py

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV FLASK_APP=main.py

EXPOSE 8080

CMD ["gunicorn", "--workers", "1", "main:app"]
