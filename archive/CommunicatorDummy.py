import socket
import requests

def listen(self, clientsocket):
    while True:
        message = clientsocket.recv(1024).decode()
        print(message)
    
    listen_process = threading.Thread(target=self.pair_device, daemon=True)
    listen_process.start()

if __name__ == '__main__':
    print(requests.get('https://api.ipify.org').text)
    
    s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    hostname = 'Swifty'
    host =  '76.181.183.164'
    port = 8000
    try:
        s.connect((host, port))

    except Exception as e:
        print(type(e), e)
        input('Enter to end...')
        raise e
        
    while True:
        x = input('Enter Message: ')
        s.sendall(x.encode())
        if x == 'end':
            break
