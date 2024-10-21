import os
import time
import tempfile
import random
import networkx as nx
import json
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
import websockets

# Funções para criação de grafo e cálculo de rotas
file = 'cidades.txt'

def create_graph(file):
    graph = nx.Graph()
    with open(file, 'r') as f:
        for linha in f:
            cidade1, cidade2 = linha.strip().split()
            graph.add_edge(cidade1, cidade2)
    return graph

def find_path(graph, source, target):
    return list(nx.all_simple_paths(graph, source=source, target=target))

graph = create_graph(file)

def generate_tickets(all_paths):
    rotes_tickets = {}
    for path in all_paths:
        tickets = random.randint(0, 6)
        place = ' -> '.join(path)
        rotes_tickets[place] = tickets
    return rotes_tickets

def print_rotas(rotas, mensagem):
    print(mensagem)
    for rota, passagens in rotas.items():
        print(f"Rota: {rota}, Passagens disponíveis: {passagens}")
    print("\n")

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

# Função para propagar atualizações via WebSockets
async def propagate_update(data):
    if connected_clients:
        await asyncio.gather(*(client.send(json.dumps(data)) for client in connected_clients))

# Classe para tratar requisições HTTP
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/rota":
            print("Recebendo solicitação de rota...")
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            print("Dados recebidos:", data)

            origem = data.get("origem")
            destino = data.get("destino")

            # Adquirir lock antes de processar a rota
            lock_id = acquire_lock_with_timeout("rota_lock")
            if lock_id:
                try:
                    # Processamento da rota
                    all_paths = find_path(graph, origem, destino)
                    all_paths = [path for path in all_paths if len(path) <= 4]  # Filtra rotas com mais de 4 cidades
                    print('Rotas calculadas:', all_paths)

                    # Limita as rotas a no máximo 3 antes de gerar os tickets
                    all_paths = all_paths[:3]
                    rotes_tickets = generate_tickets(all_paths)

                    # Print rotas antes de enviar ao cliente
                    print_rotas(rotes_tickets, "Rotas e vagas antes de enviar para o cliente:")

                    resposta = {"rotas": [{"rota": rota, "passagens": rotes_tickets[rota]} for rota in rotes_tickets]}

                    # Enviar resposta
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(resposta).encode())

                    # Print para indicar conexão de cliente e processamento
                    print(f"Cliente conectado e processando rota de {origem} para {destino}")

                    # Propagar a transação para outros nós (WebSocket)
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(propagate_update(resposta))
                finally:
                    release_lock("rota_lock")
            else:
                self.send_response(503)
                self.send_header("Content-type", "application/json")
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"erro": "Não foi possível adquirir o lock"}).encode())
                print("Não foi possível adquirir o lock")

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
        try:
            async for message in websocket:
                print(f"Recebido: {message}")
        finally:
            connected_clients.remove(websocket)

    server = await websockets.serve(handler, "localhost", 6789)
    print("WebSocket server started at ws://localhost:6789")
    await server.wait_closed()

# Função principal para rodar ambos os servidores
def main():
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_http_server)
    loop.run_until_complete(run_ws_server())

if __name__ == "__main__":
    main()
