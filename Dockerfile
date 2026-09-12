# Small, standard Python base image
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (separate layer so Docker can cache this step
# and skip reinstalling everything just because you changed one .py file)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the actual application code
COPY . .

# Render (and most container hosts) inject the port to listen on via $PORT.
# Locally, default to 8000 if $PORT isn't set.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]
