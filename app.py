from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import time
import threading
import random
import re
from datetime import datetime
import os
import requests   # <--- adicionado

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Variáveis globais para controle de envio de mensagens
fila_envio = []
esta_enviando = False
thread_envio = None
pausar_envio = False
parar_envio = False

# Armazenar configuração da API
config_api = {
    'endpoint': '',
    'token': '',
    'phone_id': '',
    'tipo': ''
}

# APIs pré-configuradas
apis_preconfiguradas = {
    'meta': {
        'nome': 'Meta (Facebook) WhatsApp Business API',
        'endpoint': 'https://graph.facebook.com/v18.0/{phone_id}/messages',
        'requer_phone_id': True
    },
    'evolution': {
        'nome': 'Evolution API',
        'endpoint': 'https://evolution-api.com/message/sendText/{instance}',
        'requer_phone_id': False
    },
    'twilio': {
        'nome': 'Twilio WhatsApp API',
        'endpoint': 'https://api.twilio.com/2010-04-01/Accounts/{phone_id}/Messages.json',
        'requer_phone_id': True
    }
}

# Acompanhamento de performance
estatisticas_performance = {
    'semana': {'enviadas': 0, 'falharam': 0, 'data_inicio': datetime.now()},
    'semestre': {'enviadas': 0, 'falharam': 0, 'data_inicio': datetime.now()},
    'ano': {'enviadas': 0, 'falharam': 0, 'data_inicio': datetime.now()}
}

def validar_numero_telefone(telefone):
    """Validar número de telefone no formato E.164"""
    padrao = r'^\+?[1-9]\d{1,14}$'
    return re.match(padrao, telefone.strip()) is not None

