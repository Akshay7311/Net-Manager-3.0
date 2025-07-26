import subprocess
from datetime import  datetime
from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from App import get_local_uptime,ip_range,get_os_info
from html_generator import generate_dashboard_html
import logging

# Initialize Flask app
app = Flask(__name__)
import os
app.config['SECRET_KEY'] = os.environ.get('NETMANAGER_SECRET_KEY', 'default_secret_key')
socketio = SocketIO(app, cors_allowed_origins="*")

logging.basicConfig(
    filename="scan_logs.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.info("Starting Flask server")

# Chat-related variables
chat_clients = {}  # sid -> (name, ip)
ip_to_sid = {}  # ip -> sid
chat_messages = []  # Store recent messages
MAX_MESSAGES = 100  # Keep last 100 messages


# Flask Routes
@app.route('/')
def index():
    return render_template('app.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/api/network-scan')
def network_scan():
    """API endpoint to trigger network scan and return results"""
    try:
        import concurrent.futures
        NMAP = r"C:\Program Files (x86)\Nmap\nmap.exe"
        # Run the network scanning logic
        active_ips = []
        inactive_ips = []
        rdp_users = {}
        uptime_info = {}
        services_and_ports = {}
        
        # Get local system info
        local_uptime = get_local_uptime()
        os_info = get_os_info()
        
        # Run nmap scan
        nmap_output = subprocess.check_output([NMAP, "-sn", "--max-retries", "2", "--host-timeout", "30s", "-T4", ip_range])
        
        # Parse results
        for line in nmap_output.decode("utf-8").splitlines():
            if "Nmap scan report for" in line:
                ip = line.split()[-1]
                active_ips.append(ip)
        
        # Identify inactive IPs
        for i in range(1, 255):
            ip = f"10.25.1.{i}"
            if ip not in active_ips:
                inactive_ips.append(ip)
        
    
        
        def scan_host(ip):
            try:
                host_result = {
                    "rdp": "RDP is not open",
                    "uptime": "",
                    "ports": []
                }

                rdp_out = subprocess.check_output([NMAP, "-p", "3389", "--open", "-T4", ip])
                if "open" in rdp_out.decode("utf-8"):
                    host_result["rdp"] = "RDP is open"

                os_out = subprocess.check_output([NMAP, "-O", "-T4", ip])
                for line in os_out.decode("utf-8").splitlines():
                    if "Uptime guess" in line:
                        host_result["uptime"] = line.strip()
                        break

                port_out = subprocess.check_output([NMAP, "-sV", "--top-ports", "20", "-T4", ip])
                for line in port_out.decode("utf-8").splitlines():
                    if "/tcp" in line and "open" in line:
                        host_result["ports"].append(line.strip())

                return ip, host_result

            except subprocess.CalledProcessError:
                return ip, None

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_results = executor.map(scan_host, active_ips)
            for ip, result in future_results:
                if result:
                    rdp_users[ip] = result["rdp"]
                    uptime_info[ip] = result["uptime"]
                    services_and_ports[ip] = result["ports"]

        generate_dashboard_html(
        os_info=os_info,
        local_uptime=local_uptime,
        active_ips=active_ips,
        inactive_ips=inactive_ips,
        rdp_users=rdp_users,
        uptime_info=uptime_info,
        services_and_ports=services_and_ports
        )
        
        return jsonify({"status": "success", "message": "Dashboard regenerated."})
        
    except Exception as e:
        logging.error("Error in network scan API: %s", str(e))
        return jsonify({'success': False, 'error': str(e)})

# SocketIO Event Handlers
@socketio.on('connect')
def handle_connect():
    ip = request.remote_addr
    print(f"Client connected: {ip}")
    if ip in ip_to_sid:
        # Disconnect previous session from this IP
        disconnect(sid=ip_to_sid[ip])
    ip_to_sid[ip] = request.sid
    emit('system_message', {'msg': f'Connected from {ip}'})

@socketio.on('set_name')
def handle_set_name(data):
    name = data if isinstance(data, str) else data.get('name', 'Anonymous')
    ip = request.remote_addr
    session['name'] = name
    chat_clients[request.sid] = (name, ip)
    join_room('chatroom')
    
    # Send join message
    join_msg = {
        'type': 'join',
        'name': name,
        'ip': ip,
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'msg': f'{name} ({ip}) has joined the chat'
    }
    chat_messages.append(join_msg)
    if len(chat_messages) > MAX_MESSAGES:
        chat_messages.pop(0)
    
    emit('message', join_msg, room='chatroom')
    emit('user_list', {'users': list(chat_clients.values())}, room='chatroom')

@socketio.on('message')
def handle_message(data):
    msg = data.get('message', '')
    if not msg.strip():
        return
    
    name, ip = chat_clients.get(request.sid, ('Unknown', request.remote_addr))
    
    message_data = {
        'type': 'message',
        'name': name,
        'ip': ip,
        'message': msg,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }
    
    chat_messages.append(message_data)
    if len(chat_messages) > MAX_MESSAGES:
        chat_messages.pop(0)
    
    emit('message', message_data, room='chatroom')

@socketio.on('typing')
def handle_typing(data):
    name, ip = chat_clients.get(request.sid, ('Unknown', request.remote_addr))
    emit('typing', {'name': name, 'ip': ip}, room='chatroom', include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing():
    name, ip = chat_clients.get(request.sid, ('Unknown', request.remote_addr))
    emit('stop_typing', {'name': name, 'ip': ip}, room='chatroom', include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    ip = request.remote_addr
    
    if sid in chat_clients:
        name, ip_addr = chat_clients[sid]
        leave_msg = {
            'type': 'leave',
            'name': name,
            'ip': ip_addr,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'msg': f'{name} ({ip_addr}) has left the chat'
        }
        chat_messages.append(leave_msg)
        if len(chat_messages) > MAX_MESSAGES:
            chat_messages.pop(0)
        
        emit('message', leave_msg, room='chatroom')
        del chat_clients[sid]
        
        # Update user list
        emit('user_list', {'users': list(chat_clients.values())}, room='chatroom')
    
    if ip in ip_to_sid and ip_to_sid[ip] == sid:
        del ip_to_sid[ip]

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=80, debug=True)
