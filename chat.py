# app.py (Python code - same as before)
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, disconnect

app = Flask(__name__)
import os
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'default_secret_key')
socketio = SocketIO(app)

clients = {}  # sid -> (name, ip)
ip_to_sid = {}  # ip -> sid

@app.route('/')
def index():
    return render_template('chat.html')

@socketio.on('connect')
def handle_connect():
    ip = request.remote_addr
    if ip in ip_to_sid:
        # Disconnect previous session from this IP
        disconnect(sid=ip_to_sid[ip])
    ip_to_sid[ip] = request.sid
    # No name set yet

@socketio.on('set_name')
def handle_set_name(name):
    ip = request.remote_addr
    session['name'] = name
    clients[request.sid] = (name, ip)
    join_room('chatroom')
    emit('message', {'name': 'System', 'msg': f'{name} ({ip}) has joined the chat'}, room='chatroom')

@socketio.on('message')
def handle_message(msg):
    name, ip = clients.get(request.sid, ('Unknown', request.remote_addr))
    emit('message', {'name': f'{name} ({ip})', 'msg': msg}, room='chatroom')

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    ip = request.remote_addr
    if sid in clients:
        name, ip_addr = clients[sid]
        emit('message', {'name': 'System', 'msg': f'{name} ({ip_addr}) has left the chat'}, room='chatroom')
        del clients[sid]
    if ip in ip_to_sid and ip_to_sid[ip] == sid:
        del ip_to_sid[ip]

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=80, debug=True)