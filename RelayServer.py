import socket
import threading
import requests
import time
import dataclasses

@dataclasses.dataclass()
class Server:
    name: str
    password: str
    connection_waitlist: list[tuple[socket.socket, str]]
    clients: list[tuple[socket.socket, str]]
    host: socket.socket
    host_address: str
    
class Host:
    def __init__(self, port=9000):
        self.port = port
        self.passkey = 'I2)&[*G3gpDPS7nai"0H-q9Ro{>M;{i'
        self.servers: dict[str, Server] = {}
        self.public_ip = '0.0.0.0'

    def _update_ip(self):
        while True:
            try:
                self.public_ip = socket.gethostbyname('xraybotics.ddns.net')
                print(f'Ip updated: {self.public_ip}...')
            except:
                pass
            time.sleep(300)
    
    def setup(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('0.0.0.0', 9000))
        self.socket.listen()
        threading.Thread(target=self._update_ip, daemon=True).start()
        time.sleep(0.5)
        print(f'Relay server running on port {self.port}...')
        print(f'Public: {self.public_ip} Local: {socket.gethostbyname(socket.gethostname())}')

        while True:
            conn, addr = self.socket.accept()
            threading.Thread(target=self._new_connection, args=(conn, addr), daemon=True).start()
    
    def _new_connection(self, conn:socket.socket, addr):
        try:
            while True:
                recieved_code = conn.recv(1024).decode()
                print(recieved_code)
                if self.passkey in recieved_code and 'Get Servers' in recieved_code:
                    print(f'Getting servers for {addr}')
                    self.send_servers(conn, addr)
                else:
                    print('here')
                    break
            
            client_passkey, is_host, hostname, password = tuple(recieved_code.split('~'))
            is_host = True if is_host=='True' else False
            if client_passkey == self.passkey:
                if not is_host:
                    if hostname not in self.servers:
                        conn.send(f'Server "{hostname}" not set up...'.encode())
                        conn.close()
                        return
                    if password == self.servers[hostname].password:
                        print(f'Client {addr} joined {hostname}...')
                        conn.send('Connected'.encode())
                        self.servers[hostname].connection_waitlist.append((conn, addr))
                    else:
                        print(f'Client {addr} entered wrong password for {hostname}...')
                        conn.send('Incorrect Password!'.encode())
                        conn.close()
                        return
                else:
                    if hostname in self.servers:
                        print(f'Client {addr} tried to create duplicate {hostname}...')
                        conn.send('Hostname already exists...'.encode())
                        conn.close()
                        return
                    print(f'Client {addr} created {hostname}...')
                    conn.send('Connected'.encode())
                    self.servers.setdefault(hostname, Server(name=hostname, password=password, 
                                                             connection_waitlist=[], clients=[],
                                                             host=conn, host_address=addr))
                    threading.Thread(target=self.handle_server, args=(self.servers[hostname],), daemon=True).start()
                    return
            else:
                print(f'Client {addr} provided the wrong key')
                conn.send('Incorrect key!'.encode())
                conn.close()
                return
        except Exception as e:
            print(f'Client {addr} not from GUI\n{e}')
            conn.close()
            return

    def send_servers(self, conn: socket.socket, addr):
        serverlist = '~'.join(self.servers.keys())
        print(f'sending: {serverlist}')
        serverlist = 'None' if not serverlist else serverlist
        conn.send(serverlist.encode())

        
    def handle_server(self, server: Server):
        threading.Thread(target=self.handle_host, args=(server, server.host, server.host_address), daemon=True).start()
        server.clients.append((server.host, server.host_address))
        while True:
            for conn, addr in server.connection_waitlist:
                server.clients.append((conn, addr))
                threading.Thread(target=self.handle_client, args=(server, conn, addr), daemon=True).start()
                server.connection_waitlist.remove((conn, addr))
            time.sleep(0.5)

    def handle_host(self, server:Server, conn: socket.socket, addr):
        while True:
            try:
                data = conn.recv(1024)
                # Forward to all other clients
                for (c, addr) in server.clients:
                    if c != conn:
                        c.sendall(data)
            except:
                break
        try:
            conn.close()
        except:
            pass
        print('Host Disconnected')
        self._server_closed(server)
            

    def handle_client(self, server:Server, conn: socket.socket, addr):
        print(f"Handeling: {conn}\n{addr}\n\n")
        try:
            while server.host is not None:
                data = conn.recv(1024)
                # Forward to all other clients
                for (c, addr) in server.clients:
                    if c != conn:
                        try:
                            c.sendall(data)
                        except:
                            pass
        except Exception as e:
            print(e)
            pass
        print(f"Disconnected: {conn}\n{addr}")
        server.clients.remove((conn, addr))
        conn.close()
            
    def _server_closed(self, server:Server):
        print('Server Closing')
        try:
            for (c, addr) in server.clients:
                try:
                    c.sendall(f'Host {addr} has disconnected!'.encode())
                    c.close()
                except:
                    pass
        finally:
            server.host = None
            del self.servers[server.name]
            
            


relay_server = Host(9000)
threading.Thread(target=relay_server.setup).start()
