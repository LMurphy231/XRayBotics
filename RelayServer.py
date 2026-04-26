import socket
import threading
import requests

clients = []

def handle_client(conn, addr):
    print(f"Connected: {addr}")
    clients.append(conn)

    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break

            # Forward to all other clients
            for c in clients:
                if c != conn:
                    c.sendall(data)

    except:
        pass

    print(f"Disconnected: {addr}")
    clients.remove(conn)
    conn.close()
    

def server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9000))
    server.listen()

    print("Relay server running on port 8000...")
    print(f"Public: {requests.get('https://api.ipify.org').text} Local: {socket.gethostbyname(socket.gethostname())}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    
threading.Thread(target=server).start()