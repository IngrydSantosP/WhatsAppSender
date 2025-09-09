// Initialize Socket.IO
const socket = io();
let isPaused = false;
let contatosSalvos = "";
let mensagemSalva = "";
let chartEnvios;

// Tooltips Bootstrap
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
});

// === Socket.IO Events ===
socket.on('atualizar_log', function(data) {
    adicionarEntradaLog(data.mensagem, data.tipo, data.timestamp);
});

socket.on('atualizar_performance', function(data) {
    atualizarPerformance(data);
});

socket.on('envio_parado', function() {
    document.getElementById('startBtn').disabled = false;
    document.getElementById('pauseBtn').disabled = true;
    document.getElementById('stopBtn').disabled = true;
    adicionarEntradaLog('Envio finalizado', 'info', new Date().toLocaleTimeString());
});

// === Funções de UI ===
function adicionarEntradaLog(mensagem, tipo, timestamp) {
    const areaLog = document.getElementById('logArea');
    const entradaLog = document.createElement('div');
    entradaLog.className = `log-entry log-${tipo}`;
    entradaLog.innerHTML = `<strong>[${timestamp}]</strong> ${mensagem}`;
    areaLog.appendChild(entradaLog);
    areaLog.scrollTop = areaLog.scrollHeight;
}

function atualizarPerformance(dados) {
  document.getElementById("weekSent").textContent = dados.semana.enviadas;
  document.getElementById("weekFailed").textContent = dados.semana.falharam;
  document.getElementById("semesterSent").textContent = dados.semestre.enviadas;
  document.getElementById("semesterFailed").textContent = dados.semestre.falharam;
  document.getElementById("yearSent").textContent = dados.ano.enviadas;
  document.getElementById("yearFailed").textContent = dados.ano.falharam;

  if (chartEnvios) {
    const now = new Date();
    const timeLabel = now.toLocaleTimeString();

    chartEnvios.data.labels.push(timeLabel);
    chartEnvios.data.datasets[0].data.push(dados.semana.enviadas);
    chartEnvios.data.datasets[1].data.push(dados.semana.falharam);

    if (chartEnvios.data.labels.length > 20) {
      chartEnvios.data.labels.shift();
      chartEnvios.data.datasets[0].data.shift();
      chartEnvios.data.datasets[1].data.shift();
    }
    chartEnvios.update();
  }
}

// === Funções chamadas pelos botões ===
async function configurarAPI() {
  const tipoApi = document.getElementById("tipoApi").value;
  const token = document.getElementById("apiToken").value;
  const phoneId = document.getElementById("phoneId").value;
  const endpoint = document.getElementById("apiEndpoint").value;
  const fromNumber = document.getElementById("fromNumber").value;

  const res = await fetch("/api/configurar", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ tipo_api: tipoApi, token, phone_id: phoneId, endpoint, from: fromNumber })
  });
  const data = await res.json();
  adicionarEntradaLog(data.mensagem, data.sucesso ? "success" : "error", new Date().toLocaleTimeString());
}

function alterarTipoApi() {
  const tipo = document.getElementById("tipoApi").value;
  const camposApi = document.getElementById("camposApi");
  const campoFromNumber = document.getElementById("campoFromNumber");
  const btn = document.getElementById("btnConfigurar");

  if (tipo) {
    camposApi.style.display = "";
    campoFromNumber.style.display = "";
    btn.disabled = false;

    if (tipo === "meta") {
      document.getElementById("apiEndpoint").value = "https://graph.facebook.com/v18.0/{phone_id}/messages";
    } else if (tipo === "evolution") {
      document.getElementById("apiEndpoint").value = "https://evolution-api.com/message/sendText/{instance}";
    } else if (tipo === "twilio") {
      document.getElementById("apiEndpoint").value = "https://api.twilio.com/2010-04-01/Accounts/{phone_id}/Messages.json";
    } else {
      document.getElementById("apiEndpoint").value = "";
    }
  } else {
    camposApi.style.display = "none";
    campoFromNumber.style.display = "none";
    btn.disabled = true;
  }
}

function salvarContatos() {
  contatosSalvos = document.getElementById("contactsList").value;
  adicionarEntradaLog("Contatos salvos", "info", new Date().toLocaleTimeString());
}

function salvarMensagem() {
  mensagemSalva = document.getElementById("messageText").value;
  adicionarEntradaLog("Mensagem salva", "info", new Date().toLocaleTimeString());
}

async function sendTestMessage() {
  const telefone = document.getElementById("testPhone").value;
  const mensagem = document.getElementById("messageText").value;

  const res = await fetch("/api/mensagem-teste", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ telefone, mensagem })
  });
  const data = await res.json();
  adicionarEntradaLog(`[Teste] ${data.mensagem}`, data.sucesso ? "success" : "error", new Date().toLocaleTimeString());
}

