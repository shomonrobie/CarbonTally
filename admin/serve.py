# serve.py - Place this in D:\carbon_ledger\admin
import http.server
import socketserver
import os
import urllib.parse

PORT = 3001
BUILD_DIR = os.path.join(os.path.dirname(__file__), 'build')

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BUILD_DIR, **kwargs)
    
    def do_GET(self):
        # Parse the path
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        # Handle /admin paths
        if path.startswith('/admin'):
            # Remove /admin prefix
            new_path = path[6:]  # Remove '/admin'
            
            # If it's empty or '/', serve index.html
            if not new_path or new_path == '/':
                new_path = '/index.html'
            
            # If it's a static file request, serve it from the build folder
            if new_path.startswith('/static/'):
                self.path = new_path
                return super().do_GET()
            
            # Otherwise, serve index.html for client-side routing
            self.path = '/index.html'
            return super().do_GET()
        
        # Handle root path - redirect to /admin
        if path == '/' or path == '':
            self.send_response(302)
            self.send_header('Location', '/admin/')
            self.end_headers()
            return
        
        # Handle favicon.ico
        if path == '/favicon.ico':
            favicon_path = os.path.join(BUILD_DIR, 'favicon.ico')
            if os.path.exists(favicon_path):
                self.path = '/favicon.ico'
                return super().do_GET()
            else:
                self.send_response(404)
                self.end_headers()
                return
        
        # For all other paths, try to serve from build
        self.path = path
        return super().do_GET()

with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
    print("=" * 50)
    print("🌱 CarbonTally Admin Dashboard")
    print("=" * 50)
    print(f"✅ Server running on http://localhost:{PORT}")
    print(f"📱 Admin dashboard: http://localhost:{PORT}/admin")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    httpd.serve_forever()