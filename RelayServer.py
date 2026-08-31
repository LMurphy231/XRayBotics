import socket
import threading
import requests
import time
import dataclasses
from utill import consts
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler("RelayServer.log"),      # Log to a file
        logging.StreamHandler(sys.stdout)   # Log to the terminal
    ]
)

@dataclasses.dataclass()
class Server:
    name: str
    password: str
    connection_waitlist: list[tuple[socket.socket, str]]
    clients: list[tuple[socket.socket, str]]
    host: socket.socket
    host_address: str
    
class Host:
    def __init__(self):
        self.servers: dict[str, Server] = {}
        self.public_ip = '0.0.0.0'

    def _update_ip(self):
        while True:
            try:
                self.public_ip = socket.gethostbyname('xraybotics.ddns.net')
                logging.debug(f'Ip updated: {self.public_ip}...')
            except:
                pass
            time.sleep(300)
    
    def setup(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((consts._HOST, consts._PORT))
        self.socket.listen()
        threading.Thread(target=self._update_ip, daemon=True).start()
        time.sleep(0.5)
        logging.info(f'Relay server running on port {consts._PORT}...')
        logging.info(f'Public: {self.public_ip} Local: {socket.gethostbyname(socket.gethostname())}')

        while True:
            conn, addr = self.socket.accept()
            logging.info(f'Connection attempt by: {addr}')
            threading.Thread(target=self._new_connection, args=(conn, addr), daemon=True).start()
    
    def send(self, conn:socket.socket, message):
        try:
            return conn.sendall((str(message)+consts._DELIMITER).encode(encoding=consts._ENCODING))
        except Exception as e:
            raise e
        
    def listen(self, conn:socket.socket, bufsize=1024, decode=True, delimiter=consts._DELIMITER):
        try:    
            data = bytearray()
            while True:
                packet = conn.recv(bufsize)
                if not packet:
                    break
                data.extend(packet)
                if bytes(delimiter, encoding=consts._ENCODING) in packet:
                    break
            
            return data.decode(encoding=consts._ENCODING).replace(delimiter, '') if decode else data[:-len(bytes(delimiter))]
        except Exception as e:
            logging.warning(data)
            logging.warning(e)
            return None

    def _new_connection(self, conn:socket.socket, addr):
        try:
            recieved_code = self.listen(conn)
            if recieved_code != consts._PASSKEY:
                logging.info(f'Client {addr} provided the wrong key')
                self.send(conn, consts._MSG_INCORRECT_PASSKEY)
                conn.close()
                return
            self.send(conn, consts._MSG_PASSKEY_ACCEPTED)
            
            while True:
                code, return_data = self._handle_message(conn, addr, self.listen(conn), in_server=False)
                
                if code == consts._ACCEPT_CONNECTION:
                    (is_host, hostname, password) = return_data
                    if is_host:
                        logging.info(f'Client {addr} created {hostname}...')
                        self.send(conn, 'Connected')
                        self.servers.setdefault(hostname, Server(name=hostname, password=password, 
                                                                     connection_waitlist=[], clients=[],
                                                                     host=conn, host_address=addr))
                        threading.Thread(target=self.handle_server, args=(self.servers[hostname],), daemon=True).start()
                    else:
                        logging.info(f'Client {addr} joined {hostname}...')
                        self.send(conn, consts._MSG_JOIN_SUCCESS)
                        self.servers[hostname].connection_waitlist.append((conn, addr))
                    return
                elif code == consts._REFUSE_CONNECTION:
                    logging.warning(f'Client {addr} connection was refused')
                    self.send(conn, consts._MSG_CONNECTION_REFUSED)
                    conn.close()
                    return
                
        except ConnectionResetError:
            logging.warning(f'Client {addr} disconnected')
            return
        
        except Exception as e:
            logging.warning(f'Client {addr} not from GUI: {e}')
            conn.close()
            return
    
    def _handle_message(self, conn: socket.socket, addr, message:str, in_server=False):
        logging.info(f'Checking message {(message,)}: {conn.getpeername()} {conn.fileno()}')
        if message is None:
            return consts._REFUSE_CONNECTION, None
        split_message = message.split(consts._DIVIDER)

        # Client Awaiting Server connection
        if not in_server and len(split_message) == 3:
            is_host, hostname, password = tuple(message.split('~'))
            is_host = True if is_host=='True' else False
            
            if not is_host and hostname not in self.servers:
                logging.info(f'Client {addr} tried to join nonexistant {hostname}...')
                self.send(conn, consts._MSG_HOSTNAME_NOT_EXISTS_ERROR)
                return consts._IGNORE_MESSAGE, None
            
            elif not is_host and password == self.servers[hostname].password:
                return consts._ACCEPT_CONNECTION, (is_host, hostname, password)

            elif not is_host and password != self.servers[hostname].password:
                logging.info(f'Client {addr} entered wrong password for {hostname}...')
                self.send(conn, consts._MSG_INCORRECT_PASSWORD)
                return consts._IGNORE_MESSAGE, None
            
            elif is_host and hostname in self.servers:
                logging.info(f'Client {addr} tried to create duplicate server of {hostname}...')
                self.send(conn, conn, consts._MSG_HOSTNAME_EXISTS_ERROR)
                return consts._IGNORE_MESSAGE, None
            
            elif is_host and hostname not in self.servers:
                return consts._ACCEPT_CONNECTION, (is_host, hostname, password)
            
            logging.info(f'Client {addr} created {hostname}...')

        if message == consts._PING:
            self.send(conn, consts._PING)
            return consts._IGNORE_MESSAGE, None

        return consts._IGNORE_MESSAGE, None

    @property
    def server_list(self):
        return list(self.servers.keys())
    
    def send_servers(self, conn: socket.socket, addr):
        serverlist = consts._DIVIDER.join(self.server_list)
        logging.debug(f'sending: {serverlist}')
        serverlist = consts._MSG_NO_ACTIVE_SERVERS if not serverlist else serverlist
        self.send(conn, serverlist)

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
                data = self.listen(conn)
                # Forward to all other clients
                for (c, addr) in server.clients:
                    if c != conn:
                        self.send(c, data)
            except:
                break
        try:
            conn.close()
        except:
            pass
        logging.critical(f'Server {server.name} Host Disconnected')
        self._server_closed(server)
            
    def handle_client(self, server:Server, conn: socket.socket, addr):
        logging.info(f"Handeling: {conn}\n{addr}\n\n")
        try:
            while server.host is not None:
                data = self.listen(conn)
                # Forward to all other clients
                for (c, addr) in server.clients:
                    if c != conn:
                        try:
                            self.send(c, data)
                        except:
                            pass
        except Exception as e:
            logging.warning(e)
            pass
        logging.critical(f"Disconnected: {conn}\n{addr}")
        server.clients.remove((conn, addr))
        conn.close()
            
    def _server_closed(self, server:Server):
        logging.critical(f'Server {server.name} Closing')
        try:
            for (c, addr) in server.clients:
                try:
                    self.send(c, f'Host {addr} has disconnected!')
                    c.close()
                except:
                    pass
        finally:
            server.host = None
            del self.servers[server.name]
            
relay_server = Host()
#relay_server.setup()
#while True:
#    pass
threading.Thread(target=relay_server.setup).start()