async function startSending() {
  if (!contatosSalvos || !mensagemSalva) {
    adicionarEntradaLog("Salve os contatos e a mensagem antes de iniciar!", "error", new Date().toLocaleTimeString());
    return;
  }

  const intervaloMin = document.getElementById("minInterval").value;
  const intervaloMax = document.getElementById("maxInterval").value;

  const res = await fetch("/api/iniciar-envio", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      contatos: contatosSalvos,
      mensagem: mensagemSalva,
      intervalo_min: intervaloMin,
      intervalo_max: intervaloMax
    })
  });
  const data = await res.json();
  adicionarEntradaLog(data.mensagem, data.sucesso ? "success" : "error", new Date().toLocaleTimeString());

  if (data.sucesso) {
    document.getElementById("startBtn").disabled = true;
    document.getElementById("pauseBtn").disabled = false;
    document.getElementById("stopBtn").disabled = false;
  }
}

async function pauseSending() {
  const res = await fetch("/api/pausar-envio", { method: "POST" });
  const data = await res.json();
  adicionarEntradaLog(data.mensagem, "info", new Date().toLocaleTimeString());

  document.getElementById("pauseBtn").textContent = data.pausado ? "Retomar" : "Pausar";
}

async function stopSending() {
  const res = await fetch("/api/parar-envio", { method: "POST" });
  const data = await res.json();
  adicionarEntradaLog(data.mensagem, "info", new Date().toLocaleTimeString());

  document.getElementById("startBtn").disabled = false;
  document.getElementById("pauseBtn").disabled = true;
  document.getElementById("stopBtn").disabled = true;
}

function clearLogs() {
  document.getElementById("logArea").innerHTML = "";
  adicionarEntradaLog("Logs limpos", "info", new Date().toLocaleTimeString());
}




// === Chart.js - Gráfico de Envios em Tempo Real ===
document.addEventListener("DOMContentLoaded", function () {
    const ctx = document.getElementById("chartEnvios")?.getContext("2d");
    if (ctx) {
        chartEnvios = new Chart(ctx, {
            type: "line",
            data: {
                labels: [],
                datasets: [
                    {
                        label: "Enviadas",
                        data: [],
                        borderColor: "#4caf50",
                        backgroundColor: "rgba(76,175,80,0.2)",
                        fill: true,
                        tension: 0.3
                    },
                    {
                        label: "Falhas",
                        data: [],
                        borderColor: "#f44336",
                        backgroundColor: "rgba(244,67,54,0.2)",
                        fill: true,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                animation: { duration: 200 },
                scales: {
                    x: { ticks: { color: "#fff" } },
                    y: { ticks: { color: "#fff" }, beginAtZero: true }
                },
                plugins: { legend: { labels: { color: "#fff" } } }
            }
        });
    }
});

// Bootstrap tooltips
document.addEventListener("DOMContentLoaded", function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
});

// === Socket.IO Events ===
socket.on("atualizar_log", function(data) {
    adicionarEntradaLog(data.mensagem, data.tipo, data.timestamp);
});

socket.on("atualizar_performance", function(dados) {
    atualizarPerformance(dados);
    atualizarGrafico(dados);
});

socket.on("envio_parado", function() {
    document.getElementById("startBtn").disabled = false;
    document.getElementById("pauseBtn").disabled = true;
    document.getElementById("stopBtn").disabled = true;
    adicionarEntradaLog("Envio finalizado", "info", new Date().toLocaleTimeString());
});

// === Funções de UI ===
function adicionarEntradaLog(mensagem, tipo, timestamp) {
    const areaLog = document.getElementById("logArea");
    const entradaLog = document.createElement("div");
    entradaLog.className = `log-entry log-${tipo}`;
    entradaLog.innerHTML = `<strong>[${timestamp}]</strong> ${mensagem}`;
    areaLog.appendChild(entradaLog);
    areaLog.scrollTop = areaLog.scrollHeight;
}

function atualizarPerformance(dados) {
    document.getElementById("weekSent").textContent = dados.semana.enviadas;
    document.getElementById("weekFailed").textContent = dados.semana.falharam;
    document.getElementById("semesterSent").textContent = dados.semestre.enviadas;
    document.getElementById("semesterFailed").textContent = dados.semestre.falharam;
    document.getElementById("yearSent").textContent = dados.ano.enviadas;
    document.getElementById("yearFailed").textContent = dados.ano.falharam;
}

function atualizarGrafico(dados) {
    if (!chartEnvios) return;
    const now = new Date().toLocaleTimeString();

    chartEnvios.data.labels.push(now);
    chartEnvios.data.datasets[0].data.push(dados.semana.enviadas);
    chartEnvios.data.datasets[1].data.push(dados.semana.falharam);

    // manter apenas últimos 20 pontos
    if (chartEnvios.data.labels.length > 20) {
        chartEnvios.data.labels.shift();
        chartEnvios.data.datasets[0].data.shift();
        chartEnvios.data.datasets[1].data.shift();
    }
    chartEnvios.update();
}
