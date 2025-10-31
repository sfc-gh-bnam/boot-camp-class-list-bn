# Quick Start - Run Server on Your Mac

## 🚀 Start the Server (Easiest Way)

**Use the startup script:**
```bash
cd "/Users/bnam/Code Development/streamlit"
./start_server.sh
```

**Or manually:**
```bash
cd "/Users/bnam/Code Development/streamlit"
streamlit run employee_dashboard_fixed.py --server.port=8501 --server.address=0.0.0.0
```

## 📍 Find Your Access URLs

Run this to see all your IP addresses:
```bash
./get_ip.sh
```

## 🌐 Access Your App

### On Same Network (WiFi/LAN):
- **On your Mac**: http://localhost:8501
- **On other devices** (phones, tablets, other computers): http://YOUR_LOCAL_IP:8501
  - Replace YOUR_LOCAL_IP with the IP shown by `get_ip.sh`
  - Example: http://192.168.1.100:8501

### From Internet (Requires Router Setup):
1. Configure port forwarding on your router (port 8501)
2. Use your public IP or Dynamic DNS
3. Access at: http://YOUR_PUBLIC_IP:8501

## ⚙️ Keep Server Running

### Option 1: Keep Terminal Open
- Just leave the terminal window open while server runs
- Press `Ctrl+C` to stop

### Option 2: Run in Background
```bash
cd "/Users/bnam/Code Development/streamlit"
nohup ./start_server.sh > server.log 2>&1 &
```

To stop background server:
```bash
pkill -f "streamlit run"
```

### Option 3: Use macOS Launch Agent (Auto-start on boot)
See `MAC_WEBSERVER_SETUP.md` for detailed instructions

## 🔒 Security Tips

1. **Add password protection** (consider Streamlit authentication)
2. **Use HTTPS** if exposing to internet (requires reverse proxy like nginx)
3. **Firewall**: Make sure port 8501 is allowed in macOS Firewall settings
4. **Keep Mac awake**: Use "Prevent automatic sleeping" in System Preferences

## 🛑 Stop the Server

Press `Ctrl+C` in the terminal where it's running

Or if running in background:
```bash
pkill -f "streamlit run"
```

---

**See `MAC_WEBSERVER_SETUP.md` for detailed setup instructions!**

