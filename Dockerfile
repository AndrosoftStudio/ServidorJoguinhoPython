
# Minimal image for dedicated server
FROM python:3.11-slim
WORKDIR /app
COPY config.py common.py server.py ./
COPY DedicatedServer/server_main.py ./server_main.py
RUN pip install --no-cache-dir --upgrade pip
EXPOSE 7777
ENV PORT=7777
CMD ["python", "server_main.py"]
