import paramiko
import uuid

class SSHManager:
    def __init__(self):
        self.connections = {}

    def add_connection(self, host, port, username, password, pub_key):
        connection_id = str(uuid.uuid4())
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if pub_key:
                pkey = paramiko.RSAKey.from_private_key_file(pub_key)
                ssh.connect(hostname=host, port=port, username=username, pkey=pkey)
            else:
                ssh.connect(hostname=host, port=port, username=username, password=password)
            self.connections[connection_id] = ssh
            return connection_id
        except Exception as e:
            print(f"Failed to connect: {e}")
            return None

    def run_command(self, connection_id, command):
        ssh = self.connections.get(connection_id)
        if ssh:
            stdin, stdout, stderr = ssh.exec_command(command)
            return stdout.read().decode()
        return ""

    def remove_connection(self, connection_id):
        ssh = self.connections.pop(connection_id, None)
        if ssh:
            ssh.close()
