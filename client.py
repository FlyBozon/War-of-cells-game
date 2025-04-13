import socket
import threading
import time

show_encrypted = False

def xor_encrypt_decrypt(message, key='X'):
    return ''.join(chr(ord(c) ^ ord(key)) for c in message)

def receive_messages(client_socket):
    global show_encrypted
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            decrypted_message = xor_encrypt_decrypt(message)
            if show_encrypted:
                print(f"[Serwer] Encrypted: {message} | Decrypted: {decrypted_message}")
            else:
                print(f"[Serwer]: {decrypted_message}")
        except:
            print("[INFO] Połączenie z serwerem utracone. Próba ponownego połączenia...")
            reconnect()
            break

def reconnect():
    time.sleep(5)
    start_client()

def start_client():
    global show_encrypted
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(('localhost', 5555))
        print("[INFO] Połączono z serwerem.")
    except:
        print("[ERROR] Nie można połączyć się z serwerem. Próba ponownego połączenia...")
        reconnect()
        return

    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.start()

    while True:
        message = input("")
        if message.lower() == "exit":
            break
        if message.lower() == "szyfr":
            show_encrypted = not show_encrypted
            print(f"[INFO] Tryb szyfrowania: {'Włączony' if show_encrypted else 'Wyłączony'}")
            continue
        encrypted_message = xor_encrypt_decrypt(message)
        client.send(encrypted_message.encode('utf-8'))

    client.close()

if __name__ == "__main__":
    start_client()
