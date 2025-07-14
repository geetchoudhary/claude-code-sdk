#!/usr/bin/env python3
"""
Simple HTTP server to serve the MCP UI on port 3547
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

PORT = 3547

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS headers."""
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        # Serve the UI HTML file
        if self.path == '/' or self.path == '/index.html':
            self.path = '/mcp_ui.html'
        return super().do_GET()

def main():
    # Change to the script directory
    os.chdir(Path(__file__).parent)
    
    # Create the server
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"🌐 MCP UI Server running at http://localhost:{PORT}")
        print(f"📁 Serving from: {os.getcwd()}")
        print("\nPress Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            sys.exit(0)

if __name__ == "__main__":
    main()