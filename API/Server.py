import time
from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import socket
import json
from collections import deque

app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Rotas sob a responsabilidade do servidor 1
routes_server1 = {
    'Recife->Fortaleza->Salvador->Brasilia': 5,
    'Recife->Brasilia->Fortaleza->Manaus': 3,
    'Recife->Salvador->Brasilia->Uberlandia': 4,
}

# Lista de servidores (endereços IP e portas)
servers = [
    ('localhost', 8082),  # Adicione o segundo servidor aqui
]

# Token inicial
token = {
    "current_holder": 1,
    "last_updated": time.time()
}

# Fila de solicitações pendentes
pending_requests = deque()

# Timeout e número de tentativas ao reencaminhar token
TOKEN_TIMEOUT = 10  # segundos
RETRY_ATTEMPTS = 3


def process_purchase(route):
    if route in routes_server1 and routes_server1[route] > 0:
        routes_server1[route] -= 1
        return {"success": True, "remaining": routes_server1[route]}  # Retorna as passagens restantes
    else:
        return {"success": False, "message": "Passagem indisponível ou rota inválida."}


@app.route('/api/rota', methods=['POST'])
def descobrir_rotas():
    data = request.json
    origem = data.get('origem')
    destino = data.get('destino')

    rotas_disponiveis = {}

    for rota, passagens in routes_server1.items():
        if rota.startswith(origem) and rota.endswith(destino):
            rotas_disponiveis[rota] = {"passagens": passagens}

    return jsonify({"rotas": rotas_disponiveis})


@app.route('/api/comprar', methods=['POST', 'OPTIONS'])
def comprar_passagem():
    if request.method == 'OPTIONS':
        return jsonify({}), 200  # Responde às preflight requests com 200
    data = request.json
    rota = data.get('rota')

    if rota:
        if token['current_holder'] == 1:  # Verifica se o servidor possui o token
            print(f"Servidor 1: Processando compra para a rota: {rota}")
            resultado = process_purchase(rota)
            if resultado['success']:
                print(f"Compra realizada para a rota: {rota}")
                return jsonify({"success": True, "remaining": resultado['remaining']})
            else:
                print(f"Falha na compra: {resultado['message']}")
                return jsonify({"success": False, "message": resultado['message']})
        else:
            # Adiciona a solicitação à fila de pendências
            pending_requests.append(rota)
            print(f"Servidor 1: Solicitação para a rota {rota} adicionada à fila.")
            return jsonify({"success": False, "message": "Solicitação adicionada à fila."})
    else:
        return jsonify({"error": "Rota não especificada"}), 400


@app.route('/api/verificar_token', methods=['GET'])
def verificar_token():
    return jsonify({"has_token": token['current_holder'] == 1})  # Verifica se o servidor atual tem o token


def process_pending_requests():
    while True:
        if pending_requests:
            rota = pending_requests.popleft()  # Processa a próxima solicitação pendente
            print(f"Servidor 1: Processando solicitação pendente para a rota: {rota}")
            resultado = process_purchase(rota)
            if resultado['success']:
                print(f"Compra processada para a rota pendente: {rota}")
            else:
                print(f"Falha na compra da rota pendente: {rota}")


def start_token_server():
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('localhost', 8084))
                s.listen()
                print("Servidor de tokens está ouvindo...")
                while True:
                    conn, addr = s.accept()
                    print(f"Servidor 1: Conexão recebida de {addr}")
                    with conn:
                        token_data = json.loads(conn.recv(1024).decode('utf-8'))
                        print(f"Servidor 1: Token recebido: {token_data}")
                        token['last_updated'] = time.time()  # Atualiza o timestamp do token
                        print("Servidor 1: Processando token...")

                        # Verifica se há mais servidores
                        if len(servers) > 0:
                            token['current_holder'] = (token['current_holder'] % (
                                        len(servers) + 1)) + 1  # Passa para o próximo servidor
                            print(f"Servidor 1: Token passado para o Servidor {token['current_holder']}.")
                        else:
                            print("Servidor 1: Não há outros servidores. Mantendo o token.")

                        send_token(token_data)
                        process_pending_requests()  # Processa as solicitações pendentes
        except Exception as e:
            print(f"Ocorreu um erro no servidor de tokens: {e}")
            time.sleep(1)


def send_token(token_data):
    try:
        attempts = 0
        while attempts < RETRY_ATTEMPTS:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    if len(servers) > 0:
                        next_server = servers[(token['current_holder'] - 1) % len(servers)]
                        s.connect(next_server)
                        s.sendall(json.dumps(token_data).encode('utf-8'))
                        print(f"Servidor 1: Token enviado para {next_server}.")
                        return
                    else:
                        print("Servidor 1: Não há servidores para enviar o token.")
                        break
            except Exception as e:
                attempts += 1
                print(f"Falha ao enviar o token, tentativa {attempts}/{RETRY_ATTEMPTS}. Erro: {e}")
                time.sleep(1)
    except Exception as e:
        print(f"Ocorreu um erro ao enviar o token: {e}")


def check_token_timeout():
    while True:
        if time.time() - token['last_updated'] > TOKEN_TIMEOUT:
            print("Token expirado. Revertendo controle para o servidor inicial.")
            token['current_holder'] = 1  # Reverte o token para o servidor inicial
        time.sleep(5)


def iniciar_token_thread():
    token_thread = threading.Thread(target=start_token_server)
    timeout_thread = threading.Thread(target=check_token_timeout)
    token_thread.start()
    timeout_thread.start()


if __name__ == '__main__':
    iniciar_token_thread()
    app.run(port=8081, debug=True)  # Servidor escutando na porta 8081
