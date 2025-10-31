#!/bin/bash

# Quick script to get your IP addresses

echo "🌐 Network Information"
echo "===================="
echo ""

echo "📱 Local Network IP (for same WiFi access):"
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)
if [ -z "$LOCAL_IP" ]; then
    echo "   Not connected to network"
else
    echo "   http://${LOCAL_IP}:8501"
fi
echo ""

echo "🌍 Public IP (for internet access):"
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "Unable to fetch")
echo "   ${PUBLIC_IP}"
if [ "$PUBLIC_IP" != "Unable to fetch" ]; then
    echo "   http://${PUBLIC_IP}:8501 (requires port forwarding)"
fi
echo ""

echo "💡 Tips:"
echo "   - Local IP works for devices on same WiFi"
echo "   - Public IP requires router port forwarding"
echo "   - Consider using Dynamic DNS if IP changes"

