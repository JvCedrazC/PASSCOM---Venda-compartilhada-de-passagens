document.addEventListener('DOMContentLoaded', function() {
    var origem;
    var destino;
    var nome;

    console.log("Carregou o DOM Macedo!")
    // Cria um soquete TCP
    chrome.sockets.ttcp.create({}, function(createInfo) {
        var socketId = createInfo.socketId;
        console.log("Criou o ID do Socket")


        // Conecta ao servidor
        chrome.sockets.tcp.connect(socketId, '172.16.103.222', 8080, function(result) {
            if (result < 0) {
                console.log('Erro ao conectar: ' + chrome.runtime.lastError.message);
            } else {
                console.log('Conectado com sucesso');

                // Envia dados
                var data = new TextEncoder().encode('Sua mensagem aqui');
                chrome.sockets.tcp.send(socketId, data.buffer, function(sendInfo) {
                    if (sendInfo.resultCode < 0) {
                        console.log('Erro ao enviar: ' + chrome.runtime.lastError.message);
                    } else {
                        console.log('Dados enviados com sucesso');
                    }
                });

                // Recebe dados
                chrome.sockets.tcp.onReceive.addListener(function(receiveInfo) {
                    if (receiveInfo.socketId === socketId) {
                        var receivedData = new TextDecoder().decode(receiveInfo.data);
                        console.log('Dados recebidos: ' + receivedData);
                    }
                });
            }
        });

        // Fecha o soquete ao sair
        window.addEventListener('beforeunload', function() {
            chrome.sockets.tcp.close(socketId, function() {
                console.log('Soquete fechado');
            });
        });
    });
});



function receberOrigem(CidadeO){
    origem = CidadeO.innerText;
    window.alert("Você escolheu " + origem);    

    // Esconde a div de origem
    document.querySelector('.opcoes-origem').style.display = 'none';

    // Mostra a div de destino
    document.querySelector('.opcoes-destino').style.display = 'flex';

    document.querySelector('.button-voltar').style.display = "block";

    document.querySelector('.nomeUser').classList.add('input-hidden'); // Oculta o input

    var paragrafo = document.getElementById("paragrafo-origem-destino");
    paragrafo.innerText = "Escolha seu local de destino"



}

function receberDestino(CidadeD){
    destino = CidadeD.innerText;
    window.alert("Você escolheu " + destino);

    document.querySelector('.descobrir-rotas').style.display = 'flex';


}

function descobrirRotas(){ 
    nome = document.querySelector('.nomeUser') 
    
    


}

function voltar(){
    // Esconde a div de destino
    document.querySelector('.opcoes-destino').style.display = 'none';

    // Mostra a div de origem
    document.querySelector('.opcoes-origem').style.display = 'flex';

    // Esconde o botão "Voltar"
    document.querySelector('.button-voltar').style.display = 'none';

    document.querySelector('.descobrir-rotas').style.display = 'none';

    document.querySelector('.nomeUser').classList.remove('input-hidden'); // Mostra o input

    var paragrafo = document.getElementById("paragrafo-origem-destino");
    paragrafo.innerText = "Escolha seu local de origem"



}
