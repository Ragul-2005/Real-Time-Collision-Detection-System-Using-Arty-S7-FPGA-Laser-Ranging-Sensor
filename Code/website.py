import serial
import time
import threading
import json
import csv
import os
from datetime import datetime
from collections import deque
from flask import Flask, Response, render_template_string, request, jsonify

# Check for required libraries
try:
    import serial
    print(f"[INFO] Required libraries found - pyserial: {serial._version_}")
except ImportError as e:
    print(f"[ERROR] Missing required library: {e}")
    print("[INFO] Please install: pip install pyserial flask")
    exit(1)

# --- Serial Configuration ---
SERIAL_PORT = 'COM7'
SERIAL_BAUDRATE = 9600

# --- Global Variables ---
latest_data = "No data yet"
data_history = deque(maxlen=1000)
connection_status = "Disconnected"
total_bytes = 0
message_count = 0
start_time = datetime.now()
data_logging = False
log_filename = ""

# --- Flask Setup ---
app = Flask(_name_)

# Disable Flask logging for cleaner output
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

# Enhanced HTML Template with Modern UI
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Dynamic Serial Monitor Pro</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            color: #ffffff;
        }
        
        .header {
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            padding: 15px 30px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .header h1 {
            font-size: 1.8rem;
            font-weight: 600;
            margin: 0;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 20px;
            padding: 25px 30px;
            background: rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
        }
        
        @media (max-width: 1200px) {
            .status-grid { grid-template-columns: repeat(3, 1fr); }
        }
        
        @media (max-width: 768px) {
            .status-grid { grid-template-columns: repeat(2, 1fr); }
        }
        
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }
        
        .status-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            background: rgba(255, 255, 255, 0.15);
        }
        
        .status-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
            display: block;
            margin-bottom: 8px;
        }
        
        .status-label {
            font-size: 0.85rem;
            color: rgba(255, 255, 255, 0.8);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
        }
        
        .connection-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        .connected {
            background: #00ff88;
            box-shadow: 0 0 15px #00ff88;
        }
        
        .disconnected {
            background: #ff4757;
            box-shadow: 0 0 15px #ff4757;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        
        .controls-section {
            padding: 20px 30px;
            background: rgba(0, 0, 0, 0.15);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .controls-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
            background: rgba(255, 255, 255, 0.2);
        }
        
        .btn-primary { background: linear-gradient(45deg, #3b82f6, #1d4ed8); }
        .btn-success { background: linear-gradient(45deg, #10b981, #059669); }
        .btn-danger { background: linear-gradient(45deg, #ef4444, #dc2626); }
        .btn-warning { background: linear-gradient(45deg, #f59e0b, #d97706); }
        
        .checkbox-wrapper {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.1);
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .checkbox-wrapper:hover {
            background: rgba(255, 255, 255, 0.15);
        }
        
        .checkbox-wrapper input[type="checkbox"] {
            accent-color: #3b82f6;
            transform: scale(1.2);
        }
        
        .main-layout {
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 30px;
            padding: 30px;
            height: calc(100vh - 300px);
        }
        
        @media (max-width: 1024px) {
            .main-layout { 
                grid-template-columns: 1fr; 
                height: auto;
            }
        }
        
        .data-panel {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            overflow: hidden;
            backdrop-filter: blur(15px);
            display: flex;
            flex-direction: column;
        }
        
        .panel-header {
            background: rgba(0, 0, 0, 0.3);
            padding: 15px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .panel-header i {
            color: #3b82f6;
        }
        
        .panel-title {
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .data-rate {
            margin-left: auto;
            font-size: 0.9rem;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .data-display {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background: rgba(0, 0, 0, 0.6);
            color: #00ff88;
            line-height: 1.6;
            font-size: 0.9rem;
        }
        
        .data-display::-webkit-scrollbar {
            width: 8px;
        }
        
        .data-display::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.3);
        }
        
        .data-display::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 4px;
        }
        
        .data-line {
            margin-bottom: 8px;
            padding: 8px 12px;
            background: rgba(0, 0, 0, 0.2);
            border-left: 3px solid #3b82f6;
            border-radius: 0 6px 6px 0;
            animation: slideIn 0.3s ease-out;
            word-break: break-all;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        .timestamp {
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.8rem;
            margin-right: 10px;
        }
        
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        .stats-panel {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            overflow: hidden;
            backdrop-filter: blur(15px);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            padding: 20px;
        }
        
        .stat-item {
            text-align: center;
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .stat-value {
            font-size: 1.3rem;
            font-weight: 700;
            color: #ffffff;
            display: block;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: rgba(255, 255, 255, 0.7);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .filter-panel {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            overflow: hidden;
            backdrop-filter: blur(15px);
        }
        
        .filter-content {
            padding: 20px;
        }
        
        .input-group {
            margin-bottom: 15px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.9rem;
        }
        
        .form-control {
            width: 100%;
            padding: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.3);
            color: white;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        }
        
        .form-control::placeholder {
            color: rgba(255, 255, 255, 0.5);
        }
        
        .no-data-message {
            text-align: center;
            color: rgba(255, 255, 255, 0.6);
            font-style: italic;
            padding: 40px;
        }
        
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #3b82f6;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Success message styling */
        .success-message {
            color: #00ff88;
            background: rgba(0, 255, 136, 0.1);
            border: 1px solid rgba(0, 255, 136, 0.3);
            padding: 12px;
            border-radius: 8px;
            margin-top: 10px;
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-satellite-dish"></i> Dynamic Serial Monitor Pro</h1>
    </div>
    
    <div class="status-grid">
        <div class="status-card">
            <span class="status-value" id="connection-status">
                <span class="connection-indicator disconnected"></span>Disconnected
            </span>
            <span class="status-label">Connection Status</span>
        </div>
        <div class="status-card">
            <span class="status-value" id="port-info">{{port}}</span>
            <span class="status-label">Port</span>
        </div>
        <div class="status-card">
            <span class="status-value" id="baudrate-info">{{baudrate}}</span>
            <span class="status-label">Baud Rate</span>
        </div>
        <div class="status-card">
            <span class="status-value" id="message-count">0</span>
            <span class="status-label">Messages</span>
        </div>
        <div class="status-card">
            <span class="status-value" id="bytes-count">0 B</span>
            <span class="status-label">Total Bytes</span>
        </div>
        <div class="status-card">
            <span class="status-value" id="uptime">00:00:00</span>
            <span class="status-label">Uptime</span>
        </div>
    </div>
    
    <div class="controls-section">
        <div class="controls-grid">
            <button class="btn btn-primary" onclick="clearDisplay()">
                <i class="fas fa-trash"></i> Clear Display
            </button>
            <button class="btn btn-success" onclick="downloadData()">
                <i class="fas fa-download"></i> Download Data
            </button>
            <button class="btn btn-warning" onclick="toggleLogging()" id="log-btn">
                <i class="fas fa-file-alt"></i> Start Logging
            </button>
            <label class="checkbox-wrapper">
                <input type="checkbox" id="auto-scroll" checked onchange="toggleAutoScroll()">
                <i class="fas fa-arrows-alt-v"></i>
                <span>Auto Scroll</span>
            </label>
            <label class="checkbox-wrapper">
                <input type="checkbox" id="timestamps" checked onchange="toggleTimestamps()">
                <i class="fas fa-clock"></i>
                <span>Show Timestamps</span>
            </label>
            <label class="checkbox-wrapper">
                <input type="checkbox" id="sound-alerts" onchange="toggleSoundAlerts()">
                <i class="fas fa-volume-up"></i>
                <span>Sound Alerts</span>
            </label>
        </div>
    </div>
    
    <div class="main-layout">
        <div class="data-panel">
            <div class="panel-header">
                <i class="fas fa-stream"></i>
                <span class="panel-title">Live Serial Data Stream</span>
                <span class="data-rate" id="data-rate-display">0 B/s</span>
            </div>
            <div class="data-display" id="data-display">
                <div class="no-data-message">
                    <i class="loading-spinner"></i> Waiting for data...
                </div>
            </div>
        </div>
        
        <div class="sidebar">
            <div class="stats-panel">
                <div class="panel-header">
                    <i class="fas fa-chart-bar"></i>
                    <span class="panel-title">Live Statistics</span>
                </div>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-value" id="avg-msg-size">0 B</span>
                        <span class="stat-label">Avg Message Size</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="msg-rate">0.0/s</span>
                        <span class="stat-label">Messages/sec</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="data-rate">0 B/s</span>
                        <span class="stat-label">Data Rate</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-value" id="last-message">1:14:03 PM</span>
                        <span class="stat-label">Last Message</span>
                    </div>
                </div>
            </div>
            
            <div class="filter-panel">
                <div class="panel-header">
                    <i class="fas fa-filter"></i>
                    <span class="panel-title">Data Filter</span>
                </div>
                <div class="filter-content">
                    <div class="input-group">
                        <label><i class="fas fa-search"></i> Filter Text</label>
                        <input type="text" class="form-control" id="filter-text" 
                               placeholder="Enter text to filter..." 
                               onkeyup="applyFilter()">
                    </div>
                    <button class="btn btn-danger" onclick="clearFilter()" style="width: 100%;">
                        <i class="fas fa-times"></i> Clear Filter
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let showTimestamps = true;
        let autoScrollEnabled = true;
        let soundAlertsEnabled = false;
        let filterText = '';
        let allData = [];
        let startTime = new Date();
        
        // Server-Sent Events connection
        console.log("Starting EventSource connection...");
        const evtSource = new EventSource("/stream");
        
        evtSource.onopen = function(event) {
            console.log("EventSource connection opened");
        };
        
        evtSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                updateDisplay(data);
                updateStatistics(data);
                
                // Play sound alert if enabled
                if (soundAlertsEnabled && data.message && data.message !== "No data yet") {
                    playNotificationSound();
                }
            } catch (e) {
                console.log("Error parsing JSON, treating as plain text");
                const data = {
                    message: event.data,
                    timestamp: new Date().toISOString(),
                    status: 'Connected'
                };
                updateDisplay(data);
            }
        };
        
        evtSource.onerror = function(event) {
            console.error("EventSource error:", event);
            updateConnectionStatus("Connection Error");
        };
        
        function updateDisplay(data) {
            const display = document.getElementById('data-display');
            const timestamp = new Date(data.timestamp).toLocaleTimeString();
            
            // Store all data
            allData.push(data);
            if (allData.length > 1000) {
                allData.shift();
            }
            
            // Remove "waiting for data" message on first real data
            if (data.message && data.message !== "No data yet" && display.querySelector('.no-data-message')) {
                display.innerHTML = '';
            }
            
            // Apply filter
            if (shouldShowMessage(data.message)) {
                const dataLine = document.createElement('div');
                dataLine.className = 'data-line';
                
                let content = '';
                if (showTimestamps) {
                    content += <span class="timestamp">[${timestamp}]</span>;
                }
                content += data.message;
                
                dataLine.innerHTML = content;
                display.appendChild(dataLine);
                
                // Keep only last 200 visible messages for performance
                while (display.children.length > 200) {
                    display.removeChild(display.firstChild);
                }
                
                // Auto scroll
                if (autoScrollEnabled) {
                    display.scrollTop = display.scrollHeight;
                }
            }
            
            // Update connection status
            if (data.status) {
                updateConnectionStatus(data.status);
            }
        }
        
        function updateConnectionStatus(status) {
            const statusElement = document.getElementById('connection-status');
            const indicator = statusElement.querySelector('.connection-indicator');
            
            if (status === 'Connected') {
                statusElement.innerHTML = '<span class="connection-indicator connected"></span>Connected';
            } else {
                statusElement.innerHTML = <span class="connection-indicator disconnected"></span>${status};
            }
        }
        
        function updateStatistics(data) {
            if (data.stats) {
                document.getElementById('message-count').textContent = data.stats.message_count || 0;
                document.getElementById('bytes-count').textContent = formatBytes(data.stats.total_bytes || 0);
                document.getElementById('avg-msg-size').textContent = formatBytes(data.stats.avg_message_size || 0);
                document.getElementById('msg-rate').textContent = (data.stats.message_rate || 0).toFixed(1) + '/s';
                
                const dataRate = formatBytes(data.stats.data_rate || 0) + '/s';
                document.getElementById('data-rate').textContent = dataRate;
                document.getElementById('data-rate-display').textContent = dataRate;
                
                document.getElementById('last-message').textContent = 
                    new Date(data.timestamp).toLocaleTimeString();
            }
        }
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function shouldShowMessage(message) {
            if (!filterText) return true;
            return message.toLowerCase().includes(filterText.toLowerCase());
        }
        
        function clearDisplay() {
            document.getElementById('data-display').innerHTML = 
                '<div class="no-data-message"><i class="loading-spinner"></i> Display cleared...</div>';
        }
        
        function toggleAutoScroll() {
            autoScrollEnabled = document.getElementById('auto-scroll').checked;
        }
        
        function toggleTimestamps() {
            showTimestamps = document.getElementById('timestamps').checked;
        }
        
        function toggleSoundAlerts() {
            soundAlertsEnabled = document.getElementById('sound-alerts').checked;
        }
        
        function playNotificationSound() {
            // Create a simple beep sound
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        }
        
        function applyFilter() {
            filterText = document.getElementById('filter-text').value;
        }
        
        function clearFilter() {
            document.getElementById('filter-text').value = '';
            filterText = '';
        }
        
        function downloadData() {
            const data = allData.map(item => 
                "${item.timestamp}","${item.message.replace(/"/g, '""')}"
            ).join('\\n');
            
            const blob = new Blob(['Timestamp,Message\\n' + data], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = serial_data_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }
        
        function toggleLogging() {
            fetch('/toggle_logging', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    const btn = document.getElementById('log-btn');
                    if (data.logging) {
                        btn.innerHTML = '<i class="fas fa-stop"></i> Stop Logging';
                        btn.className = 'btn btn-danger';
                    } else {
                        btn.innerHTML = '<i class="fas fa-file-alt"></i> Start Logging';
                        btn.className = 'btn btn-warning';
                    }
                })
                .catch(error => console.log('Logging toggle error:', error));
        }
        
        // Update uptime every second
        setInterval(() => {
            const uptime = Math.floor((new Date() - startTime) / 1000);
            const hours = Math.floor(uptime / 3600).toString().padStart(2, '0');
            const minutes = Math.floor((uptime % 3600) / 60).toString().padStart(2, '0');
            const seconds = (uptime % 60).toString().padStart(2, '0');
            document.getElementById('uptime').textContent = ${hours}:${minutes}:${seconds};
        }, 1000);
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    try:
        return render_template_string(HTML_PAGE, port=SERIAL_PORT, baudrate=SERIAL_BAUDRATE)
    except Exception as e:
        print(f"[ERROR] Template error: {e}")
        return f"<h1>Error</h1><p>{e}</p>", 500

@app.route("/stream")
def stream():
    print("[DEBUG] Stream route accessed")
    
    def event_stream():
        print("[DEBUG] Event stream generator started")
        global message_count, total_bytes, start_time
        last_time = time.time()
        last_message_count = 0
        last_bytes = 0
        
        while True:
            try:
                current_time = time.time()
                time_diff = current_time - last_time
                
                # Calculate rates every second
                message_rate = 0
                data_rate = 0
                if time_diff >= 1.0:
                    message_rate = (message_count - last_message_count) / time_diff
                    data_rate = (total_bytes - last_bytes) / time_diff
                    last_message_count = message_count
                    last_bytes = total_bytes
                    last_time = current_time
                
                # Calculate average message size
                avg_msg_size = total_bytes / max(message_count, 1)
                
                data = {
                    "message": latest_data,
                    "timestamp": datetime.now().isoformat(),
                    "status": connection_status,
                    "stats": {
                        "message_count": message_count,
                        "total_bytes": total_bytes,
                        "avg_message_size": avg_msg_size,
                        "message_rate": message_rate,
                        "data_rate": data_rate
                    }
                }
                
                json_str = json.dumps(data)
                yield f"data: {json_str}\n\n"
                time.sleep(0.2)  # Send updates every 200ms
                
            except Exception as e:
                print(f"[ERROR] Stream error: {e}")
                error_data = json.dumps({"error": str(e), "timestamp": datetime.now().isoformat()})
                yield f"data: {error_data}\n\n"
                time.sleep(1)
    
    response = Response(event_stream(), mimetype="text/event-stream")
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route("/toggle_logging", methods=["POST"])
def toggle_logging():
    global data_logging, log_filename
    
    try:
        data_logging = not data_logging
        
        if data_logging:
            log_filename = f"serial_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(log_filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Data'])
            print(f"[INFO] Started logging to {log_filename}")
        else:
            print(f"[INFO] Stopped logging")
        
        return jsonify({"logging": data_logging, "filename": log_filename})
    
    except Exception as e:
        print(f"[ERROR] Logging toggle failed: {e}")
        return jsonify({"error": str(e)})

# --- Serial Reader Thread ---
def serial_reader():
    global latest_data, connection_status, total_bytes, message_count, data_history
    
    while True:
        try:
            print(f"[INFO] Attempting to connect to {SERIAL_PORT}...")
            ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=0.1)
            ser.dtr = False
            ser.rts = False
            connection_status = "Connected"
            print(f"[INFO] Connected to {SERIAL_PORT} at {SERIAL_BAUDRATE} baud")
            
            while True:
                if ser.in_waiting > 0:
                    data_bytes = ser.read(ser.in_waiting)
                    try:
                        data_str = data_bytes.decode('utf-8').strip()
                    except UnicodeDecodeError:
                        data_str = f"<BIN:{data_bytes.hex()}>"
                    
                    if data_str:
                        latest_data = data_str
                        total_bytes += len(data_bytes)
                        message_count += 1
                        
                        # Store in history
                        timestamp = datetime.now()
                        data_history.append({
                            'timestamp': timestamp,
                            'data': data_str,
                            'bytes': len(data_bytes)
                        })
                        
                        # Log to file if enabled
                        if data_logging and log_filename:
                            try:
                                with open(log_filename, 'a', newline='') as f:
                                    writer = csv.writer(f)
                                    writer.writerow([timestamp.isoformat(), data_str])
                            except Exception as e:
                                print(f"[ERROR] Logging failed: {e}")
                        
                        print(f"[SERIAL] {data_str}")
                
                time.sleep(0.05)
                
        except serial.SerialException as e:
            print(f"[ERROR] Serial connection failed: {e}")
            connection_status = f"Serial Error: {str(e)}"
            latest_data = "Serial connection error"
            time.sleep(3)
            
        except Exception as e:
            print(f"[ERROR] Unexpected serial error: {e}")
            connection_status = f"Error: {str(e)}"
            time.sleep(3)

if _name_ == "_main_":
    try:
        print(f"[INFO] Dynamic Serial Monitor Pro Starting...")
        print(f"[INFO] Configuration: {SERIAL_PORT} @ {SERIAL_BAUDRATE} baud")
        
        # Start the serial reader thread
        print(f"[INFO] Starting serial reader thread...")
        threading.Thread(target=serial_reader, daemon=True).start()
        time.sleep(1)  # Give serial thread time to start
        
        print(f"[INFO] Starting Flask web server...")
        print(f"[INFO] 🌐 Access dashboard at: http://localhost:5000")
        print(f"[INFO] 🌐 Or from network: http://10.157.212.51:5000")
        print(f"[INFO] Press Ctrl+C to stop")
        
        # Run Flask
        app.run(host="0.0.0.0", port=5000, debug=False, threaded=True, use_reloader=False)
        
    except KeyboardInterrupt:
        print(f"\\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"[ERROR] Application failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"[INFO] Application ended")