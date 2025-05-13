![image](https://github.com/user-attachments/assets/5b3b7dc5-3250-45e5-859c-c3acbdfe4dd9)

# Simple Chat Application

A real-time chat application that allows users in the same network to communicate through a modern interface.

## Features
- Random nickname generation on entry
- Real-time user presence detection
- Direct messaging between users
- No database required (temporary chats)
- Minimal setup needed

## Technology Stack
- **Backend**: Python FastAPI
- **Frontend**: Svelte
- **Real-time Communication**: WebSockets

## Project Structure
```
simple-chat/
├── backend/           # FastAPI backend
│   ├── main.py       # Main application file
│   └── requirements.txt
└── frontend/         # Svelte frontend
    ├── src/
    │   ├── components/
    │   │   ├── UserList.svelte   # User list component
    │   │   └── ChatWindow.svelte # Chat interface component
    │   ├── App.svelte
    │   ├── main.js
    │   └── app.css
    ├── public/
    ├── package.json
    └── vite.config.js
```

## Installation

### Backend Setup
1. Make sure you have Python 3.8+ installed
2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Frontend Setup
1. Make sure you have Node.js 16+ installed
2. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

## Docker Setup

The easiest way to run the application is using Docker and Docker Compose with our single-container setup:

1. Make sure you have [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/) installed
2. Build and start the container:
   ```bash
   docker-compose up --build
   ```
3. The application will be available at:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000

### Building and Running Manually

You can also build and run the container manually:

```bash
# Build the image
docker build -t simple-chat .

# Run the container
docker run -p 8000:8000 -p 5173:5173 simple-chat
```

## Running the Application

### Start the Backend
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
This will start the FastAPI server on port 8000.

### Start the Frontend
```bash
cd frontend
npm run dev -- --host
```
This will start the Svelte development server, usually on port 5173.

## Usage
1. Open your browser and navigate to http://localhost:5173
2. You'll automatically be assigned a random nickname
3. All users in the same network will appear in the user list
4. Click on a user to start chatting with them
5. Messages are temporary and will be lost if the page is refreshed

## Network Configuration
By default, the application is configured to work on a local network:
- Backend accessible at: http://your-ip-address:8000
- Frontend accessible at: http://your-ip-address:5173

Make sure to allow these ports through your firewall if you want others on the same network to connect.

## Customization
- Modify `/backend/main.py` to change server behavior or nickname generation
- Edit Svelte components in `/frontend/src/components/` to customize the UI
