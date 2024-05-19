from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import paramiko
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

ssh_clients = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_ssh', methods=['POST'])
def add_ssh():
    data = request.json
    host = data['host']
    port = int(data['port'])
    username = data['username']
    password = data['password']
    pub_key = data.get('pub_key')

    ssh_id = f"{username}@{host}:{port}"

    ssh_clients[ssh_id] = {'client': None, 'thread': None}

    def ssh_thread(ssh_id, host, port, username, password, pub_key):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if pub_key:
                key = paramiko.RSAKey(data=base64.b64decode(pub_key.split()[1]))
                client.connect(host, port=port, username=username, pkey=key)
            else:
                client.connect(host, port=port, username=username, password=password)
        except Exception as e:
            emit('ssh_error', {'message': str(e)}, namespace='/', to=ssh_id)
            return

        ssh_clients[ssh_id]['client'] = client
        chan = client.invoke_shell()
        chan.setblocking(0)

        while True:
            if chan.recv_ready():
                data = chan.recv(1024).decode()
                socketio.emit('ssh_output', {'output': data}, namespace='/', to=ssh_id)

            socketio.sleep(0.1)

    ssh_clients[ssh_id]['thread'] = socketio.start_background_task(ssh_thread, ssh_id, host, port, username, password, pub_key)

    return jsonify({'ssh_id': ssh_id})

@socketio.on('ssh_input')
def handle_ssh_input(json):
    ssh_id = json['ssh_id']
    input_data = json['input']

    if ssh_id in ssh_clients and ssh_clients[ssh_id]['client']:
        chan = ssh_clients[ssh_id]['client'].invoke_shell()
        chan.send(input_data)

@app.route('/delete_ssh', methods=['POST'])
def delete_ssh():
    ssh_id = request.json['ssh_id']

    if ssh_id in ssh_clients:
        ssh_clients[ssh_id]['client'].close()
        ssh_clients.pop(ssh_id)

    return jsonify({'status': 'success'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
