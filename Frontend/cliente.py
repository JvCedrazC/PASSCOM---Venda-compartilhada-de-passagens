import networkx as nx


# Função para ler o arquivo e criar o grafo
def criar_grafo(arquivo):
    grafo = nx.Graph()
    with open(arquivo, 'r') as f:
        for linha in f:
            cidade1, cidade2 = linha.strip().split()
            grafo.add_edge(cidade1, cidade2)
    return grafo


# Função para encontrar todos os caminhos entre duas cidades
def encontrar_caminhos(grafo, origem, destino):
    return list(nx.all_simple_paths(grafo, source=origem, target=destino))

def descobrir_cidade(cidade):
    match cidade:
        case 1:
            return "A"
        case 2:
            return "B"
        case 3:
            return "C"
        case 4:
            return "D"
        case 5:
            return "E"
        case 6:
            return "F"
        case 7:
            return "G"
        case 8:
            return "H"
        case 9:
            return "I"
        case 10:
            return "J"
                

def main():
    sair = 0

    while sair == 0:
        print("-------- Bem vindo a foda-se --------")
        print("\n")
        
        print("Escolha o número que represente o seu local de origem (local de onde você quer viajar)\n 1 = A\n 2 = B\n 3 = C \n 4 = D\n 5 = E\n 6 = F\n 7 = G\n 8 = H\n 9 = I\n 10 = J\n 11 = Para sair")
        origem = int(input("Origem: "))
        
        #Tratamento de erro / Desistência do usuario
        if origem == 11:
            break

        #Deixa o usuario preso em um while caso escolha um valor invalido
        while origem < 1 or origem > 11:
            print("Escolha um número válido")
            origem = int(input("Origem: "))

        
        print("\n")
        print(100*"=")
        print("\nAgora escolha o número que represente o seu local de destino (local para onde você quer viajar):\n 1 = A\n 2 = B\n 3 = C \n 4 = D\n 5 = E\n 6 = F\n 7 = G\n 8 = H\n 9 = I\n 10 = J\n 11 = Para sair ")
        destino = int(input("Destino: "))

        #Tratamento de erro / Desistência do usuario
        if destino == 11:
            break
        elif destino == origem:
            print("Escolha um número válido")
            origem = int(input("Origem: "))
            print("\n")
            print("O seu destino não pode ser igual a sua origem")


        #Deixa o usuario preso em um while caso escolha um valor invalido
        while destino < 1 or destino > 11:
            print("Escolha um número válido")
            origem = int(input("Origem: "))
            print("\n")
        

        #Descobre quais são as cidades equivalentes aos números escolhidos
        origem = descobrir_cidade(origem)
        destino = descobrir_cidade(destino)
        
        
        #Cria o grafo, encontra as rotas e retorna para o usuario
        grafo = criar_grafo('Cidades.txt')
        caminhos = encontrar_caminhos(grafo, origem, destino)
        
        print(100*("="))
        print("Rotas disponíveis: ")
        for caminho in caminhos:
            print(" -> ".join(caminho))
        print(100*("="))







main()






















'''# Echo client program
import socket
HOST = 'localhost' 
PORT = 50007 
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'Hello, world')
    data = s.recv(1024)
print('Received', repr(data))'''

