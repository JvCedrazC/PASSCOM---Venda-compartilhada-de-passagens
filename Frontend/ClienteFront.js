document.addEventListener('DOMContentLoaded', function() {
    var origem;
    var destino;
    var rotasDisponiveis = {};
    var servidor = 'http://localhost:8081'; // Servidor Flask
    var hasToken = false;  // Variável para controlar a posse do token

    console.log("Carregou o DOM!");

    window.receberOrigem = function(CidadeO) {
        origem = CidadeO.innerText;
        console.log("Origem escolhida: " + origem);
        document.querySelector('.opcoes-origem').style.display = 'none';
        document.querySelector('.opcoes-destino').style.display = 'flex';
        document.querySelector('.button-voltar').style.display = "block";
        document.querySelector('.nomeUser').classList.add('input-hidden');
        document.getElementById("paragrafo-origem-destino").innerText = "Escolha seu local de destino";
    };

    window.receberDestino = function(CidadeD) {
        destino = CidadeD.innerText;
        console.log("Destino escolhido: " + destino);
        document.querySelector('.descobrir-rotas').style.display = 'block';
    };

    window.enviarRota = function() {
        document.querySelector('.opcoes-destino').style.display = 'none';
        document.querySelector('.descobrir-rotas').style.display = 'none';
        
        console.log("Enviando rota...", origem, destino);
    
        fetch(`${servidor}/api/rota`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ origem: origem, destino: destino })
        })
        .then(response => {
            console.log("Status da resposta:", response.status);
            return response.json();
        })
        .then(data => {
            console.log("Resposta da API: ", data);
            rotasDisponiveis = data.rotas;
            mostrarRotas(rotasDisponiveis);
        })
        .catch(error => {
            console.error('Erro:', error);
        });
    };

    function mostrarRotas(rotas) {
        var resultadoDiv = document.querySelector('.resultado');
        resultadoDiv.style.display = 'flex';  // Mostrar a div resultados
        var botoes = ['rota1', 'rota2', 'rota3'];
        var passagens = ['passagem-rota1', 'passagem-rota2', 'passagem-rota3'];
        
        // Limpa os textos anteriores
        botoes.forEach((botaoId) => {
            document.getElementById(botaoId).innerText = 'Rota indisponível';
            document.getElementsByClassName(passagens[botoes.indexOf(botaoId)])[0].innerText = "Passagens disponíveis: 0";
        });
    
        var rotasArray = Object.entries(rotas);
        
        for (var i = 0; i < botoes.length; i++) {
            var botao = document.getElementById(botoes[i]);
            var passagem = document.getElementsByClassName(passagens[i])[0];
            
            if (rotasArray[i]) {
                var rota = rotasArray[i][0]; // Nome da rota
                var passagensDisponiveis = rotasArray[i][1].passagens; // Passagens disponíveis
                
                botao.innerText = rota;
                passagem.innerText = "Passagens disponíveis: " + passagensDisponiveis;
                botao.setAttribute("data-rota", rota);  // Adicionar atributo data-rota
            } else {
                botao.innerText = 'Rota ' + (i + 1) + ' indisponível';
                passagem.innerText = "Passagens disponíveis: 0";
                botao.removeAttribute("data-rota");  // Remover atributo data-rota
            }
        }
    }

    function verificarToken() {
        return fetch(`${servidor}/api/verificar_token`)
            .then(response => response.json())
            .then(data => {
                hasToken = data.has_token; // Atualiza a variável hasToken com o status retornado
                console.log("Verificação de token:", hasToken ? "Token presente" : "Token ausente");
                return hasToken; // Retorna o status do token
            })
            .catch(error => {
                console.error('Erro ao verificar o token:', error);
                return false; // Retorna false em caso de erro
            });
    }

    window.comprarPassagem = function(rota) {
        verificarToken().then(isTokenPresent => {
            if (!isTokenPresent) {
                alert("Aguarde o token antes de tentar comprar.");
                return;
            }

            console.log("Comprando passagem para a rota:", rota.innerText);

            fetch(`${servidor}/api/comprar`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ rota: rota.getAttribute("data-rota") })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(`Passagem comprada para ${rota.innerText} com sucesso! Passagens restantes: ${data.remaining}`);
                    hasToken = false;  // Perde o token após a compra
                    console.log("Token perdido após a compra.");
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Erro ao comprar passagem:', error);
            });
        });
    };

    function receberToken() {
        hasToken = true;  // Define que agora o cliente possui o token
        alert("Você possui o token! Pode realizar a compra.");
        console.log("Token recebido. Cliente agora possui o token.");
    }

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
