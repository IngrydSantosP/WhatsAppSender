from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import time
import threading
import random
import re
import requests
from datetime import datetime, timedelta
import os
import sqlite3

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
    }
}

# Banco de dados SQLite
def inicializar_banco():
    """Inicializar banco de dados SQLite"""
    conn = sqlite3.connect('contatos.db')
    cursor = conn.cursor()
    
    # Criar tabela de contatos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telefone TEXT UNIQUE NOT NULL,
            nome TEXT,
            outro TEXT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultima_modificacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Criar tabela de listas de contatos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listas_contatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_lista TEXT NOT NULL,
            descricao TEXT,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Criar tabela de performance detalhada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telefone TEXT,
            status TEXT,
            mensagem TEXT,
            data_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

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

def salvar_contato(telefone, nome='', outro=''):
    """Salvar contato no banco de dados"""
    try:
        conn = sqlite3.connect('contatos.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO contatos (telefone, nome, outro, ultima_modificacao)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (telefone, nome, outro))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao salvar contato: {e}")
        return False

def obter_contatos():
    """Obter todos os contatos do banco de dados"""
    try:
        conn = sqlite3.connect('contatos.db')
        cursor = conn.cursor()
        cursor.execute('SELECT telefone, nome, outro FROM contatos ORDER BY ultima_modificacao DESC')
        contatos = cursor.fetchall()
        conn.close()
        return [{'telefone': c[0], 'nome': c[1], 'outro': c[2]} for c in contatos]
    except Exception as e:
        print(f"Erro ao obter contatos: {e}")
        return []

def salvar_log_performance(telefone, status, mensagem):
    """Salvar log de performance no banco"""
    try:
        conn = sqlite3.connect('contatos.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO performance_logs (telefone, status, mensagem)
            VALUES (?, ?, ?)
        ''', (telefone, status, mensagem))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao salvar log: {e}")

def obter_dados_graficos():
    """Obter dados para gráficos de performance"""
    try:
        conn = sqlite3.connect('contatos.db')
        cursor = conn.cursor()
        
        # Dados dos últimos 7 dias
        cursor.execute('''
            SELECT DATE(data_envio) as data, 
                   SUM(CASE WHEN status = 'sucesso' THEN 1 ELSE 0 END) as sucessos,
                   SUM(CASE WHEN status = 'erro' THEN 1 ELSE 0 END) as erros
            FROM performance_logs 
            WHERE data_envio >= date('now', '-7 days')
            GROUP BY DATE(data_envio)
            ORDER BY data
        ''')
        dados_semana = cursor.fetchall()
        
        # Dados mensais do ano atual
        cursor.execute('''
            SELECT strftime('%Y-%m', data_envio) as mes,
                   SUM(CASE WHEN status = 'sucesso' THEN 1 ELSE 0 END) as sucessos,
                   SUM(CASE WHEN status = 'erro' THEN 1 ELSE 0 END) as erros
            FROM performance_logs 
            WHERE strftime('%Y', data_envio) = strftime('%Y', 'now')
            GROUP BY strftime('%Y-%m', data_envio)
            ORDER BY mes
        ''')
        dados_ano = cursor.fetchall()
        
        conn.close()
        
        return {
            'semana': [{'data': d[0], 'sucessos': d[1], 'erros': d[2]} for d in dados_semana],
            'ano': [{'mes': d[0], 'sucessos': d[1], 'erros': d[2]} for d in dados_ano]
        }
    except Exception as e:
        print(f"Erro ao obter dados gráficos: {e}")
        return {'semana': [], 'ano': []}

def enviar_mensagem_whatsapp(telefone, mensagem):
    """Enviar mensagem WhatsApp usando API"""
    try:
        if not config_api['endpoint'] or not config_api['token']:
            return False, "API não configurada"
        
        headers = {
            'Authorization': f'Bearer {config_api["token"]}',
            'Content-Type': 'application/json'
        }
        
        # Configurar dados baseado no tipo de API
        if config_api['tipo'] == 'meta':
            endpoint = config_api['endpoint'].replace('{phone_id}', config_api['phone_id'])
            dados = {
                'messaging_product': 'whatsapp',
                'to': telefone,
                'type': 'text',
                'text': {'body': mensagem}
            }
        elif config_api['tipo'] == 'evolution':
            endpoint = config_api['endpoint'].replace('{instance}', config_api.get('instance', 'default'))
            dados = {
                'number': telefone,
                'text': mensagem
            }
        else:
            # API personalizada
            endpoint = config_api['endpoint']
            dados = {
                'to': telefone,
                'message': mensagem
            }
        
        # Para demonstração, simular chamada da API
        # response = requests.post(endpoint, headers=headers, json=dados)
        # return response.status_code == 200, response.text
        
        # Simular sucesso/falha para demo
        import random
        sucesso = random.choice([True, True, True, False])  # 75% taxa de sucesso para demo
        return sucesso, "Mensagem enviada" if sucesso else "Erro na API"
        
    except Exception as e:
        return False, str(e)

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
            salvar_log_performance(contato['telefone'], 'sucesso', resultado)
            socketio.emit('atualizar_log', {
                'mensagem': f'✓ Enviado para {contato["telefone"]} - {resultado}',
                'tipo': 'success',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
        else:
            estatisticas_performance['semana']['falharam'] += 1
            estatisticas_performance['semestre']['falharam'] += 1
            estatisticas_performance['ano']['falharam'] += 1
            salvar_log_performance(contato['telefone'], 'erro', resultado)
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
        
        if tipo_api == 'evolution':
            config_api['instance'] = dados.get('instance', 'default')
    else:
        # API personalizada
        config_api['endpoint'] = dados.get('endpoint', '')
        config_api['token'] = dados.get('token', '')
        config_api['phone_id'] = dados.get('phone_id', '')
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
        # Salvar contato no banco de dados
        salvar_contato(contato['telefone'], contato['nome'], contato['outro'])
    
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

@app.route('/api/contatos', methods=['GET'])
def listar_contatos():
    contatos = obter_contatos()
    return jsonify(contatos)

@app.route('/api/contatos', methods=['POST'])
def adicionar_contato():
    dados = request.get_json()
    telefone = dados.get('telefone', '')
    nome = dados.get('nome', '')
    outro = dados.get('outro', '')
    
    if not validar_numero_telefone(telefone):
        return jsonify({'sucesso': False, 'mensagem': 'Número de telefone inválido'})
    
    sucesso = salvar_contato(telefone, nome, outro)
    if sucesso:
        return jsonify({'sucesso': True, 'mensagem': 'Contato salvo com sucesso'})
    else:
        return jsonify({'sucesso': False, 'mensagem': 'Erro ao salvar contato'})

@app.route('/api/preview-mensagem', methods=['POST'])
def preview_mensagem():
    dados = request.get_json()
    template_mensagem = dados.get('mensagem', '')
    contato_exemplo = dados.get('contato', {'nome': 'João', 'outro': 'amigo'})
    
    mensagem_final = substituir_variaveis(template_mensagem, contato_exemplo)
    return jsonify({'mensagem_preview': mensagem_final})

@app.route('/api/graficos-performance', methods=['GET'])
def obter_graficos_performance():
    dados = obter_dados_graficos()
    return jsonify(dados)

if __name__ == '__main__':
    inicializar_banco()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, log_output=True)