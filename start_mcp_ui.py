#!/usr/bin/env python3
"""
Start the MCP UI server and ngrok tunnel
"""

import subprocess
import time
import sys
import os
import json
import requests
from pathlib import Path

def check_ngrok_installed():
    """Check if ngrok is installed"""
    try:
        subprocess.run(["ngrok", "version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_ngrok_url():
    """Get the public URL from ngrok API"""
    try:
        # Check ngrok API
        response = requests.get("http://localhost:4040/api/tunnels")
        tunnels = response.json()["tunnels"]
        for tunnel in tunnels:
            if tunnel["proto"] == "https":
                return tunnel["public_url"]
        # If no HTTPS, return HTTP
        for tunnel in tunnels:
            if tunnel["proto"] == "http":
                return tunnel["public_url"]
    except:
        return None
    return None

def main():
    print("🚀 Starting MCP UI System...")
    print("=" * 50)
    
    # Check if ngrok is installed
    if not check_ngrok_installed():
        print("❌ ngrok is not installed!")
        print("\nTo install ngrok:")
        print("1. Visit https://ngrok.com/download")
        print("2. Download and install for your platform")
        print("3. Sign up for a free account at https://ngrok.com")
        print("4. Run: ngrok authtoken YOUR_AUTH_TOKEN")
        sys.exit(1)
    
    # Start the MCP client server
    print("\n1️⃣ Starting MCP Client Server on port 8000...")
    mcp_server = subprocess.Popen(
        [sys.executable, "mcp_client_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)  # Give it time to start
    
    # Start the UI server
    print("2️⃣ Starting UI Server on port 3547...")
    ui_server = subprocess.Popen(
        [sys.executable, "mcp_ui_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(1)  # Give it time to start
    
    # Start ngrok
    print("3️⃣ Starting ngrok tunnel...")
    ngrok_process = subprocess.Popen(
        ["ngrok", "http", "3547"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for ngrok to establish connection
    print("⏳ Waiting for ngrok to establish tunnel...")
    time.sleep(3)
    
    # Get ngrok URL
    ngrok_url = get_ngrok_url()
    
    print("\n" + "=" * 50)
    print("✅ ALL SERVICES STARTED SUCCESSFULLY!")
    print("=" * 50)
    
    print("\n📍 Local Access:")
    print(f"   UI: http://localhost:3547")
    print(f"   API: http://localhost:8000")
    
    if ngrok_url:
        print(f"\n🌍 Public Access (via ngrok):")
        print(f"   {ngrok_url}")
        print(f"\n📋 Share this URL to access the MCP UI from anywhere!")
    else:
        print("\n⚠️  Could not retrieve ngrok URL.")
        print("   Check ngrok dashboard at: http://localhost:4040")
    
    print("\n📖 Quick Start:")
    print("   1. Open the UI in your browser")
    print("   2. Use Quick Connect buttons for common MCP servers")
    print("   3. Or manually configure a connection")
    print("   4. Interact with tools, resources, and prompts")
    
    print("\n⚠️  Press Ctrl+C to stop all services")
    print("=" * 50)
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        
        # Terminate all processes
        for process in [mcp_server, ui_server, ngrok_process]:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        
        print("✅ All services stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()