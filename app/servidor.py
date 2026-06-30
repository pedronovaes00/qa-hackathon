import http.server
import socketserver
import os
import sys

PORT = 3000

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app_dir = os.path.join(project_root, "app")
os.chdir(app_dir)

Handler = http.server.SimpleHTTPRequestHandler


class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

print(f"Servidor rodando em http://localhost:{PORT}")
print(f"Servindo arquivos de: {app_dir}")
print("Pressione Ctrl+C para parar")

with ReusableThreadingTCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado.")
        httpd.server_close()
        sys.exit(0)
