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

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for message sending control
send_queue = []
is_sending = False
send_thread = None
pause_sending = False
stop_sending = False

# Store API configuration
api_config = {
    'endpoint': '',
    'token': '',
    'phone_id': ''
}

# Performance tracking
performance_stats = {
    'week': {'sent': 0, 'failed': 0, 'start_date': datetime.now()},
    'semester': {'sent': 0, 'failed': 0, 'start_date': datetime.now()},
    'year': {'sent': 0, 'failed': 0, 'start_date': datetime.now()}
}

def validate_phone_number(phone):
    """Validate phone number in E.164 format"""
    pattern = r'^\+?[1-9]\d{1,14}$'
    return re.match(pattern, phone.strip()) is not None

def parse_contacts(contacts_text):
    """Parse contacts text and return list of contacts with variables"""
    contacts = []
    lines = contacts_text.strip().split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        parts = [part.strip() for part in line.split(',')]
        if len(parts) < 1:
            continue
            
        phone = parts[0]
        if not validate_phone_number(phone):
            socketio.emit('log_update', {
                'message': f'Linha {line_num}: Telefone inválido - {phone}',
                'type': 'error',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
            continue
            
        nome = parts[1] if len(parts) > 1 else ''
        outro = parts[2] if len(parts) > 2 else ''
        
        contacts.append({
            'phone': phone,
            'nome': nome,
            'outro': outro,
            'line_num': line_num
        })
    
    return contacts

def substitute_variables(message, contact):
    """Substitute variables in message"""
    message = message.replace('{nome}', contact['nome'])
    message = message.replace('{outro}', contact['outro'])
    return message

def send_whatsapp_message(phone, message):
    """Send WhatsApp message using API"""
    try:
        if not api_config['endpoint'] or not api_config['token']:
            return False, "API não configurada"
        
        # This is a mock implementation - replace with actual WhatsApp API call
        headers = {
            'Authorization': f'Bearer {api_config["token"]}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'messaging_product': 'whatsapp',
            'to': phone,
            'type': 'text',
            'text': {'body': message}
        }
        
        # For demo purposes, we'll simulate API call
        # response = requests.post(api_config['endpoint'], headers=headers, json=data)
        # return response.status_code == 200, response.text
        
        # Simulate success/failure for demo
        import random
        success = random.choice([True, True, True, False])  # 75% success rate for demo
        return success, "Mensagem enviada" if success else "Erro na API"
        
    except Exception as e:
        return False, str(e)

def send_messages_worker():
    """Worker function to send messages"""
    global is_sending, pause_sending, stop_sending, send_queue
    
    while send_queue and not stop_sending:
        if pause_sending:
            time.sleep(1)
            continue
            
        contact = send_queue.pop(0)
        message = substitute_variables(contact['message'], contact)
        
        socketio.emit('log_update', {
            'message': f'Enviando para {contact["phone"]} (Linha {contact["line_num"]})...',
            'type': 'info',
            'timestamp': datetime.now().strftime('%H:%M:%S')
        })
        
        success, result = send_whatsapp_message(contact['phone'], message)
        
        if success:
            performance_stats['week']['sent'] += 1
            performance_stats['semester']['sent'] += 1
            performance_stats['year']['sent'] += 1
            socketio.emit('log_update', {
                'message': f'✓ Enviado para {contact["phone"]} - {result}',
                'type': 'success',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
        else:
            performance_stats['week']['failed'] += 1
            performance_stats['semester']['failed'] += 1
            performance_stats['year']['failed'] += 1
            socketio.emit('log_update', {
                'message': f'✗ Falha para {contact["phone"]} - {result}',
                'type': 'error',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
        
        # Update performance stats
        socketio.emit('performance_update', performance_stats)
        
        if send_queue and not stop_sending:
            # Random delay between min and max interval
            delay = random.randint(contact['min_interval'], contact['max_interval'])
            socketio.emit('log_update', {
                'message': f'Aguardando {delay} segundos...',
                'type': 'info',
                'timestamp': datetime.now().strftime('%H:%M:%S')
            })
            time.sleep(delay)
    
    is_sending = False
    socketio.emit('sending_stopped')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/configure', methods=['POST'])
def configure_api():
    global api_config
    data = request.get_json()
    
    api_config['endpoint'] = data.get('endpoint', '')
    api_config['token'] = data.get('token', '')
    api_config['phone_id'] = data.get('phone_id', '')
    
    # Validate API configuration (mock validation)
    if api_config['endpoint'] and api_config['token']:
        return jsonify({'success': True, 'message': 'API configurada com sucesso'})
    else:
        return jsonify({'success': False, 'message': 'Dados de API inválidos'})

@app.route('/api/test-message', methods=['POST'])
def test_message():
    data = request.get_json()
    phone = data.get('phone', '')
    message = data.get('message', '')
    
    if not validate_phone_number(phone):
        return jsonify({'success': False, 'message': 'Número de telefone inválido'})
    
    success, result = send_whatsapp_message(phone, message)
    return jsonify({'success': success, 'message': result})

@app.route('/api/start-sending', methods=['POST'])
def start_sending():
    global send_queue, is_sending, send_thread, pause_sending, stop_sending
    
    if is_sending:
        return jsonify({'success': False, 'message': 'Envio já está em andamento'})
    
    data = request.get_json()
    contacts_text = data.get('contacts', '')
    message_template = data.get('message', '')
    min_interval = int(data.get('min_interval', 5))
    max_interval = int(data.get('max_interval', 10))
    
    contacts = parse_contacts(contacts_text)
    
    if not contacts:
        return jsonify({'success': False, 'message': 'Nenhum contato válido encontrado'})
    
    send_queue = []
    for contact in contacts:
        contact['message'] = message_template
        contact['min_interval'] = min_interval
        contact['max_interval'] = max_interval
        send_queue.append(contact)
    
    is_sending = True
    pause_sending = False
    stop_sending = False
    
    send_thread = threading.Thread(target=send_messages_worker)
    send_thread.start()
    
    return jsonify({'success': True, 'message': f'Iniciando envio para {len(contacts)} contatos'})

@app.route('/api/pause-sending', methods=['POST'])
def pause_sending_route():
    global pause_sending
    pause_sending = not pause_sending
    status = 'pausado' if pause_sending else 'retomado'
    return jsonify({'success': True, 'message': f'Envio {status}', 'paused': pause_sending})

@app.route('/api/stop-sending', methods=['POST'])
def stop_sending_route():
    global stop_sending, send_queue
    stop_sending = True
    send_queue = []
    return jsonify({'success': True, 'message': 'Envio cancelado'})

@app.route('/api/performance', methods=['GET'])
def get_performance():
    return jsonify(performance_stats)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, log_output=True)