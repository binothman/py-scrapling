FROM python:3.13.0 AS builder
 
WORKDIR /app
 
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
 
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
# RUN python3 -m playwright install --with-deps chromium


# Stage 2
FROM python:3.13.0 AS runner
 
WORKDIR /app
 
COPY --from=builder /app/venv venv
COPY main.py main.py
 
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV FLASK_APP=app/main.py


EXPOSE 8080
 
CMD ["gunicorn", "--workers", "1", "main:app"]