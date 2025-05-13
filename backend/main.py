from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_200_OK
import random
import json
import uuid
import datetime
from typing import Dict, List, Optional

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint that handles both GET and HEAD methods
@app.get("/")
@app.head("/")
def root():
    return Response(status_code=HTTP_200_OK)

# Store active connections and user data
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_nicknames: Dict[str, str] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str, nickname: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.user_nicknames[client_id] = nickname
        await self.broadcast_user_list()
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.user_nicknames:
            del self.user_nicknames[client_id]
        
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except RuntimeError as e:
                # If we get an error, the connection might be closed
                if "after sending 'websocket.close'" in str(e):
                    print(f"Connection closed for client {client_id}, removing")
                    self.disconnect(client_id)
                else:
                    # Re-raise other runtime errors
                    raise
            
    async def broadcast(self, message: str):
        # Create a list of clients to remove if their connection is closed
        clients_to_remove = []
        
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except RuntimeError as e:
                # If we get an error, the connection might be closed
                if "after sending 'websocket.close'" in str(e):
                    clients_to_remove.append(client_id)
                    print(f"Connection closed for client {client_id}, marking for removal")
                else:
                    # Re-raise other runtime errors
                    raise
        
        # Remove any closed connections
        for client_id in clients_to_remove:
            self.disconnect(client_id)
            
    async def broadcast_user_list(self):
        users = [{"id": client_id, "nickname": nickname} 
                for client_id, nickname in self.user_nicknames.items()]
        
        # Create a list of clients to remove if their connection is closed
        clients_to_remove = []
        
        # Send user list to all active connections
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json({"type": "users_update", "users": users})
            except RuntimeError as e:
                # If we get an error, the connection might be closed
                if "after sending 'websocket.close'" in str(e):
                    clients_to_remove.append(client_id)
                    print(f"Connection closed for client {client_id}, marking for removal")
                else:
                    # Re-raise other runtime errors
                    raise
        
        # Remove any closed connections
        for client_id in clients_to_remove:
            self.disconnect(client_id)
            
    async def send_direct_message(self, sender_id: str, recipient_id: str, content: str, message_type: str = 'text'):
        # Generate a unique message ID
        message_id = str(uuid.uuid4())
        
        message = {
            "type": "direct_message",
            "message_id": message_id,  # Add unique message ID
            "sender_id": sender_id,
            "sender_nickname": self.user_nicknames.get(sender_id, "Unknown"),
            "content": content,
            "message_type": message_type,  # Include the message type
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Clients that need to be removed due to closed connections
        clients_to_remove = []
        
        # Send only to recipient - sender already sees the message locally
        if recipient_id in self.active_connections:
            try:
                await self.active_connections[recipient_id].send_json(message)
            except RuntimeError as e:
                # If we get an error, the connection might be closed
                if "after sending 'websocket.close'" in str(e):
                    clients_to_remove.append(recipient_id)
                    print(f"Connection closed for recipient {recipient_id}, marking for removal")
                else:
                    # Re-raise other runtime errors
                    raise
        
        # Remove any closed connections
        for client_id in clients_to_remove:
            self.disconnect(client_id)

def import_time_module():
    from datetime import datetime
    return datetime.now().isoformat()

def generate_nickname():
    adjectives = ["Happy", "Clever", "Brave", "Calm", "Bright", "Kind", "Swift", "Wise", "Bold", "Cool"]
    animals = ["Lion", "Tiger", "Bear", "Wolf", "Fox", "Eagle", "Shark", "Dolphin", "Panda", "Owl"]
    return f"{random.choice(adjectives)}{random.choice(animals)}{random.randint(1, 99)}"

manager = ConnectionManager()

@app.get("/")
async def get():
    return {"message": "Simple Chat API is running"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # Generate a new nickname for the user
    nickname = generate_nickname()
    
    # Connect the user with the generated nickname
    await manager.connect(websocket, client_id, nickname)
    
    try:
        # Send initial nickname to the client
        await websocket.send_json({
            "type": "nickname_assigned",
            "nickname": nickname,
            "client_id": client_id
        })
        
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type")
                
                if message_type == "direct_message":
                    recipient_id = message_data.get("recipient_id")
                    content = message_data.get("content")
                    message_type = message_data.get("message_type", 'text')
                    
                    if recipient_id and content and recipient_id in manager.active_connections:
                        await manager.send_direct_message(client_id, recipient_id, content, message_type)
                
                elif message_type == "nickname_change":
                    new_nickname = message_data.get("nickname")
                    if new_nickname:
                        manager.user_nicknames[client_id] = new_nickname
                        await manager.broadcast_user_list()
                        
            except json.JSONDecodeError:
                # If not JSON, treat as simple message
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
        await manager.broadcast_user_list()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
