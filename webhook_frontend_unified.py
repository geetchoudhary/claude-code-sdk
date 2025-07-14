#!/usr/bin/env python3
"""
Unified Webhook Frontend Server with API Proxy
Receives webhooks and approval requests, displays them in a web interface
"""

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
from pathlib import Path
import json
import aiohttp
import uuid
import httpx

app = FastAPI(title="Claude Code Unified Frontend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store messages in memory (in production, use a database)
messages: List[Dict[str, Any]] = []
messages_lock = asyncio.Lock()

# Store pending approvals
pending_approvals: Dict[str, Dict[str, Any]] = {}
approval_history: List[Dict[str, Any]] = []
approvals_lock = asyncio.Lock()

# Store SSE clients
sse_clients: List[asyncio.Queue] = []
sse_clients_lock = asyncio.Lock()

# Maximum messages to keep
MAX_MESSAGES = 100
MAX_APPROVAL_HISTORY = 100

# API server URL
API_SERVER_URL = "http://localhost:8001"

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML"""
    frontend_path = Path(__file__).parent / "frontend_unified.html"
    if frontend_path.exists():
        with open(frontend_path, 'r') as f:
            content = f.read()
            # Replace API_URL with proxy endpoint
            content = content.replace(
                "return 'http://192.168.29.186:8001';", 
                "return '/api';"
            )
            content = content.replace(
                "return 'http://localhost:8001';", 
                "return '/api';"
            )
            return HTMLResponse(content=content)
    else:
        # Return default HTML if file not found
        return HTMLResponse(content=get_default_html())

@app.post("/api/query")
async def proxy_query(request: Request):
    """Proxy query requests to the API server"""
    try:
        body = await request.json()
        
        # Make request to actual API server
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_SERVER_URL}/query",
                json=body,
                timeout=30.0
            )
            
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except Exception as e:
        print(f"Proxy error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def proxy_health():
    """Proxy health check to the API server"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_SERVER_URL}/health",
                timeout=5.0
            )
            return JSONResponse(
                content=response.json(),
                status_code=response.status_code
            )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "detail": str(e)},
            status_code=503
        )

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
        
        print(f"✅ Webhook received - Task: {payload.get('task_id')} Session: {payload.get('session_id')} Status: {payload.get('status')}")
        
        # Notify all SSE clients
        await notify_sse_clients({'type': 'webhook', 'data': payload})
        
        return JSONResponse(content={"status": "received"}, status_code=200)
    
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=400)

@app.post("/approval-request")
async def receive_approval_request(request: Request, background_tasks: BackgroundTasks):
    """Receive approval request from MCP server"""
    try:
        data = await request.json()
        request_id = data.get("request_id")
        
        if not request_id:
            return JSONResponse({"error": "Missing request_id"}, status_code=400)
        
        async with approvals_lock:
            pending_approvals[request_id] = {
                **data,
                "received_at": datetime.now().isoformat()
            }
        
        print(f"📥 Received approval request: {request_id} for {data.get('tool_name')}")
        
        # Notify all SSE clients
        await notify_sse_clients({'type': 'approval_request', 'data': data})
        
        return JSONResponse({"status": "received", "request_id": request_id})
    
    except Exception as e:
        print(f"Error processing approval request: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/approve/{request_id}")
async def approve_request(request_id: str, request: Request, background_tasks: BackgroundTasks):
    """Handle approval decision"""
    try:
        data = await request.json()
        decision = data.get("decision")
        reason = data.get("reason", "")
        
        async with approvals_lock:
            if request_id not in pending_approvals:
                return JSONResponse({"error": "Request not found"}, status_code=404)
            
            approval_data = pending_approvals.pop(request_id)
            
            # Add to history
            approval_history.append({
                **approval_data,
                "decision": decision,
                "reason": reason,
                "decided_at": datetime.now().isoformat()
            })
            
            # Keep only last N history items
            if len(approval_history) > MAX_APPROVAL_HISTORY:
                approval_history.pop(0)
        
        # Send callback to MCP server
        callback_url = approval_data.get("callback_url")
        if callback_url:
            background_tasks.add_task(
                send_callback,
                callback_url,
                request_id,
                decision,
                reason
            )
        
        print(f"✅ Approval decision: {request_id} -> {decision}")
        
        # Notify all SSE clients
        await notify_sse_clients({'type': 'approval_decision', 'data': {
            'request_id': request_id,
            'decision': decision,
            'tool_name': approval_data.get('tool_name')
        }})
        
        return JSONResponse({"status": "approved", "decision": decision})
    
    except Exception as e:
        print(f"Error handling approval: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

async def send_callback(callback_url: str, request_id: str, decision: str, reason: str):
    """Send approval decision back to MCP server"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "request_id": request_id,
                "decision": decision,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
            
            async with session.post(callback_url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status >= 400:
                    print(f"Callback failed: {resp.status}")
                else:
                    print(f"Callback sent successfully to {callback_url}")
    
    except Exception as e:
        print(f"Error sending callback: {e}")

async def notify_sse_clients(data: dict):
    """Notify all SSE clients of an event"""
    async with sse_clients_lock:
        dead_clients = []
        for client_queue in sse_clients:
            try:
                await client_queue.put(data)
            except:
                dead_clients.append(client_queue)
        # Remove dead clients
        for client in dead_clients:
            sse_clients.remove(client)

@app.get("/messages")
async def get_messages():
    """Get all stored messages"""
    async with messages_lock:
        return JSONResponse(content={"messages": messages})

@app.get("/approvals")
async def get_approvals():
    """Get current pending approvals and history"""
    async with approvals_lock:
        return JSONResponse({
            "pending": pending_approvals,
            "history": approval_history[-20:]  # Last 20 items
        })

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
        "pending_approvals": len(pending_approvals),
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

def get_default_html():
    """Return default HTML if frontend file not found"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Claude Code Unified Frontend</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Claude Code Unified Frontend</h1>
        <p>Frontend HTML file not found. Please ensure frontend_unified.html exists.</p>
        <p>API Endpoints:</p>
        <ul>
            <li>POST /webhook - Receive Claude Code webhooks</li>
            <li>POST /approval-request - Receive MCP approval requests</li>
            <li>GET /messages - Get webhook messages</li>
            <li>GET /approvals - Get pending approvals</li>
            <li>POST /api/query - Proxy to API server</li>
        </ul>
    </div>
</body>
</html>
    """

if __name__ == "__main__":
    print("🚀 Claude Code Unified Frontend Server with API Proxy")
    print("📍 Frontend: http://localhost:8002")
    print("🔗 Webhook endpoint: http://localhost:8002/webhook")
    print("🔒 Approval endpoint: http://localhost:8002/approval-request")
    print("🔄 API Proxy: http://localhost:8002/api/*")
    print("\nThis server handles Claude webhooks, MCP approvals, and proxies API requests!")
    
    uvicorn.run(app, host="0.0.0.0", port=8002)