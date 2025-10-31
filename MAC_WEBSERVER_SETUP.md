# Setting Up Your MacBook Air as a Web Server

## Option 1: Access from Same Network (Easiest)

This allows anyone on your WiFi/network to access the app.

### Step 1: Run Streamlit with Network Access

```bash
cd "/Users/bnam/Code Development/streamlit"
./start_server.sh
```

Or manually:
```bash
streamlit run employee_dashboard_fixed.py --server.port=8501 --server.address=0.0.0.0
```

This makes the app accessible from other devices on your network.

### Step 2: Find Your Mac's IP Address

```bash
./get_ip.sh
```

This will show your local IP address (e.g., `192.168.1.100`).

### Step 3: Access from Other Devices

- **On your Mac**: http://localhost:8501
- **From other devices on same network**: http://YOUR_LOCAL_IP:8501
- Replace `YOUR_LOCAL_IP` with the IP shown by `get_ip.sh`
- Example: http://192.168.1.100:8501

---

## Option 2: Access from Internet (More Setup Required)

To access from anywhere in the world, you'll need:

### Step A: Configure Your Router (Port Forwarding)

1. **Find your router's admin page**:
   - Usually: http://192.168.1.1 or http://192.168.0.1
   - Check router manual for admin login

2. **Set up port forwarding**:
   - Forward external port (e.g., 8501) to your Mac's IP:8501
   - Protocol: TCP
   - Save settings

3. **Find your public IP**:
   ```bash
   ./get_ip.sh
   ```
   Or:
   ```bash
   curl ifconfig.me
   ```

4. **Access from anywhere**:
   - `http://YOUR_PUBLIC_IP:8501`

⚠️ **Security Note**: This exposes your app to the internet. Consider adding password protection!

---

## Option 3: Use Dynamic DNS (If IP Changes)

If your public IP changes frequently:

1. **Sign up for free Dynamic DNS**:
   - DuckDNS.org (completely free) - Recommended
   - No-IP.com (free tier available)
   - Cloudflare (free)

2. **Install Dynamic DNS client** on your Mac (if needed)
3. **Access via**: `http://yourname.duckdns.org:8501`

---

## Keep Server Running

### Option 1: Keep Terminal Open
- Just leave the terminal window open while server runs
- Press `Ctrl+C` to stop

### Option 2: Run in Background
```bash
nohup ./start_server.sh > server.log 2>&1 &
```

To stop background server:
```bash
pkill -f "streamlit run"
```

### Option 3: Create Launch Agent (Auto-start on Boot)

1. Create plist file:
```bash
nano ~/Library/LaunchAgents/com.bootcamp.dashboard.plist
```

2. Add this content:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bootcamp.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/streamlit</string>
        <string>run</string>
        <string>/Users/bnam/Code Development/streamlit/employee_dashboard_fixed.py</string>
        <string>--server.port=8501</string>
        <string>--server.address=0.0.0.0</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/Users/bnam/Code Development/streamlit</string>
</dict>
</plist>
```

3. Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.bootcamp.dashboard.plist
```

---

## Security Considerations

1. **Firewall Settings**:
   - System Preferences → Security & Privacy → Firewall
   - Make sure Streamlit/Python is allowed

2. **Add Authentication** (Recommended for internet access):
   - Use Streamlit's built-in authentication
   - Or implement custom authentication

3. **Use HTTPS** (Advanced):
   - Requires reverse proxy like nginx
   - SSL certificate (Let's Encrypt is free)

---

## Troubleshooting

**Can't access from other devices?**
- Make sure devices are on same WiFi network
- Check macOS Firewall settings
- Verify IP address with `./get_ip.sh`

**Port already in use?**
- Change port: `--server.port=8502`
- Kill existing process: `pkill -f streamlit`

**Connection refused?**
- Make sure you used `--server.address=0.0.0.0` (not localhost)

