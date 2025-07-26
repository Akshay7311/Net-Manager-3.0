def generate_dashboard_html(
    os_info: str,
    local_uptime: str,
    active_ips: list,
    inactive_ips: list,
    rdp_users: dict,
    uptime_info: dict,
    services_and_ports: dict
):
    html_path = "templates/app.html"
    # Generate the HTML report
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NetManager - Network Dashboard</title>
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
                background-color: var(--discord-accent);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                color: white;
            }

            /* Main Content */
            .main-content {
                flex: 1;
                display: flex;
                flex-direction: column;
                background-color: var(--discord-dark);
            }

            .content-header {
                background-color: var(--discord-darker);
                border-bottom: 1px solid var(--discord-border);
                padding: 16px 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
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

            /* Cards */
            .card {
                background-color: var(--discord-darker);
                border: 1px solid var(--discord-border);
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 16px;
                box-shadow: var(--discord-shadow);
            }

            .card-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 16px;
            }

            .card-title {
                font-size: 16px;
                font-weight: 600;
                color: var(--discord-text);
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .card-title i {
                color: var(--discord-accent);
            }

            .card-content {
                color: var(--discord-text);
            }

            /* Grid Layouts */
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 12px;
            }

            .grid-item {
                background-color: var(--discord-light);
                border: 1px solid var(--discord-border);
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                transition: all 0.2s ease;
            }

            .grid-item:hover {
                background-color: var(--discord-lighter);
                transform: translateY(-1px);
            }

            .grid-item.active {
                border-color: var(--discord-green);
                background-color: rgba(67, 181, 129, 0.1);
            }

            .grid-item.inactive {
                border-color: var(--discord-red);
                background-color: rgba(240, 71, 71, 0.1);
            }

            /* Status Indicators */
            .status-indicator {
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                margin-right: 8px;
            }

            .status-online {
                background-color: var(--discord-green);
            }

            .status-offline {
                background-color: var(--discord-red);
            }

            .status-idle {
                background-color: var(--discord-yellow);
            }

            /* Buttons */
            .btn {
                background-color: var(--discord-accent);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s ease;
            }

            .btn:hover {
                background-color: var(--discord-accent-hover);
            }

            .btn-secondary {
                background-color: var(--discord-light);
                color: var(--discord-text);
            }

            .btn-secondary:hover {
                background-color: var(--discord-lighter);
            }

            /* Responsive */
            @media (max-width: 768px) {
                .sidebar {
                    position: fixed;
                    left: -240px;
                    top: 0;
                    bottom: 0;
                    z-index: 1000;
                    transition: left 0.3s ease;
                }

                .sidebar.open {
                    left: 0;
                }

                .content-header {
                    padding: 12px 16px;
                }

                .content-body {
                    padding: 16px;
                }

                .grid {
                    grid-template-columns: 1fr;
                }
            }

            /* Scrollbar */
            ::-webkit-scrollbar {
                width: 8px;
            }

            ::-webkit-scrollbar-track {
                background: var(--discord-darkest);
            }

            ::-webkit-scrollbar-thumb {
                background: var(--discord-light);
                border-radius: 4px;
            }

            ::-webkit-scrollbar-thumb:hover {
                background: var(--discord-lighter);
            }

            /* Animations */
            .fade-in {
                animation: fadeIn 0.3s ease-in;
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            /* Hidden by default */
            .content-section {
                display: none;
            }

            .content-section.active {
                display: block;
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
                        NetManager
                    </div>
                  
                </div>
                
                <nav class="sidebar-nav">
                    <div class="nav-section">
                        <div class="nav-section-title">System</div>
                        <a href="#" class="nav-item active" onclick="showSection('local-info')">
                            <i class="fas fa-desktop"></i>
                            Local Info
                        </a>
                    </div>
                    
                    <div class="nav-section">
                        <div class="nav-section-title">Network</div>
                        <a href="#" class="nav-item" onclick="showSection('active-ips')">
                            <i class="fas fa-wifi"></i>
                            Active IPs
                        </a>
                        <a href="#" class="nav-item" onclick="showSection('inactive-ips')">
                            <i class="fas fa-times-circle"></i>
                            Inactive IPs
                        </a>
                        <a href="#" class="nav-item" onclick="showSection('rdp-users')">
                            <i class="fas fa-users"></i>
                            RDP Status
                        </a>
                        <a href="#" class="nav-item" onclick="showSection('uptime-info')">
                            <i class="fas fa-clock"></i>
                            Uptime
                        </a>
                        <a href="#" class="nav-item" onclick="showSection('services-and-ports')">
                            <i class="fas fa-server"></i>
                            Services & Ports
                        </a>
                        <a href="/chat" class="nav-item" onclick="showSection('services-and-ports')">
                            <i class="fas fa-server"></i>
                            Chat
                        </a>
                    </div>
                </nav>
                
                <div class="sidebar-footer">
                    <div class="user-info">
                        <div class="user-avatar">N</div>
                        <div>
                            <div style="font-weight: 500;">Network Admin</div>
                            <div style="font-size: 12px; color: var(--discord-text-muted);">Online</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Main Content -->
            <div class="main-content">
                <div class="content-header">
                    <div>
                        <div class="content-title" id="content-title">Local System Information</div>
                        <div class="content-subtitle" id="content-subtitle">System details and configuration</div>
                    </div>
                    <div>
                        <span id="last-refresh-status" style="color: var(--discord-text-muted); font-size: 14px;">
                            Just now
                        </span>
                        <button id="refresh-btn" class="btn" onclick="refreshScan()">
                            <i class="fas fa-sync-alt"></i>
                            Refresh
                        </button>
                        <button class="btn" onclick="window.open('index.html', '_blank')">
                            <i class="fas fa-home"></i>
                            Back to Home
                        </button>
                    </div>
                </div>

                <div class="content-body">
                    <!-- Local Info Section -->
                    <div id="local-info" class="content-section active fade-in">
                        <div class="card">
                            <div class="card-header">
                                <div class="card-title">
                                    <i class="fas fa-info-circle"></i>
                                    System Information
                                </div>
                            </div>
                            <div class="card-content">
                                <div style="margin-bottom: 16px;">
                                    <strong>OS Information:</strong><br>
                                    """ + os_info.replace('<br>', '<br>') + """
                                </div>
                                <div>
                                    <strong>Uptime:</strong><br>
                                    """ + local_uptime + """
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Active IPs Section -->
                    <div id="active-ips" class="content-section">
                        <div class="card">
                            <div class="card-header">
                                <div class="card-title">
                                    <i class="fas fa-check-circle"></i>
                                    Active IP Addresses
                                </div>
                                <div style="color: var(--discord-text-muted); font-size: 14px;">
                                    """ + str(len(active_ips)) + """ devices online
                                </div>
                            </div>
                            <div class="card-content">
                                <div class="grid">
        """)
        
        for ip in active_ips:
            f.write(f"""
                                    <div class="grid-item active">
                                        <span class="status-indicator status-online"></span>
                                        {ip}
                                    </div>
            """)

        f.write("""
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Inactive IPs Section -->
                    <div id="inactive-ips" class="content-section">
                        <div class="card">
                            <div class="card-header">
                                <div class="card-title">
                                    <i class="fas fa-times-circle"></i>
                                    Inactive IP Addresses
                                </div>
                                <div style="color: var(--discord-text-muted); font-size: 14px;">
                                    """ + str(len(inactive_ips)) + """ devices offline
                                </div>
                            </div>
                            <div class="card-content">
                                <div class="grid">
        """)

        for ip in inactive_ips:
            f.write(f"""
                                    <div class="grid-item inactive">
                                        <span class="status-indicator status-offline"></span>
                                        {ip}
                                    </div>
            """)

        f.write("""
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- RDP Users Section -->
                    <div id="rdp-users" class="content-section">
                        <div class="card">
                            <div class="card-header">
                                <div class="card-title">
                                    <i class="fas fa-users"></i>
                                    Remote Desktop Protocol Status
                                </div>
                            </div>
                            <div class="card-content">
                                <div class="grid">
        """)

        for ip, status in rdp_users.items():
            status_class = "active" if "open" in status else "inactive"
            status_icon = "status-online" if "open" in status else "status-offline"
            f.write(f"""
                                    <div class="grid-item {status_class}">
                                        <span class="status-indicator {status_icon}"></span>
                                        <strong>{ip}:</strong><br>
                                        {status}
                                    </div>
            """)

        f.write("""
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Uptime Info Section -->
                    <div id="uptime-info" class="content-section">
                        <div class="card">
                            <div class="card-header">
                                <div class="card-title">
                                    <i class="fas fa-clock"></i>
                                    System Uptime Information
                                </div>
                            </div>
                            <div class="card-content">
                                <div class="grid">
        """)

        for ip, uptime in uptime_info.items():
            f.write(f"""
                                    <div class="grid-item">
                                        <span class="status-indicator status-idle"></span>
                                        <strong>{ip}:</strong><br>
                                        {uptime}
                                    </div>
            """)

        f.write("""
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Services and Ports Section -->
                    <div id="services-and-ports" class="content-section">
                        <div class="card">
                            <div class="card-header">
                                <div class="card-title">
                                    <i class="fas fa-server"></i>
                                    Open Ports and Services
                                </div>
                            </div>
                            <div class="card-content">
                                <div class="grid">
        """)

        for ip, services in services_and_ports.items():
            f.write(f"""
                                    <div class="grid-item">
                                        <span class="status-indicator status-online"></span>
                                        <strong>{ip}:</strong><br>
                                        """ + "<br>".join(services) + """
                                    </div>
            """)

        f.write("""
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
                    function setLastRefreshed() {
                const now = new Date();
                localStorage.setItem("lastRefresh", now.toISOString());
                updateLastRefreshed();
            }

            function updateLastRefreshed() {
                const lastRefresh = localStorage.getItem("lastRefresh");
                const display = document.getElementById("last-refresh-status");

                if (!lastRefresh) {
                    display.textContent = "Unknown";
                    return;
                }

                const last = new Date(lastRefresh);
                const now = new Date();
                const diffMs = now - last;
                const diffMins = Math.floor(diffMs / (1000 * 60));
                const diffHours = Math.floor(diffMins / 60);
                const diffDays = Math.floor(diffHours / 24);

                if (diffMins < 1) {
                    display.textContent = "Just now";
                } else if (diffMins < 60) {
                    display.textContent = `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
                } else if (diffHours < 24) {
                    display.textContent = `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
                } else {
                    display.textContent = `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
                }
            }

            async function refreshScan() {
                const button = document.getElementById("refresh-btn");
                button.disabled = true;
                button.innerText = "Refreshing...";
                const res = await fetch("/api/network-scan");
                setLastRefreshed(); // <-- Save time
                location.reload();   // Reloads HTML
            }
            
            function showSection(sectionId) {
                // Hide all sections
                const sections = document.querySelectorAll('.content-section');
                sections.forEach(section => {
                    section.classList.remove('active');
                });

                // Show selected section
                const selectedSection = document.getElementById(sectionId);
                selectedSection.classList.add('active');
                selectedSection.classList.add('fade-in');

                // Update navigation
                const navItems = document.querySelectorAll('.nav-item');
                navItems.forEach(item => {
                    item.classList.remove('active');
                });
                event.target.classList.add('active');

                // Update header
                updateHeader(sectionId);
            }
                    document.addEventListener('DOMContentLoaded', () => {
                        updateLastRefreshed();

                        // Optionally update every 30 seconds for live display
                        setInterval(updateLastRefreshed, 30000);
                    });

            function updateHeader(sectionId) {
                const titles = {
                    'local-info': {
                        title: 'Local System Information',
                        subtitle: 'System details and configuration'
                    },
                    'active-ips': {
                        title: 'Active IP Addresses',
                        subtitle: 'Currently online devices on the network'
                    },
                    'inactive-ips': {
                        title: 'Inactive IP Addresses',
                        subtitle: 'Offline devices on the network'
                    },
                    'rdp-users': {
                        title: 'Remote Desktop Protocol Status',
                        subtitle: 'RDP accessibility for network devices'
                    },
                    'uptime-info': {
                        title: 'System Uptime Information',
                        subtitle: 'Device uptime and availability'
                    },
                    'services-and-ports': {
                        title: 'Open Ports and Services',
                        subtitle: 'Active services and open ports'
                    }
                };

                const header = titles[sectionId];
                document.getElementById('content-title').textContent = header.title;
                document.getElementById('content-subtitle').textContent = header.subtitle;
            }

            // Mobile menu toggle
            function toggleSidebar() {
                const sidebar = document.querySelector('.sidebar');
                sidebar.classList.toggle('open');
            }

            // Initialize
            document.addEventListener('DOMContentLoaded', function() {
                // Add mobile menu button if needed
                if (window.innerWidth <= 768) {
                    const header = document.querySelector('.content-header');
                    const menuBtn = document.createElement('button');
                    menuBtn.innerHTML = '<i class="fas fa-bars"></i>';
                    menuBtn.className = 'btn btn-secondary';
                    menuBtn.style.marginRight = '12px';
                    menuBtn.onclick = toggleSidebar;
                    header.insertBefore(menuBtn, header.firstChild);
                }
            });
        </script>
    </body>
    </html>
        """)

        print("HTML file with complete information generated successfully.")
