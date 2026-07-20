# === Stage 1: Build Frontend ===
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# === Stage 2: Backend + Frontend ===
FROM python:3.11-alpine
WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev curl

# Install Python deps
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code into /app/backend/
COPY backend/ ./backend/

# Copy frontend build into /app/frontend/dist/
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Create data dir
RUN mkdir -p /app/data

EXPOSE 6066

WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6066"]
