document.addEventListener('DOMContentLoaded', function() {
    var origem;
    var destino;
    var rotasDisponiveis = [];  // Guardar rotas e passagens disponíveis
    var ws;

    console.log("Carregou o DOM!");

    // Função para receber a origem da rota
    window.receberOrigem = function(CidadeO) {
        origem = CidadeO.innerText;
        console.log("Origem escolhida: " + origem);
        document.querySelector('.opcoes-origem').style.display = 'none';
        document.querySelector('.opcoes-destino').style.display = 'flex';
        document.querySelector('.button-voltar').style.display = "block";
        document.querySelector('.nomeUser').classList.add('input-hidden');
        var paragrafo = document.getElementById("paragrafo-origem-destino");
        paragrafo.innerText = "Escolha seu local de destino";
    };

    // Função para receber o destino da rota
    window.receberDestino = function(CidadeD) {
        destino = CidadeD.innerText;
        console.log("Destino escolhido: " + destino);
        document.querySelector('.descobrir-rotas').style.display = 'block';
    };

    // Função para enviar os dados da rota e receber as rotas calculadas
    window.enviarRota = function() {
        document.querySelector('.opcoes-destino').style.display = 'none';
        document.querySelector('.descobrir-rotas').style.display = 'none';

        console.log("Enviando rota...");
        const data = { origem, destino };
        console.log("Dados da rota: ", data);
        fetch('http://localhost:777/api/rota', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            console.log("Resposta da API: ", data);
            rotasDisponiveis = data.rotas;
            mostrarRotas(data.rotas);
        })
        .catch(error => {
            console.error('Erro:', error);
        });
    };

    // Função para mostrar as rotas calculadas
    function mostrarRotas(rotas) {
        var resultadoDiv = document.querySelector('.resultado');
        resultadoDiv.style.display = 'flex';  // Mostrar a div resultados
        var botoes = ['rota1', 'rota2', 'rota3'];
        var passagens = ['passagem-rota1', 'passagem-rota2', 'passagem-rota3'];
        for (var i = 0; i < botoes.length; i++) {
            var botao = document.getElementById(botoes[i]);
            var passagem = document.getElementsByClassName(passagens[i])[0];
            if (rotas[i]) {
                botao.innerText = rotas[i].rota;
                passagem.innerText = "Passagens disponíveis: " + rotas[i].passagens;
                botao.setAttribute("data-rota", rotas[i].rota);  // Adicionar atributo data-rota
            } else {
                botao.innerText = 'Rota ' + (i + 1) + ' indisponível';
                passagem.innerText = "Passagens disponíveis: 0";
                botao.removeAttribute("data-rota");  // Remover atributo data-rota
            }
        }
    }

    // Função para comprar passagem
    window.comprarPassagem = function(botao) {
        var rotaEscolhida = botao.getAttribute("data-rota");  // Obter a rota do atributo data-rota
        console.log("Rota escolhida: " + rotaEscolhida);
        if (rotaEscolhida) {
            var rota = rotasDisponiveis.find(r => r.rota === rotaEscolhida);
            if (rota && rota.passagens > 0) {
                rota.passagens--;
                console.log("Passagem comprada. Passagens restantes:", rota.passagens);
                // Atualizar UI
                mostrarRotas(rotasDisponiveis);
                // Propagar para outros usuários
                if (ws) {
                    ws.send(JSON.stringify({ rota: rotaEscolhida, passagens: rota.passagens }));
                }
            } else {
                console.log("Passagens esgotadas para esta rota.");
                alert("Passagens esgotadas para esta rota.");
            }
        }
    }

    // Função para inicializar WebSocket
    function iniciarWebSocket() {
        ws = new WebSocket("ws://localhost:6789/");
        ws.onmessage = function(event) {
            var data = JSON.parse(event.data);
            console.log("Atualização recebida via WebSocket:", data);
            var rotaAtualizada = rotasDisponiveis.find(r => r.rota === data.rota);
            if (rotaAtualizada) {
                rotaAtualizada.passagens = data.passagens;
                mostrarRotas(rotasDisponiveis);
            }
        };
        ws.onclose = function() {
            console.log("WebSocket desconectado. Tentando reconectar...");
            setTimeout(iniciarWebSocket, 1000);
        };
    }

    // Iniciar WebSocket
    iniciarWebSocket();

    window.voltar = function() {
        console.log("Voltando para seleção de origem");
        document.querySelector('.opcoes-destino').style.display = 'none';
        document.querySelector('.opcoes-origem').style.display = 'flex';
        document.querySelector('.button-voltar').style.display = 'none';
        document.querySelector('.descobrir-rotas').style.display = 'none';
        document.querySelector('.resultado').style.display = 'none';
        document.querySelector('.nomeUser').classList.remove('input-hidden');
        var paragrafo = document.getElementById("paragrafo-origem-destino");
        paragrafo.innerText = "Escolha seu local de origem";
    };
});
