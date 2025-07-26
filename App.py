import os
import platform
import subprocess
import psutil
import time
import logging
from html_generator import generate_dashboard_html
from datetime import timedelta, datetime
from flask import Flask, render_template, request, session, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import threading
import concurrent.futures
NMAP = r"C:\Program Files (x86)\Nmap\nmap.exe"
    

# Set up logging
logging.basicConfig(
    filename="scan_logs.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

ip_range = "192.168.126.1/24"

logging.info("Starting network scan for range: %s", ip_range)

nmap_output = subprocess.check_output([NMAP, "-sn", ip_range])

logging.info("Nmap scan completed for IP range.")

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

def parse_nmap_output(nmap_output):
    active_ips = []
    for line in nmap_output.decode("utf-8").splitlines():
        if "Nmap scan report for" in line:
            ip = line.split()[-1]
            active_ips.append(ip)
            logging.info("Active IP detected: %s", ip)
    return active_ips

def get_inactive_ips(active_ips, base_ip="192.168.126"):
    inactive_ips = []
    for i in range(1, 255):
        ip = f"{base_ip}.{i}"
        if ip not in active_ips:
            inactive_ips.append(ip)
    return inactive_ips

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

def scan_hosts_concurrently(active_ips):
    rdp_users = {}
    uptime_info = {}
    services_and_ports = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_results = executor.map(scan_host, active_ips)
        for ip, result in future_results:
            if result:
                rdp_users[ip] = result["rdp"]
                uptime_info[ip] = result["uptime"]
                services_and_ports[ip] = result["ports"]
    return rdp_users, uptime_info, services_and_ports

def generate_dashboard():
    logging.info("Starting network scan for range: %s", ip_range)
    try:
        nmap_output = subprocess.check_output([NMAP, "-sn", ip_range])
    except subprocess.CalledProcessError as e:
        logging.error("Nmap scan failed: %s", str(e))
        return

    active_ips = parse_nmap_output(nmap_output)
    inactive_ips = get_inactive_ips(active_ips)
    local_uptime = get_local_uptime()
    os_info = get_os_info()
    rdp_users, uptime_info, services_and_ports = scan_hosts_concurrently(active_ips)

    generate_dashboard_html(
        os_info=os_info,
        local_uptime=local_uptime,
        active_ips=active_ips,
        inactive_ips=inactive_ips,
        rdp_users=rdp_users,
        uptime_info=uptime_info,
        services_and_ports=services_and_ports
    )


if __name__ == '__main__':
    generate_dashboard()