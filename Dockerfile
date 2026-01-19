FROM python:3.10-slim

WORKDIR /app

COPY requirement.txt ./requirement.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir --prefer-binary --default-timeout=300 --retries 10 -r requirement.txt && \
    python -m spacy download en_core_web_sm

COPY . .

EXPOSE 8000
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]