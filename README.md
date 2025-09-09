# Sistema de Envio de Mensagens em Massa com Monitoramento em Tempo Real

Este projeto é uma **plataforma web para envio automatizado de mensagens** via APIs como **Twilio, Meta e Evolution**, permitindo o envio para múltiplos contatos com monitoramento em tempo real.

## Funcionalidades principais

* **Envio em lote**: Dispara mensagens para vários contatos de forma programada, com intervalos configuráveis.
* **Suporte a múltiplas APIs**: Integração com Twilio, Meta e Evolution.
* **Monitoramento em tempo real**: Gráfico dinâmico mostrando mensagens enviadas e falhas.
* **Logs detalhados**: Histórico de envios e erros, com marcações de eventos importantes (ex.: falhas do Twilio).
* **Testes de envio**: Permite enviar mensagens de teste antes do envio em massa.
* **Interface amigável**: Painel web com botões de iniciar, pausar, parar e limpar logs.
* **Alertas visuais**: Marcação automática de erros no gráfico para fácil identificação.

## Tecnologias utilizadas

* **Front-end**: HTML, CSS, JavaScript, Bootstrap, Chart.js
* **Back-end**: Node.js, Express, Socket.IO
* **APIs externas**: Twilio, Meta, Evolution

## Objetivo do projeto

Facilitar o envio de mensagens em massa de forma **controlada, monitorada e segura**, permitindo acompanhar o desempenho e identificar problemas em tempo real, com logs detalhados e gráficos interativos.
