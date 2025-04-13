import socket
import threading
import json
import time
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('WarOfCellsServer')

def xor_encrypt_decrypt(message, key='X'):
    return ''.join(chr(ord(c) ^ ord(key)) for c in message)

# Include GameServer class here

class GameServer:
    def __init__(self, host='localhost', port=5555):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = {}  # addr -> {"socket": socket, "role": "PLAYER"|"ENEMY"}
        self.player_addr = None
        self.enemy_addr = None

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(2)  # Only need 2 clients - player and enemy
            
            self.running = True
            logger.info(f"Game server started on {self.host}:{self.port}")
            
            # Start acceptor thread
            threading.Thread(target=self.accept_clients, daemon=True).start()
            
            # Start command thread
            threading.Thread(target=self.command_loop, daemon=True).start()
            
            return True
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False

    def accept_clients(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                
                # Create client handler thread
                threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, addr), 
                    daemon=True
                ).start()
                
                logger.info(f"Client connected from {addr}")
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting client: {e}")
                    time.sleep(1)

    def handle_client(self, client_socket, addr):
        self.clients[addr] = {"socket": client_socket, "role": None}
        
        while self.running:
            try:
                encrypted_message = client_socket.recv(4096).decode('utf-8')
                if not encrypted_message:
                    break
                
                message = xor_encrypt_decrypt(encrypted_message)
                
                try:
                    event = json.loads(message)
                    self.process_client_event(addr, event)
                except json.JSONDecodeError:
                    logger.error(f"Received invalid JSON from {addr}: {message}")
            except Exception as e:
                logger.error(f"Error handling client {addr}: {e}")
                break
                
        # Client disconnected
        self.handle_client_disconnect(addr)
        
    def process_client_event(self, addr, event):
        if event.get("type") == "GAME_EVENT":
            event_type = event.get("event_type")
            data = event.get("data", {})
            
            if event_type == "CONNECT":
                role = data.get("role")
                if role in ["PLAYER", "ENEMY"]:
                    assigned_role = self.assign_role(addr, role)
                    
                    # Send acknowledgment
                    self.send_to_client(addr, {
                        "type": "CONNECT_ACK",
                        "data": {"control_enemy": assigned_role == "ENEMY"}
                    })
                    
                    logger.info(f"Client {addr} assigned role: {assigned_role}")
            else:
                # Forward game events to other client
                self.broadcast_event(event, sender_addr=addr)
        
    def assign_role(self, addr, requested_role):
        # If roles are available, assign the requested role
        if requested_role == "PLAYER" and not self.player_addr:
            self.player_addr = addr
            self.clients[addr]["role"] = "PLAYER"
            return "PLAYER"
        
        if requested_role == "ENEMY" and not self.enemy_addr:
            self.enemy_addr = addr
            self.clients[addr]["role"] = "ENEMY"
            return "ENEMY"
        
        # If requested role unavailable, assign any available role
        if not self.player_addr:
            self.player_addr = addr
            self.clients[addr]["role"] = "PLAYER"
            return "PLAYER"
        
        if not self.enemy_addr:
            self.enemy_addr = addr
            self.clients[addr]["role"] = "ENEMY"
            return "ENEMY"
        
        # If all roles taken, assign observer (no actions)
        self.clients[addr]["role"] = "OBSERVER"
        return "OBSERVER"
        
    def handle_client_disconnect(self, addr):
        if addr in self.clients:
            role = self.clients[addr].get("role")
            
            if role == "PLAYER":
                self.player_addr = None
            elif role == "ENEMY":
                self.enemy_addr = None
                
            del self.clients[addr]
            logger.info(f"Client {addr} ({role}) disconnected")
    
    def broadcast_event(self, event, sender_addr=None):
        for addr, client in self.clients.items():
            if addr != sender_addr:
                self.send_to_client(addr, event)
    
    def send_to_client(self, addr, data):
        if addr in self.clients:
            try:
                json_data = json.dumps(data)
                encrypted_data = xor_encrypt_decrypt(json_data)
                self.clients[addr]["socket"].send(encrypted_data.encode('utf-8'))
            except Exception as e:
                logger.error(f"Error sending to client {addr}: {e}")
                self.handle_client_disconnect(addr)
    
    def command_loop(self):
        print("Server commands: 'quit', 'clients', 'kick <addr>'")
        while self.running:
            try:
                cmd = input("> ")
                if cmd.lower() == "quit":
                    self.stop()
                    break
                elif cmd.lower() == "clients":
                    self.print_clients()
                elif cmd.lower().startswith("kick"):
                    parts = cmd.split(None, 1)
                    if len(parts) > 1:
                        self.kick_client(parts[1])
            except Exception as e:
                logger.error(f"Error in command loop: {e}")
    
    def print_clients(self):
        print(f"Connected clients: {len(self.clients)}")
        for addr, client in self.clients.items():
            print(f"  {addr}: {client['role']}")
    
    def kick_client(self, addr_str):
        try:
            # Parse addr from string like '127.0.0.1:12345'
            host, port = addr_str.split(':')
            addr = (host, int(port))
            
            if addr in self.clients:
                self.handle_client_disconnect(addr)
                print(f"Kicked client {addr}")
            else:
                print(f"Client {addr} not found")
        except Exception as e:
            print(f"Invalid address format: {e}")
    
    def stop(self):
        self.running = False
        
        # Close all client connections
        for addr, client in list(self.clients.items()):
            try:
                client["socket"].close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        logger.info("Game server stopped")

if __name__ == "__main__":
    host = 'localhost'
    port = 5555
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
        
    server = GameServer(host, port)
    if server.start():
        print(f"Game server running on {host}:{port}")
        print("Press Ctrl+C to stop")
        try:
            # Keep main thread running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping server...")
        finally:
            server.stop()
    else:
        print("Failed to start server")