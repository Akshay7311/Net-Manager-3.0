# NetManager 3.0

A comprehensive network monitoring and management tool built with Python Flask and modern web technologies.

## Features

- 🔍 **Network Discovery**: Scan and discover devices on your network
- 📊 **Real-time Dashboard**: Beautiful Discord-inspired UI for network monitoring
- 💬 **Real-time Chat**: Built-in chat system for team communication
- 🔐 **RDP Detection**: Identify devices with Remote Desktop Protocol enabled
- 📈 **Service Monitoring**: Detect open ports and running services
- ⏱️ **Uptime Tracking**: Monitor system uptime and availability
- 🎨 **Modern UI**: Responsive design with Discord-like interface

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Akshay7311/Net-Manager-3.0.git
   cd Net-Manager-3.0
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   # Original version (requires Nmap installation)
   python App.py
   
   # Alternative version (uses Python libraries only)
   python App_alternative.py
   ```

4. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - The dashboard will be available at `http://localhost:5000/dashboard`

## Usage

### Network Scanning

The application supports multiple scanning methods:

1. **Original Method**: Uses external Nmap installation
   - Requires Nmap to be installed on your system
   - More comprehensive scanning capabilities

2. **Alternative Method**: Uses Python libraries only
   - No external dependencies required
   - Faster and more portable
   - Supports Scapy, python-nmap, and ping-based scanning

### Configuration

You can modify the scanning configuration in the application:

- **IP Range**: Change `ip_range` variable (default: "192.168.1.1/24")
- **Scan Method**: Choose between different scanning approaches
- **Ports**: Customize which ports to scan for services

## Project Structure

```
NetManager 3.0/
├── App.py                    # Main application (requires Nmap)
├── App_alternative.py        # Alternative version (Python libraries only)
├── requirements.txt          # Python dependencies
├── README.md                # This file
├── .gitignore               # Git ignore rules
├── Frontend/                # Frontend assets
│   ├── Css/                 # Stylesheets
│   ├── Scripts/             # JavaScript files
│   └── *.html              # HTML pages
├── app.html                 # Generated dashboard
├── app_alternative.html     # Alternative dashboard
└── scan_logs.log           # Application logs
```

## Dependencies

### Core Dependencies
- **Flask**: Web framework
- **Flask-SocketIO**: Real-time communication
- **psutil**: System and process utilities

### Network Scanning Dependencies
- **scapy**: Packet manipulation and network scanning
- **python-nmap**: Python wrapper for Nmap functionality
- **netaddr**: Network address manipulation

## Features in Detail

### Network Discovery
- Automatic IP range scanning
- Device status detection (online/offline)
- MAC address resolution
- Network topology mapping