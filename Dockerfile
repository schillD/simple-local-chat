FROM node:16-alpine

# Install Python and required packages
RUN apk add --no-cache python3 py3-pip bash curl

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt /app/backend/
RUN pip3 install --no-cache-dir -r backend/requirements.txt

# Install frontend dependencies
COPY frontend/package.json frontend/package-lock.json* /app/frontend/
WORKDIR /app/frontend

# Install dependencies with legacy peer deps to avoid compatibility issues
RUN npm install --legacy-peer-deps

# Copy frontend code
COPY frontend/ /app/frontend/

# Copy backend code
COPY backend/ /app/backend/

# Create a start script for both services
COPY start.sh /app/
RUN chmod +x /app/start.sh

EXPOSE 8000 5173

WORKDIR /app

CMD ["/app/start.sh"]
