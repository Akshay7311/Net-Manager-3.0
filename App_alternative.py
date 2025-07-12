import os
import platform
import subprocess
import psutil
import time
import logging
from datetime import timedelta, datetime
from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import threading
import nmap  # python-nmap library
from scapy.all import ARP, Ether, srp
import netaddr

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'netmanager_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Chat-related variables
chat_clients = {}  # sid -> (name, ip)
ip_to_sid = {}  # ip -> sid
chat_messages = []  # Store recent messages
MAX_MESSAGES = 100  # Keep last 100 messages

# Set up logging
logging.basicConfig(
    filename="scan_logs.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

ip_range = "192.168.1.1/24"

logging.info("Starting network scan for range: %s", ip_range)

# Alternative 1: Using python-nmap library
def scan_network_with_nmap_lib():
    """Scan network using python-nmap library"""
    try:
        nm = nmap.PortScanner()
        nm.scan(hosts=ip_range, arguments='-sn')
        active_ips = []
        
        for host in nm.all_hosts():
            if nm[host].state() == 'up':
                active_ips.append(host)
                logging.info("Active IP detected: %s", host)
        
        return active_ips
    except Exception as e:
        logging.error("Error with python-nmap: %s", str(e))
        return []

# Alternative 2: Using Scapy for ARP scanning
def scan_network_with_scapy():
    """Scan network using Scapy ARP requests"""
    try:
        # Create ARP request packet
        arp = ARP(pdst=ip_range)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp
        
        # Send packet and capture response
        result = srp(packet, timeout=3, verbose=0)[0]
        
        active_ips = []
        for sent, received in result:
            active_ips.append(received.psrc)
            logging.info("Active IP detected: %s", received.psrc)
        
        return active_ips
    except Exception as e:
        logging.error("Error with Scapy: %s", str(e))
        return []

# Alternative 3: Simple ping-based scanning
def scan_network_with_ping():
    """Scan network using ping (platform independent)"""
    try:
        network = netaddr.IPNetwork(ip_range)
        active_ips = []
        
        for ip in network.iter_hosts():
            ip_str = str(ip)
            try:
                # Use platform-specific ping command
                if platform.system().lower() == "windows":
                    response = subprocess.run(['ping', '-n', '1', '-w', '1000', ip_str], 
                                           capture_output=True, text=True, timeout=2)
                else:
                    response = subprocess.run(['ping', '-c', '1', '-W', '1', ip_str], 
                                           capture_output=True, text=True, timeout=2)
                
                if response.returncode == 0:
                    active_ips.append(ip_str)
                    logging.info("Active IP detected: %s", ip_str)
            except subprocess.TimeoutExpired:
                continue
            except Exception as e:
                logging.error("Error pinging %s: %s", ip_str, str(e))
        
        return active_ips
    except Exception as e:
        logging.error("Error with ping scan: %s", str(e))
        return []

# Choose scanning method (you can change this)
SCAN_METHOD = "scapy"  # Options: "nmap_lib", "scapy", "ping"

if SCAN_METHOD == "nmap_lib":
    active_ips = scan_network_with_nmap_lib()
elif SCAN_METHOD == "scapy":
    active_ips = scan_network_with_scapy()
else:
    active_ips = scan_network_with_ping()

logging.info("Network scan completed. Found %d active IPs", len(active_ips))

# Function to get the local machine's uptime using psutil
def get_local_uptime():
    try:
        boot_time = psutil.boot_time()
        current_time = time.time()
        uptime_seconds = current_time - boot_time
        uptime = timedelta(seconds=uptime_seconds)

        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        uptime_str = f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"
        return uptime_str
    except Exception as e:
        logging.error("Error fetching local uptime: %s", str(e))
        return f"Error: {str(e)}"

# Function to get local OS information
def get_os_info():
    try:
        system = platform.system()
        release = platform.release()
        version = platform.version()
        os_info = f"System: {system}<br>Release: {release}<br>Version: {version}"
        return os_info
    except Exception as e:
        logging.error("Error fetching OS information: %s", str(e))
        return f"Error: {str(e)}"

# Function to scan ports using python-nmap
def scan_ports_with_nmap_lib(ip, ports="22,23,25,53,80,110,143,443,993,995,3389"):
    """Scan specific ports on an IP using python-nmap"""
    try:
        nm = nmap.PortScanner()
        nm.scan(ip, ports)
        
        open_ports = []
        if ip in nm.all_hosts():
            for proto in nm[ip].all_protocols():
                ports_info = nm[ip][proto]
                for port, info in ports_info.items():
                    if info['state'] == 'open':
                        service = info.get('name', 'unknown')
                        open_ports.append(f"{port}/tcp {service}")
        
        return open_ports
    except Exception as e:
        logging.error("Error scanning ports for %s: %s", ip, str(e))
        return []

# Function to check RDP port using socket
def check_rdp_port(ip, port=3389):
    """Check if RDP port is open using socket connection"""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception as e:
        logging.error("Error checking RDP port for %s: %s", ip, str(e))
        return False

inactive_ips = []
rdp_users = {}
uptime_info = {}
services_and_ports = {}
local_uptime = get_local_uptime()
os_info = get_os_info()

# Generate inactive IPs list
network = netaddr.IPNetwork(ip_range)
for ip in network.iter_hosts():
    ip_str = str(ip)
    if ip_str not in active_ips:
        inactive_ips.append(ip_str)

# Gather RDP, uptime, and service/port information for active IPs
for ip in active_ips:
    try:
        logging.info("Scanning IP: %s", ip)
        
        # Check RDP port
        if check_rdp_port(ip):
            rdp_users[ip] = "RDP is open"
        else:
            rdp_users[ip] = "RDP is not open"

        # Scan ports and services
        open_ports = scan_ports_with_nmap_lib(ip)
        services_and_ports[ip] = open_ports
        
        for port_info in open_ports:
            logging.info("Service/Port info for %s: %s", ip, port_info)

        # For uptime, we'll use a simple approach since OS detection is complex
        uptime_info[ip] = "Uptime information not available (requires advanced OS detection)"

    except Exception as e:
        logging.error("Error scanning IP %s: %s", ip, str(e))

# Generate the HTML report
with open("app_alternative.html", "w") as f:
    f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NetManager - Network Dashboard (Alternative)</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --discord-dark: #36393f;
            --discord-darker: #2f3136;
            --discord-darkest: #202225;
            --discord-light: #40444b;
            --discord-lighter: #4f545c;
            --discord-accent: #7289da;
            --discord-accent-hover: #677bc4;
            --discord-green: #43b581;
            --discord-red: #f04747;
            --discord-yellow: #faa61a;
            --discord-text: #dcddde;
            --discord-text-muted: #72767d;
            --discord-border: #40444b;
            --discord-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Whitney', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            background-color: var(--discord-dark);
            color: var(--discord-text);
            line-height: 1.5;
            overflow-x: hidden;
        }

        .app-container {
            display: flex;
            height: 100vh;
        }

        /* Sidebar */
        .sidebar {
            width: 240px;
            background-color: var(--discord-darker);
            border-right: 1px solid var(--discord-border);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }

        .sidebar-header {
            padding: 16px;
            border-bottom: 1px solid var(--discord-border);
            background-color: var(--discord-darkest);
        }

        .sidebar-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--discord-text);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .sidebar-title i {
            color: var(--discord-accent);
        }

        .sidebar-nav {
            flex: 1;
            padding: 8px;
        }

        .nav-section {
            margin-bottom: 8px;
        }

        .nav-section-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--discord-text-muted);
            text-transform: uppercase;
            letter-spacing: 0.02em;
            padding: 8px 8px 4px 8px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s ease;
            color: var(--discord-text-muted);
            text-decoration: none;
            font-size: 14px;
        }

        .nav-item:hover {
            background-color: var(--discord-light);
            color: var(--discord-text);
        }

        .nav-item.active {
            background-color: var(--discord-accent);
            color: white;
        }

        .nav-item i {
            width: 20px;
            text-align: center;
        }

        .sidebar-footer {
            padding: 16px;
            border-top: 1px solid var(--discord-border);
            background-color: var(--discord-darkest);
        }

        .user-info {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
        }

        .user-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background-color: var(--discord-accent);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 600;
        }

        /* Main content */
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            background-color: var(--discord-dark);
        }

        .content-header {
            padding: 16px 24px;
            border-bottom: 1px solid var(--discord-border);
            background-color: var(--discord-darker);
        }

        .content-title {
            font-size: 20px;
            font-weight: 600;
            color: var(--discord-text);
        }

        .content-subtitle {
            font-size: 14px;
            color: var(--discord-text-muted);
            margin-top: 4px;
        }

        .content-body {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
        }

        /* Dashboard cards */
        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }

        .card {
            background-color: var(--discord-darker);
            border-radius: 8px;
            padding: 20px;
            border: 1px solid var(--discord-border);
            box-shadow: var(--discord-shadow);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }

        .card-icon {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }

        .card-icon.green {
            background-color: var(--discord-green);
        }

        .card-icon.red {
            background-color: var(--discord-red);
        }

        .card-icon.blue {
            background-color: var(--discord-accent);
        }

        .card-icon.yellow {
            background-color: var(--discord-yellow);
        }

        .card-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--discord-text);
        }

        .card-subtitle {
            font-size: 12px;
            color: var(--discord-text-muted);
        }

        .card-content {
            color: var(--discord-text);
        }

        .ip-list {
            list-style: none;
            margin: 0;
            padding: 0;
        }

        .ip-item {
            padding: 8px 0;
            border-bottom: 1px solid var(--discord-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .ip-item:last-child {
            border-bottom: none;
        }

        .ip-address {
            font-family: 'Courier New', monospace;
            font-weight: 600;
        }

        .ip-status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-online {
            background-color: var(--discord-green);
            color: white;
        }

        .status-offline {
            background-color: var(--discord-red);
            color: white;
        }

        .status-rdp {
            background-color: var(--discord-accent);
            color: white;
        }

        /* Tables */
        .table-container {
            background-color: var(--discord-darker);
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--discord-border);
            margin-bottom: 24px;
        }

        .table-header {
            background-color: var(--discord-darkest);
            padding: 16px 20px;
            border-bottom: 1px solid var(--discord-border);
        }

        .table-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--discord-text);
        }

        .table {
            width: 100%;
            border-collapse: collapse;
        }

        .table th,
        .table td {
            padding: 12px 20px;
            text-align: left;
            border-bottom: 1px solid var(--discord-border);
        }

        .table th {
            background-color: var(--discord-darkest);
            font-weight: 600;
            color: var(--discord-text-muted);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }

        .table td {
            color: var(--discord-text);
        }

        .table tr:hover {
            background-color: var(--discord-light);
        }

        /* Responsive */
        @media (max-width: 768px) {
            .app-container {
                flex-direction: column;
            }

            .sidebar {
                width: 100%;
                height: auto;
            }

            .dashboard-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Sidebar -->
        <div class="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-title">
                    <i class="fas fa-network-wired"></i>
                    NetManager 3.0
                </div>
            </div>
            
            <div class="sidebar-nav">
                <div class="nav-section">
                    <div class="nav-section-title">Main</div>
                    <a href="#" class="nav-item active">
                        <i class="fas fa-tachometer-alt"></i>
                        Dashboard
                    </a>
                    <a href="#" class="nav-item">
                        <i class="fas fa-chart-line"></i>
                        Analytics
                    </a>
                </div>
                
                <div class="nav-section">
                    <div class="nav-section-title">Network</div>
                    <a href="#" class="nav-item">
                        <i class="fas fa-satellite-dish"></i>
                        Scan Network
                    </a>
                    <a href="#" class="nav-item">
                        <i class="fas fa-shield-alt"></i>
                        Security
                    </a>
                    <a href="#" class="nav-item">
                        <i class="fas fa-cogs"></i>
                        Settings
                    </a>
                </div>
                
                <div class="nav-section">
                    <div class="nav-section-title">Communication</div>
                    <a href="#" class="nav-item">
                        <i class="fas fa-comments"></i>
                        Chat
                    </a>
                    <a href="#" class="nav-item">
                        <i class="fas fa-bell"></i>
                        Notifications
                    </a>
                </div>
            </div>
            
            <div class="sidebar-footer">
                <div class="user-info">
                    <div class="user-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                    <div>
                        <div>Administrator</div>
                        <div style="font-size: 12px; color: var(--discord-text-muted);">Online</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <div class="main-content">
            <div class="content-header">
                <div class="content-title">Network Dashboard</div>
                <div class="content-subtitle">Real-time network monitoring and management</div>
            </div>
            
            <div class="content-body">
                <!-- Dashboard Cards -->
                <div class="dashboard-grid">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon green">
                                <i class="fas fa-wifi"></i>
                            </div>
                            <div>
                                <div class="card-title">Active Devices</div>
                                <div class="card-subtitle">Currently online</div>
                            </div>
                        </div>
                        <div class="card-content">
                            <div style="font-size: 32px; font-weight: 700; color: var(--discord-green);">
                                """ + str(len(active_ips)) + """
                            </div>
                            <div style="font-size: 14px; color: var(--discord-text-muted); margin-top: 8px;">
                                devices detected
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon red">
                                <i class="fas fa-times-circle"></i>
                            </div>
                            <div>
                                <div class="card-title">Inactive Devices</div>
                                <div class="card-subtitle">Offline or unreachable</div>
                            </div>
                        </div>
                        <div class="card-content">
                            <div style="font-size: 32px; font-weight: 700; color: var(--discord-red);">
                                """ + str(len(inactive_ips)) + """
                            </div>
                            <div style="font-size: 14px; color: var(--discord-text-muted); margin-top: 8px;">
                                devices offline
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon blue">
                                <i class="fas fa-desktop"></i>
                            </div>
                            <div>
                                <div class="card-title">RDP Enabled</div>
                                <div class="card-subtitle">Remote desktop access</div>
                            </div>
                        </div>
                        <div class="card-content">
                            <div style="font-size: 32px; font-weight: 700; color: var(--discord-accent);">
                                """ + str(len([ip for ip, status in rdp_users.items() if "open" in status])) + """
                            </div>
                            <div style="font-size: 14px; color: var(--discord-text-muted); margin-top: 8px;">
                                devices with RDP
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon yellow">
                                <i class="fas fa-clock"></i>
                            </div>
                            <div>
                                <div class="card-title">System Uptime</div>
                                <div class="card-subtitle">Local machine</div>
                            </div>
                        </div>
                        <div class="card-content">
                            <div style="font-size: 16px; font-weight: 600; color: var(--discord-yellow);">
                                """ + local_uptime + """
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Active Devices Table -->
                <div class="table-container">
                    <div class="table-header">
                        <div class="table-title">Active Network Devices</div>
                    </div>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>IP Address</th>
                                <th>Status</th>
                                <th>RDP Status</th>
                                <th>Services</th>
                                <th>Uptime</th>
                            </tr>
                        </thead>
                        <tbody>
""")

    # Add active devices to table
    for ip in active_ips:
        rdp_status = rdp_users.get(ip, "Unknown")
        services = services_and_ports.get(ip, [])
        uptime = uptime_info.get(ip, "Unknown")
        
        services_text = "<br>".join(services[:3])  # Show first 3 services
        if len(services) > 3:
            services_text += f"<br>... and {len(services) - 3} more"
        
        f.write(f"""
                            <tr>
                                <td><span class="ip-address">{ip}</span></td>
                                <td><span class="ip-status status-online">Online</span></td>
                                <td>{rdp_status}</td>
                                <td>{services_text if services_text else 'No services detected'}</td>
                                <td>{uptime}</td>
                            </tr>
""")

    f.write("""
                        </tbody>
                    </table>
                </div>

                <!-- System Information -->
                <div class="table-container">
                    <div class="table-header">
                        <div class="table-title">System Information</div>
                    </div>
                    <table class="table">
                        <tbody>
                            <tr>
                                <td><strong>Operating System</strong></td>
                                <td>""" + os_info + """</td>
                            </tr>
                            <tr>
                                <td><strong>Scan Method</strong></td>
                                <td>""" + SCAN_METHOD.upper() + """ (Python Libraries)</td>
                            </tr>
                            <tr>
                                <td><strong>Network Range</strong></td>
                                <td>""" + ip_range + """</td>
                            </tr>
                            <tr>
                                <td><strong>Scan Time</strong></td>
                                <td>""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        // Add any JavaScript functionality here
        console.log('NetManager Dashboard loaded successfully');
    </script>
</body>
</html>
""")

print("Alternative NetManager dashboard generated successfully!")
print(f"Active IPs found: {len(active_ips)}")
print(f"Inactive IPs: {len(inactive_ips)}")
print(f"RDP enabled devices: {len([ip for ip, status in rdp_users.items() if 'open' in status])}")

# Flask routes (same as original)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/api/network-scan')
def network_scan():
    return jsonify({
        'active_ips': active_ips,
        'inactive_ips': inactive_ips,
        'rdp_users': rdp_users,
        'uptime_info': uptime_info,
        'services_and_ports': services_and_ports,
        'local_uptime': local_uptime,
        'os_info': os_info
    })

# Socket.IO event handlers (same as original)
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('set_name')
def handle_set_name(data):
    name = data.get('name', 'Anonymous')
    ip = request.remote_addr
    
    chat_clients[request.sid] = (name, ip)
    ip_to_sid[ip] = request.sid
    
    # Join the main chat room
    join_room('main')
    
    # Notify others
    emit('user_joined', {
        'name': name,
        'ip': ip,
        'message': f'{name} joined the chat'
    }, room='main', include_self=False)
    
    # Send recent messages to new user
    for msg in chat_messages[-10:]:  # Last 10 messages
        emit('message', msg, room=request.sid)

@socketio.on('message')
def handle_message(data):
    message = data.get('message', '').strip()
    if not message:
        return
    
    name, ip = chat_clients.get(request.sid, ('Anonymous', request.remote_addr))
    
    msg_data = {
        'name': name,
        'ip': ip,
        'message': message,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }
    
    chat_messages.append(msg_data)
    if len(chat_messages) > MAX_MESSAGES:
        chat_messages.pop(0)
    
    emit('message', msg_data, room='main')

@socketio.on('typing')
def handle_typing(data):
    name, ip = chat_clients.get(request.sid, ('Anonymous', request.remote_addr))
    emit('typing', {'name': name}, room='main', include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing():
    name, ip = chat_clients.get(request.sid, ('Anonymous', request.remote_addr))
    emit('stop_typing', {'name': name}, room='main', include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in chat_clients:
        name, ip = chat_clients[request.sid]
        del chat_clients[request.sid]
        if ip in ip_to_sid:
            del ip_to_sid[ip]
        
        emit('user_left', {
            'name': name,
            'ip': ip,
            'message': f'{name} left the chat'
        }, room='main')

if __name__ == '__main__':
    print("Starting NetManager 3.0 (Alternative Version)")
    print("Using Python libraries instead of external Nmap")
    print(f"Scan method: {SCAN_METHOD}")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 