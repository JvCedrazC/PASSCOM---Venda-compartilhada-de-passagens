import threading
import socket

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("172.16.103.221", 777))
    except:
        return print("\n Não foi possível conectar ao servidor")
    username = input("Usuário>")
    print("Conectado!")

    thread1 = threading.Thread(target=receive_Messages, args=[client])
    thread2 = threading.Thread(target=sendMessages, args=[client, username])

    thread1.start()
    thread2.start()

def receive_Messages(client):
    while True:
        try:
            msg = client.recv(2048).decode('utf-8')
            print(msg + '\n')
        except:
            print('\nNão foi possível permancer conectado ao servidor!')
            print('\nPressione <enter> para continuar')
            client.close()
            break

def sendMessages(client, username):
    while True:
        try:
            msg = input('\n')
            client.send(f'<{username}>  {msg}'.encode('utf-8'))
        except:
            return

main()