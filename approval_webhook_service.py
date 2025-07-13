#!/usr/bin/env python3
"""
Approval Webhook Service
Receives approval requests and provides UI for approve/deny decisions
"""

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
import aiohttp
from pathlib import Path
import json

app = FastAPI(title="MCP Approval Webhook Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store pending approvals
pending_approvals: Dict[str, Dict[str, Any]] = {}
approval_history: List[Dict[str, Any]] = []

# Lock for thread safety
approvals_lock = asyncio.Lock()

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the approval UI"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>MCP Permission Approvals</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .section {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .approval-item {
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
            background: #fafafa;
        }
        .approval-item.pending {
            border-color: #ff9800;
            background: #fff3e0;
        }
        .approval-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .tool-name {
            font-weight: bold;
            font-size: 18px;
            color: #1976d2;
        }
        .timestamp {
            color: #666;
            font-size: 14px;
        }
        .display-text {
            margin: 10px 0;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 4px;
            font-family: monospace;
        }
        .tool-input {
            margin: 10px 0;
            padding: 10px;
            background: #f0f0f0;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            overflow-x: auto;
        }
        .buttons {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .approve-btn {
            background: #4caf50;
            color: white;
        }
        .approve-btn:hover {
            background: #45a049;
        }
        .deny-btn {
            background: #f44336;
            color: white;
        }
        .deny-btn:hover {
            background: #da190b;
        }
        .history-item {
            opacity: 0.7;
        }
        .status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 14px;
            font-weight: bold;
        }
        .status.approved {
            background: #e8f5e9;
            color: #2e7d32;
        }
        .status.denied {
            background: #ffebee;
            color: #c62828;
        }
        .empty-state {
            text-align: center;
            color: #999;
            padding: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 MCP Permission Approvals</h1>
        
        <div class="section">
            <h2>Pending Approvals</h2>
            <div id="pending-approvals">
                <div class="empty-state">No pending approvals</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Approval History</h2>
            <div id="approval-history">
                <div class="empty-state">No approval history</div>
            </div>
        </div>
    </div>

    <script>
        let eventSource = null;
        
        async function fetchApprovals() {
            try {
                const response = await fetch('/approvals');
                const data = await response.json();
                updateUI(data);
            } catch (error) {
                console.error('Error fetching approvals:', error);
            }
        }
        
        function updateUI(data) {
            // Update pending approvals
            const pendingDiv = document.getElementById('pending-approvals');
            const pendingItems = Object.entries(data.pending || {});
            
            if (pendingItems.length === 0) {
                pendingDiv.innerHTML = '<div class="empty-state">No pending approvals</div>';
            } else {
                pendingDiv.innerHTML = pendingItems.map(([id, item]) => `
                    <div class="approval-item pending">
                        <div class="approval-header">
                            <span class="tool-name">${item.tool_name}</span>
                            <span class="timestamp">${new Date(item.timestamp).toLocaleString()}</span>
                        </div>
                        <div class="display-text">${item.display_text || 'No description'}</div>
                        <details>
                            <summary>View Details</summary>
                            <div class="tool-input">${JSON.stringify(item.tool_input, null, 2)}</div>
                        </details>
                        <div class="buttons">
                            <button class="approve-btn" onclick="handleApproval('${id}', 'allow')">
                                ✅ Approve
                            </button>
                            <button class="deny-btn" onclick="handleApproval('${id}', 'deny')">
                                ❌ Deny
                            </button>
                        </div>
                    </div>
                `).join('');
            }
            
            // Update history
            const historyDiv = document.getElementById('approval-history');
            const historyItems = data.history || [];
            
            if (historyItems.length === 0) {
                historyDiv.innerHTML = '<div class="empty-state">No approval history</div>';
            } else {
                historyDiv.innerHTML = historyItems.slice(-10).reverse().map(item => `
                    <div class="approval-item history-item">
                        <div class="approval-header">
                            <span class="tool-name">${item.tool_name}</span>
                            <span class="timestamp">${new Date(item.timestamp).toLocaleString()}</span>
                        </div>
                        <div class="display-text">${item.display_text || 'No description'}</div>
                        <div>
                            <span class="status ${item.decision === 'allow' ? 'approved' : 'denied'}">
                                ${item.decision === 'allow' ? 'APPROVED' : 'DENIED'}
                            </span>
                            ${item.reason ? `<span style="margin-left: 10px; color: #666;">${item.reason}</span>` : ''}
                        </div>
                    </div>
                `).join('');
            }
        }
        
        async function handleApproval(requestId, decision) {
            try {
                const response = await fetch(`/approve/${requestId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        decision: decision,
                        reason: decision === 'deny' ? 'User denied permission' : ''
                    })
                });
                
                if (response.ok) {
                    // Refresh the UI
                    fetchApprovals();
                }
            } catch (error) {
                console.error('Error handling approval:', error);
            }
        }
        
        function connectSSE() {
            eventSource = new EventSource('/events');
            
            eventSource.onmessage = (event) => {
                fetchApprovals();
            };
            
            eventSource.onerror = (error) => {
                console.error('SSE error:', error);
                eventSource.close();
                // Reconnect after 5 seconds
                setTimeout(connectSSE, 5000);
            };
        }
        
        // Initial load
        fetchApprovals();
        connectSSE();
        
        // Refresh every 2 seconds as backup
        setInterval(fetchApprovals, 2000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

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
            
            # Keep only last 100 history items
            if len(approval_history) > 100:
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

@app.get("/approvals")
async def get_approvals():
    """Get current pending approvals and history"""
    async with approvals_lock:
        return JSONResponse({
            "pending": pending_approvals,
            "history": approval_history[-20:]  # Last 20 items
        })

@app.get("/events")
async def events(request: Request):
    """Server-sent events for real-time updates"""
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            
            # Send heartbeat
            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            await asyncio.sleep(2)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "pending_count": len(pending_approvals),
        "history_count": len(approval_history)
    }

if __name__ == "__main__":
    print("🚀 MCP Approval Webhook Service")
    print("📍 UI: http://localhost:8082")
    print("🔗 Webhook endpoint: http://localhost:8082/approval-request")
    print("\nWaiting for approval requests...")
    
    uvicorn.run(app, host="0.0.0.0", port=8082)