def processar_contatos(texto_contatos):
    """Processar texto de contatos e retornar lista de contatos com variáveis"""
    contatos = []
    linhas = texto_contatos.strip().split('\n')
    
    for num_linha, linha in enumerate(linhas, 1):
        linha = linha.strip()
        if not linha:
            continue
            
        partes = [parte.strip() for parte in linha.split(',')]
        if len(partes) < 1:
            continue
            
        telefone = partes[0]
        if not validar_numero_telefone(telefone):
            socketio.emit('atualizar_log', {
                'mensagem': f'Linha {num_linha}: Telefone inválido - {telefone}',
                'tipo': 'error',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
            continue
            
        nome = partes[1] if len(partes) > 1 else ''
        outro = partes[2] if len(partes) > 2 else ''
        
        contatos.append({
            'telefone': telefone,
            'nome': nome,
            'outro': outro,
            'num_linha': num_linha
        })
    
    return contatos

def substituir_variaveis(mensagem, contato):
    """Substituir variáveis na mensagem"""
    mensagem = mensagem.replace('{nome}', contato['nome'])
    mensagem = mensagem.replace('{outro}', contato['outro'])
    return mensagem

def enviar_mensagem_whatsapp(telefone, mensagem):
    """Enviar mensagem WhatsApp usando API real"""
    try:
        if not config_api['endpoint'] or not config_api['token']:
            return False, "API não configurada"
        
        # --- TWILIO ---
        if config_api['tipo'] == 'twilio':
            sid = config_api['phone_id']   # Account SID
            token = config_api['token']    # Auth Token
            from_number = config_api.get('from', '')
            if not sid or not token or not from_number:
                return False, "Dados do Twilio incompletos"

            endpoint = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
            dados = {
                "From": f"whatsapp:{from_number}",
                "To": f"whatsapp:{telefone}",
                "Body": mensagem
            }
            response = requests.post(endpoint, data=dados, auth=(sid, token))
            if response.status_code == 201:
                return True, "Mensagem enviada com sucesso via Twilio"
            else:
                return False, f"Erro Twilio: {response.text}"

        # --- META (Facebook) ---
        elif config_api['tipo'] == 'meta':
            endpoint = config_api['endpoint'].replace('{phone_id}', config_api['phone_id'])
            headers = {
                'Authorization': f'Bearer {config_api["token"]}',
                'Content-Type': 'application/json'
            }
            dados = {
                'messaging_product': 'whatsapp',
                'to': telefone,
                'type': 'text',
                'text': {'body': mensagem}
            }
            response = requests.post(endpoint, headers=headers, json=dados)
            return response.status_code == 200, response.text

        # --- EVOLUTION ---
        elif config_api['tipo'] == 'evolution':
            endpoint = config_api['endpoint'].replace('{instance}', config_api.get('instance', 'default'))
            headers = {
                'Authorization': f'Bearer {config_api["token"]}',
                'Content-Type': 'application/json'
            }
            dados = {"number": telefone, "text": mensagem}
            response = requests.post(endpoint, headers=headers, json=dados)
            return response.status_code == 200, response.text

        # --- PERSONALIZADA ---
        else:
            headers = {
                'Authorization': f'Bearer {config_api["token"]}',
                'Content-Type': 'application/json'
            }
            dados = {"to": telefone, "message": mensagem}
            response = requests.post(config_api['endpoint'], headers=headers, json=dados)
            return response.status_code == 200, response.text

    except Exception as e:
        return False, str(e)

# Acompanhamento de performance
estatisticas_performance = {
    'semana': {'enviadas': 0, 'falharam': 0, 'data_inicio': datetime.now()},
    'semestre': {'enviadas': 0, 'falharam': 0, 'data_inicio': datetime.now()},
    'ano': {'enviadas': 0, 'falharam': 0, 'data_inicio': datetime.now()}
}

def validar_numero_telefone(telefone):
    """Validar número de telefone no formato E.164"""
    padrao = r'^\+?[1-9]\d{1,14}$'
    return re.match(padrao, telefone.strip()) is not None

def processar_contatos(texto_contatos):
    """Processar texto de contatos e retornar lista de contatos com variáveis"""
    contatos = []
    linhas = texto_contatos.strip().split('\n')
    
    for num_linha, linha in enumerate(linhas, 1):
        linha = linha.strip()
        if not linha:
            continue
            
        partes = [parte.strip() for parte in linha.split(',')]
        if len(partes) < 1:
            continue
            
        telefone = partes[0]
        if not validar_numero_telefone(telefone):
            socketio.emit('atualizar_log', {
                'mensagem': f'Linha {num_linha}: Telefone inválido - {telefone}',
                'tipo': 'error',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
            continue
            
        nome = partes[1] if len(partes) > 1 else ''
        outro = partes[2] if len(partes) > 2 else ''
        
        contatos.append({
            'telefone': telefone,
            'nome': nome,
            'outro': outro,
            'num_linha': num_linha
        })
    
    return contatos

def substituir_variaveis(mensagem, contato):
    """Substituir variáveis na mensagem"""
    mensagem = mensagem.replace('{nome}', contato['nome'])
    mensagem = mensagem.replace('{outro}', contato['outro'])
    return mensagem

def trabalhador_envio_mensagens():
    """Função trabalhadora para enviar mensagens"""
    global esta_enviando, pausar_envio, parar_envio, fila_envio
    
    while fila_envio and not parar_envio:
        if pausar_envio:
            time.sleep(1)
            continue
            
        contato = fila_envio.pop(0)
        mensagem = substituir_variaveis(contato['mensagem'], contato)
        
        socketio.emit('atualizar_log', {
            'mensagem': f'Enviando para {contato["telefone"]} (Linha {contato["num_linha"]})...',
            'tipo': 'info',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
        sucesso, resultado = enviar_mensagem_whatsapp(contato['telefone'], mensagem)
        
        if sucesso:
            estatisticas_performance['semana']['enviadas'] += 1
            estatisticas_performance['semestre']['enviadas'] += 1
            estatisticas_performance['ano']['enviadas'] += 1
            socketio.emit('atualizar_log', {
                'mensagem': f'✓ Enviado para {contato["telefone"]} - {resultado}',
                'tipo': 'success',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
        else:
            estatisticas_performance['semana']['falharam'] += 1
            estatisticas_performance['semestre']['falharam'] += 1
            estatisticas_performance['ano']['falharam'] += 1
            socketio.emit('atualizar_log', {
                'mensagem': f'✗ Falha para {contato["telefone"]} - {resultado}',
                'tipo': 'error',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
        
        # Atualizar estatísticas de performance
        socketio.emit('atualizar_performance', estatisticas_performance)
        
        if fila_envio and not parar_envio:
            # Delay aleatório entre intervalo mínimo e máximo
            atraso = random.randint(contato['intervalo_min'], contato['intervalo_max'])
            socketio.emit('atualizar_log', {
                'mensagem': f'Aguardando {atraso} segundos...',
                'tipo': 'info',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
            time.sleep(atraso)
    
    esta_enviando = False
    socketio.emit('envio_parado')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/configurar', methods=['POST'])
def configurar_api():
    global config_api
    dados = request.get_json()
    
    tipo_api = dados.get('tipo_api', '')
    
    if tipo_api in apis_preconfiguradas:
        config_api['tipo'] = tipo_api
        config_api['endpoint'] = apis_preconfiguradas[tipo_api]['endpoint']
        config_api['token'] = dados.get('token', '')
        config_api['phone_id'] = dados.get('phone_id', '')

        if tipo_api == 'twilio':
            config_api['from'] = dados.get('from', '')   # <-- adiciona o número do WhatsApp
        if tipo_api == 'evolution':
            config_api['instance'] = dados.get('instance', 'default')
    else:
        # API personalizada
        config_api['endpoint'] = dados.get('endpoint', '')
        config_api['token'] = dados.get('token', '')
        config_api['phone_id'] = dados.get('phone_id', '')
        config_api['from'] = dados.get('from', '')       # <-- também salva para personalizadas
        config_api['tipo'] = 'personalizada'

        
    # Validar configuração da API
    if config_api['endpoint'] and config_api['token']:
        return jsonify({'sucesso': True, 'mensagem': 'API configurada com sucesso'})
    else:
        return jsonify({'sucesso': False, 'mensagem': 'Dados de API inválidos'})

@app.route('/api/mensagem-teste', methods=['POST'])
def mensagem_teste():
    dados = request.get_json()
    telefone = dados.get('telefone', '')
    mensagem = dados.get('mensagem', '')
    
    if not validar_numero_telefone(telefone):
        return jsonify({'sucesso': False, 'mensagem': 'Número de telefone inválido'})
    
    sucesso, resultado = enviar_mensagem_whatsapp(telefone, mensagem)
    return jsonify({'sucesso': sucesso, 'mensagem': resultado})

@app.route('/api/iniciar-envio', methods=['POST'])
def iniciar_envio():
    global fila_envio, esta_enviando, thread_envio, pausar_envio, parar_envio
    
    if esta_enviando:
        return jsonify({'sucesso': False, 'mensagem': 'Envio já está em andamento'})
    
    dados = request.get_json()
    texto_contatos = dados.get('contatos', '')
    template_mensagem = dados.get('mensagem', '')
    intervalo_min = int(dados.get('intervalo_min', 5))
    intervalo_max = int(dados.get('intervalo_max', 10))
    
    contatos = processar_contatos(texto_contatos)
    
    if not contatos:
        return jsonify({'sucesso': False, 'mensagem': 'Nenhum contato válido encontrado'})
    
    fila_envio = []
    for contato in contatos:
        contato['mensagem'] = template_mensagem
        contato['intervalo_min'] = intervalo_min
        contato['intervalo_max'] = intervalo_max
        fila_envio.append(contato)
    
    esta_enviando = True
    pausar_envio = False
    parar_envio = False
    
    thread_envio = threading.Thread(target=trabalhador_envio_mensagens)
    thread_envio.start()
    
    return jsonify({'sucesso': True, 'mensagem': f'Iniciando envio para {len(contatos)} contatos'})

@app.route('/api/pausar-envio', methods=['POST'])
def rota_pausar_envio():
    global pausar_envio
    pausar_envio = not pausar_envio
    status = 'pausado' if pausar_envio else 'retomado'
    return jsonify({'sucesso': True, 'mensagem': f'Envio {status}', 'pausado': pausar_envio})

@app.route('/api/parar-envio', methods=['POST'])
def rota_parar_envio():
    global parar_envio, fila_envio
    parar_envio = True
    fila_envio = []
    return jsonify({'sucesso': True, 'mensagem': 'Envio cancelado'})

@app.route('/api/performance', methods=['GET'])
def obter_performance():
    return jsonify(estatisticas_performance)

@app.route('/api/apis-disponiveis', methods=['GET'])
def obter_apis_disponiveis():
    return jsonify(apis_preconfiguradas)

def resetar_estatisticas_periodicas():
    global estatisticas_performance
    while True:
        agora = datetime.now()
        
        # Reset semanal (considerando semana começando no domingo)
        if (agora - estatisticas_performance['semana']['data_inicio']).days >= 7:
            estatisticas_performance['semana'] = {'enviadas': 0, 'falharam': 0, 'data_inicio': agora}
        
        # Reset semestral (aproximado: 6 meses = 182 dias)
        if (agora - estatisticas_performance['semestre']['data_inicio']).days >= 182:
            estatisticas_performance['semestre'] = {'enviadas': 0, 'falharam': 0, 'data_inicio': agora}
        
        # Reset anual
        if (agora - estatisticas_performance['ano']['data_inicio']).days >= 365:
            estatisticas_performance['ano'] = {'enviadas': 0, 'falharam': 0, 'data_inicio': agora}
        
        # Atualizar clientes conectados via SocketIO
        socketio.emit('atualizar_performance', estatisticas_performance)
        time.sleep(60)  # Verifica a cada minuto


if __name__ == '__main__':
    thread_reset = threading.Thread(target=resetar_estatisticas_periodicas)
    thread_reset.daemon = True
    thread_reset.start()
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, log_output=True)
