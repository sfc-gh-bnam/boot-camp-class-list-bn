#!/bin/bash

# Script to start Streamlit server on MacBook Air
# Makes the app accessible from your network

echo "🚀 Starting Boot Camp Dashboard Server..."
echo ""

# Get local IP address
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -n 1)

if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="localhost"
fi

echo "📡 Server will be accessible at:"
echo "   - On this Mac: http://localhost:8501"
echo "   - On your network: http://${LOCAL_IP}:8501"
echo ""
echo "🌐 To access from internet, you'll need to:"
echo "   1. Configure router port forwarding (port 8501)"
echo "   2. Use your public IP or Dynamic DNS"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Find streamlit command - use python3 -m streamlit as it's more reliable
if command -v python3 &> /dev/null; then
    STREAMLIT_CMD="python3 -m streamlit"
elif command -v python &> /dev/null; then
    STREAMLIT_CMD="python -m streamlit"
elif command -v streamlit &> /dev/null; then
    STREAMLIT_CMD="streamlit"
else
    echo "❌ Error: Could not find streamlit. Please install it first:"
    echo "   pip3 install streamlit"
    exit 1
fi

# Run Streamlit with network access
echo "Starting Streamlit server..."
echo ""
$STREAMLIT_CMD run employee_dashboard_fixed.py --server.port=8501 --server.address=0.0.0.0

