#!/usr/bin/env python3
"""
Webhook Frontend Server
Receives webhooks and displays them in a web interface
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from datetime import datetime
from typing import List, Dict, Any
import asyncio
from pathlib import Path
import json

app = FastAPI(title="Claude Code Webhook Frontend")

# Store messages in memory (in production, use a database)
messages: List[Dict[str, Any]] = []
messages_lock = asyncio.Lock()

# Store SSE clients
sse_clients: List[asyncio.Queue] = []
sse_clients_lock = asyncio.Lock()

# Maximum messages to keep
MAX_MESSAGES = 100

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML"""
    frontend_path = Path(__file__).parent / "frontend_sessions.html"
    if frontend_path.exists():
        with open(frontend_path, 'r') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>Frontend file not found</h1>")

@app.post("/webhook")
async def receive_webhook(request: Request):
    """Receive webhook from Claude Code API"""
    try:
        payload = await request.json()
        
        # Add received timestamp if not present
        if 'received_at' not in payload:
            payload['received_at'] = datetime.utcnow().isoformat()
        
        # Store message
        async with messages_lock:
            messages.append(payload)
            # Keep only the latest messages
            if len(messages) > MAX_MESSAGES:
                messages.pop(0)
        
        print(f"✅ Webhook received - Task: {payload.get('task_id')} Session: {payload.get('session_id')} Conversation: {payload.get('conversation_id')} Status: {payload.get('status')}")
        
        # Notify all SSE clients
        async with sse_clients_lock:
            dead_clients = []
            for client_queue in sse_clients:
                try:
                    await client_queue.put(payload)
                except:
                    dead_clients.append(client_queue)
            # Remove dead clients
            for client in dead_clients:
                sse_clients.remove(client)
        
        return JSONResponse(content={"status": "received"}, status_code=200)
    
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=400)

@app.get("/messages")
async def get_messages():
    """Get all stored messages"""
    async with messages_lock:
        return JSONResponse(content={"messages": messages})

@app.delete("/messages")
async def clear_messages():
    """Clear all messages"""
    async with messages_lock:
        messages.clear()
    return JSONResponse(content={"status": "cleared"})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message_count": len(messages),
        "timestamp": datetime.utcnow().isoformat()
    }

async def event_generator():
    """Generate SSE events for real-time updates"""
    queue = asyncio.Queue()
    
    # Add this client to the list
    async with sse_clients_lock:
        sse_clients.append(queue)
    
    try:
        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connected'})}\n\n"
        
        while True:
            # Wait for new messages
            message = await queue.get()
            yield f"data: {json.dumps(message)}\n\n"
            
    except asyncio.CancelledError:
        # Client disconnected
        async with sse_clients_lock:
            if queue in sse_clients:
                sse_clients.remove(queue)
        raise

@app.get("/events")
async def events():
    """Server-Sent Events endpoint for real-time updates"""
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

if __name__ == "__main__":
    print("🚀 Claude Code Webhook Frontend Server")
    print("📍 Frontend: http://localhost:8002")
    print("🔗 Webhook endpoint: http://localhost:8002/webhook")
    print("\nUse this webhook URL in your Claude Code API requests!")
    
    uvicorn.run(app, host="0.0.0.0", port=8002)