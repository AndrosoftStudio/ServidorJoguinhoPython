
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir --upgrade pip
EXPOSE 7777
ENV PORT=7777
CMD ["python", "server_main.py"]
