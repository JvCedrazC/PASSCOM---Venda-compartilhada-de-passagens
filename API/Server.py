import os
import time
import tempfile
import json
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
import websockets

# Identificadores dos servidores
server_id = 1  # Altere para o ID deste servidor (1, 2 ou 3 conforme necessário)
next_server = 2  # ID do próximo servidor no anel

# Funções para carregamento das rotas e passagens do arquivo
def load_routes(file):
    routes = {}
    with open(file, 'r') as f:
        for linha in f:
            if linha.strip():
                rota, passagens = linha.strip().split(": ")
                routes[rota] = int(passagens)
    return routes

routes = load_routes('cidades.txt')

# Funções de locking baseadas em arquivos
def acquire_lock_with_timeout(lock_name, acquire_timeout=10, lock_timeout=10):
    lockfile = os.path.join(tempfile.gettempdir(), lock_name)
    start_time = time.time()
    while time.time() - start_time < acquire_timeout:
        try:
            fd = os.open(lockfile, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            with os.fdopen(fd, 'w') as lockfile_fd:
                lockfile_fd.write(str(os.getpid()))
            return lockfile
        except FileExistsError:
            time.sleep(0.01)
    raise TimeoutError("Could not acquire lock within the specified timeout")

def release_lock(lock_name):
    lockfile = os.path.join(tempfile.gettempdir(), lock_name)
    try:
        os.remove(lockfile)
    except FileNotFoundError:
        pass

# Lista para armazenar os WebSocket connections
connected_clients = []

# Lista para armazenar as solicitações em espera
pending_requests = []

# Função para propagar atualizações via WebSockets
async def propagate_update(data):
    if connected_clients:
        await asyncio.gather(*(client.send(json.dumps(data)) for client in connected_clients))
        # Atualiza o arquivo local
        with open('cidades.txt', 'w') as f:
            for rota, passagens in routes.items():
                f.write(f"{rota}: {passagens}\n")

# Função para comprar passagem
def comprar_passagem(rota):
    global routes
    if routes[rota] > 0:
        routes[rota] -= 1
        return {"rota": rota, "passagens": routes[rota]}
    else:
        return {"rota": rota, "passagens": 0}

# Funções relacionadas ao Token Ring
current_token_holder = 1  # ID do servidor atual com o token

async def pass_token():
    global current_token_holder
    while True:
        await asyncio.sleep(5)  # Tempo para manter o token
        if current_token_holder == server_id:
            current_token_holder = next_server  # Passa o token para o próximo servidor
            await propagate_update({"token": current_token_holder})
            await process_pending_requests()  # Processa as solicitações em espera

# Processa as solicitações em espera quando o token é recebido
async def process_pending_requests():
    global pending_requests
    while pending_requests:
        request = pending_requests.pop(0)
        result = comprar_passagem(request["rota"])
        resposta = {"rota": result["rota"], "passagens": result["passagens"]}
        await propagate_update(resposta)
        # Envia a resposta para o cliente que fez a solicitação
        for client in connected_clients:
            await client.send(json.dumps(resposta))

# Classe para tratar requisições HTTP
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        global current_token_holder
        if self.path == "/api/rota":
            print("Recebendo solicitação de rota...")
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            print("Dados recebidos:", data)
            origem = data.get("origem")
            destino = data.get("destino")
            # Processamento das rotas e passagens
            relevant_routes = {k: v for k, v in routes.items() if origem in k and destino in k}
            resposta = {"rotas": [{"rota": rota, "passagens": passagens} for rota, passagens in relevant_routes.items()]}
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(resposta).encode())
        elif self.path == "/api/comprar":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            rota = data.get("rota")
            if rota in routes:
                if current_token_holder == server_id:  # Verifica se este servidor tem o token
                    lock_id = acquire_lock_with_timeout("rota_lock")
                    if lock_id:
                        try:
                            result = comprar_passagem(rota)
                            resposta = {"rota": result["rota"], "passagens": result["passagens"]}
                            self.send_response(200)
                            self.send_header("Content-type", "application/json")
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            self.wfile.write(json.dumps(resposta).encode())
                            asyncio.create_task(propagate_update(resposta))  # Certifica que a task é criada corretamente
                        finally:
                            release_lock("rota_lock")
                    else:
                        self.send_response(503)
                        self.send_header("Content-type", "application/json")
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({"erro": "Não foi possível adquirir o lock"}).encode())
                else:
                    pending_requests.append({"rota": rota})
                    self.send_response(202)  # Accepted
                    self.send_header("Content-type", "application/json")
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"mensagem": "A compra está em espera até que o servidor receba o token."}).encode())

# Função para rodar o servidor HTTP
def run_http_server():
    server_address = ("", 777)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"Servidor rodando na porta 777")
    httpd.serve_forever()

# Função para rodar o servidor WebSocket
async def run_ws_server():
    async def handler(websocket, path):
        connected_clients.append(websocket)
        print(f"Cliente conectado: {websocket.remote_address}")
        try:
            async for message in websocket:
                print(f"Recebido: {message}")
        finally:
            print(f"Cliente desconectado: {websocket.remote_address}")
            connected_clients.remove(websocket)
    server = await websockets.serve(handler, "localhost", 6789)
    print("WebSocket server started at ws://localhost:6789")
    await server.wait_closed()

# Função principal para rodar ambos os servidores
async def main():
    asyncio.create_task(run_ws_server())
    run_http_server()  # HTTP Server bloqueante, portanto precisa ser executado assim

if __name__ == "__main__":
    asyncio.run(main())
