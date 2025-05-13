#!/bin/bash

# Disable the 'exit on error' behavior to allow more detailed error reporting
set +e

# Create a function to handle signals
function cleanup() {
    echo "Shutting down services..."
    pkill -f "uvicorn" || true
    pkill -f "node" || true
    exit 0
}

# Trap SIGTERM and SIGINT
trap cleanup SIGTERM SIGINT

# Start the health check service
echo "=== Starting health check service ==="
cd /app/backend
python3 -m uvicorn health:app --host 0.0.0.0 --port 8080 &
HEALTH_PID=$!

# Wait for health service to start
sleep 3
if ! kill -0 $HEALTH_PID 2>/dev/null; then
    echo "!!! Health check service failed to start !!!"
else
    echo "✓ Health check service started successfully"
fi

# Start the main backend server
echo "=== Starting backend server ==="
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be available
echo "Waiting for backend to be available..."
MAX_TRIES=15
COUNT=0

while ! curl --output /dev/null --silent --head --fail http://localhost:8000/; do
    printf '.'
    sleep 1
    COUNT=$((COUNT+1))
    
    if [ $COUNT -ge $MAX_TRIES ]; then
        echo "\n!!! Backend failed to become available after $MAX_TRIES seconds !!!"
        break
    fi
    
    # Check if the process is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "\n!!! Backend process died unexpectedly !!!"
        exit 1
    fi
done

echo "\n✓ Backend is ready!"

# Start the frontend server
echo "=== Starting frontend server ==="
cd /app/frontend

# List package.json to debug
echo "==== Package.json contents ===="
cat package.json
echo "===============================\n"

# List installed packages
echo "==== Installed npm packages ===="
npm list --depth=0
echo "=================================\n"

# Serve using a simple http server instead of the dev server
echo "Starting static file server..."
npm run build

if [ ! -d "dist" ]; then
    echo "!!! Frontend build failed - dist directory not found !!!"
    # Fallback to dev server as last resort
    echo "Falling back to dev server..."
    npm run dev -- --host 0.0.0.0 &
else
    echo "✓ Frontend built successfully"
    # Install and use a simple http server
    cd dist
    python3 -m http.server 5173 &
    echo "✓ Static file server started on port 5173"
fi

echo "\nAll services started. Container is now running..."
echo "Access the app at http://localhost:5173"

# Keep container running
tail -f /dev/null
