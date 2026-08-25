import threading
import socket
import time
import logging
import sys

try:
    from . import consts
except:
    import consts


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)   # Log to the terminal
    ]
)


class Communicator:
    def __init__(self, retry_on_dc=True):
        self.socket   = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.current_hostname = None
        self._connect_to_relay()

        if retry_on_dc:
            threading.Thread(target=self._reconnect_on_dc, daemon=True).start()
            
    @property
    def ping(self):
        start_time = time.time()
        self.send(consts._PING)
        rec = None
        while (time.time()-start_time)*1000 < consts._MAX_PING_MS:
            rec = self.listen()
            if rec == consts._PING:
                return int((time.time()-start_time)*1000)
        logging.warning(f'Relay Server is taking too long to respond...')
        return consts._MAX_PING_MS
    
    @property
    def relay_ip(self):
        return socket.gethostbyname(consts._DDNS_SITE)
    
    @property
    def is_connected(self):
        self.send(consts._PING)
        return True if self.listen() is None else False


    def _reconnect_on_dc(self, delay_time=10):
        self._connect_to_relay()
        while True:
            if not self.is_connected:
                self._connect_to_relay()
            time.sleep(delay_time)

    def _connect_to_relay(self):
        try:
            self.socket.connect((self.relay_ip, consts._PORT))
            self.send(consts._PASSKEY)
            logging.info(self.listen())
            return True if self.listen() == consts._MSG_PASSKEY_ACCEPTED else False
        except Exception as e:
            self.socket.connect((consts._LOCAL_RELAY_IP, consts._PORT))
            self.send(consts._PASSKEY)
            logging.info(self.listen())
            return True
        except Exception as e:
            logging.critical(f'here {e}')
            return False      

    def send(self, message):
        message = str(message)+consts._DELIMITER
        try:
            return self.socket.sendall(message.encode(encoding=consts._ENCODING))
        except Exception as e:
            raise e
    
    def listen(self, bufsize=1024, decode=True, delimiter=consts._DELIMITER):
        try:    
            data = bytearray()
            while True:
                packet = self.socket.recv(bufsize)
                if not packet:
                    break
                data.extend(packet)
                if bytes(delimiter, encoding=consts._ENCODING) in packet:
                    break
            return data.decode(encoding=consts._ENCODING).replace(delimiter, '') if decode else data[:-len(bytes(delimiter))]
        except Exception as e:
            logging.critical(e)
            return None

    def _get_server_list(self) -> list[str]:
        join_code = consts._DIVIDER.join([consts._PASSKEY, consts._GET_SERVER])

        ierr = self.send(join_code)
        if ierr is not None:
            self.current_hostname = None
            raise ierr
        
        server_list = self.listen()

        if server_list == consts._MSG_NO_ACTIVE_SERVERS:
            return []
        
        elif server_list is None:
            self.current_hostname = None
            raise consts.ERROR[consts._MSG_LOST_CONNECTION]()
        
        return server_list.split(consts._DIVIDER)
    
    def _server_connect(self, hostname: str, password: str, is_host: bool):
        if self.current_hostname is not None:
            raise consts.ERROR[consts._MSG_ALREADY_JOINED_ERROR](self.current_hostname) 
        
        # Ensure password is allowed
        if not consts._password_is_allowed(password):
            raise consts.ERROR[consts._MSG_ILLEGAL_PASSWORD]()
        
        # Create formatted request and send
        join_code = consts._DIVIDER.join([str(is_host), str(hostname), str(password)])
        ierr = self.send(join_code)

        # Failed to send 
        if ierr is not None:
            self.current_hostname = None
            raise consts.ERROR[consts._MSG_CONNECTION_ERROR](self.current_hostname) 
        
        return_message = self.listen()

        # Failed to recieve message
        if return_message is None:
            self.current_hostname = None
            raise consts.ERROR[consts._MSG_LOST_CONNECTION](self.current_hostname) 
        
        logging.critical(return_message)
        # Save current hostname if connection is established
        if return_message not in (consts._MSG_JOIN_SUCCESS, consts._MSG_CREATE_SUCCESS,):
            raise consts.ERROR[consts._MSG_LOST_CONNECTION](self.current_hostname) 
        
        self.current_hostname = hostname
        return True
    
    def start_server(self, hostname: str, password: str):
        return self._server_connect(hostname, password, True) 
    
    def join_server(self, hostname: str, password: str):
        return self._server_connect(hostname, password, False)
    
    def disconnect(self):
        self.current_hostname = None
        self.socket.close()

if __name__ == '__main__':
    com = Communicator()
    com.start_server('First Test', 'Bazinga')
    time.sleep(20)
    pass        