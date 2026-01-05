import os
import logging
import qrcode
import io
import random
import threading
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# ========== CONFIGURAÇÃO ==========
TOKEN = os.getenv('TELEGRAM_TOKEN')

# ========== FLASK APP ==========
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot eSIM VIVO Online"

@app.route('/health')
def health():
    return "✅ Bot está online", 200

# ========== DADOS ==========
PLANOS = {
    '31': {'nome': 'VIVO DDD 31', 'preco': 20.00},
    '21': {'nome': 'VIVO DDD 21', 'preco': 20.00},
    '55': {'nome': 'VIVO DDD 55', 'preco': 20.00},
}

carrinhos = {}
pedidos = {}

# ========== FUNÇÕES ==========
def gerar_qr_pix(valor, pedido_id):
    texto_qr = f"PIX:gaila191h@gmail.com:{valor:.2f}:{pedido_id}"
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(texto_qr)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def gerar_pedido_id():
    return f"ESIM{random.randint(1000, 9999)}"

# ========== HANDLERS ==========
def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    qtd = len(carrinhos[user_id])
    
    keyboard = [
        [InlineKeyboardButton("📱 VER PLANOS", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 CARRINHO ({qtd})", callback_data='carrinho')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')]
    ]
    
    update.message.reply_text(
        "🛍️ *LOJA E-SIM VIVO*\n\n"
        "💰 *Valor:* R$20,00\n"
        "📍 *DDDs:* 31, 21, 55\n"
        "⚡ *Ativação:* Imediata\n\n"
        "Escolha uma opção:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def mostrar_planos(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    keyboard = []
    for ddd in ['31', '21', '55']:
        keyboard.append([
            InlineKeyboardButton(f"📱 {PLANOS[ddd]['nome']} - R$20", callback_data=f'ver_{ddd}')
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')])
    
    query.edit_message_text(
        "📋 *Escolha o DDD:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def ver_plano(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    ddd = query.data.split('_')[1]
    
    keyboard = [
        [InlineKeyboardButton("✅ ADICIONAR AO CARRINHO", callback_data=f'add_{ddd}')],
        [InlineKeyboardButton("📋 VER PLANOS", callback_data='planos')]
    ]
    
    query.edit_message_text(
        f"📱 *{PLANOS[ddd]['nome']}*\n"
        f"💰 R$20,00\n"
        f"💾 66GB internet",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def adicionar_carrinho(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    ddd = query.data.split('_')[1]
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    carrinhos[user_id].append(ddd)
    
    keyboard = [
        [InlineKeyboardButton(f"🛒 VER CARRINHO ({len(carrinhos[user_id])})", callback_data='carrinho')],
        [InlineKeyboardButton("📋 MAIS PLANOS", callback_data='planos')]
    ]
    
    query.edit_message_text(
        f"✅ *{PLANOS[ddd]['nome']}* adicionado!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def ver_carrinho(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        query.edit_message_text("🛒 *Carrinho vazio*", parse_mode='Markdown')
        return
    
    itens = carrinhos[user_id]
    total = len(itens) * 20.00
    
    keyboard = [
        [InlineKeyboardButton(f"💰 PAGAR R${total:.2f}", callback_data='pagar')],
        [InlineKeyboardButton("🗑️ LIMPAR CARRINHO", callback_data='limpar')]
    ]
    
    query.edit_message_text(
        f"🛒 *Seu Carrinho*\n\n"
        f"*Itens:* {len(itens)}\n"
        f"💰 *Total:* R${total:.2f}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def pagar(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        query.answer("Carrinho vazio!", show_alert=True)
        return
    
    pedido_id = gerar_pedido_id()
    total = len(carrinhos[user_id]) * 20.00
    
    pedidos[pedido_id] = {
        'user_id': user_id,
        'total': total,
        'pago': False
    }
    
    qr_img = gerar_qr_pix(total, pedido_id)
    
    context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=qr_img,
        caption=f"💰 *QR CODE PIX*\n\n*Pedido:* #{pedido_id}\n*Valor:* R${total:.2f}",
        parse_mode='Markdown'
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ JÁ PAGUEI", callback_data=f'pago_{pedido_id}')]
    ]
    
    context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"📋 *INSTRUÇÕES*\n\n"
             f"1. Pague o PIX acima\n"
             f"2. Clique em JÁ PAGUEI\n\n"
             f"*Chave PIX:* gaila191h@gmail.com\n"
             f"*Valor:* R${total:.2f}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def confirmar_pagamento(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    pedido_id = query.data.split('_')[1]
    
    if pedido_id not in pedidos:
        query.answer("Pedido não encontrado!", show_alert=True)
        return
    
    pedido = pedidos[pedido_id]
    pedido['pago'] = True
    
    user_id = pedido['user_id']
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    query.edit_message_text(
        "✅ *Pagamento confirmado!*\n\n"
        "Seu eSIM será enviado em breve!",
        parse_mode='Markdown'
    )

def suporte(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📱 WHATSAPP", url='https://wa.me/5533984518052')],
        [InlineKeyboardButton("🤖 TELEGRAM", url='https://t.me/Drwed33')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    query.edit_message_text(
        "🆘 *SUPORTE TÉCNICO*\n\n"
        "*WhatsApp:* 33 98451-8052\n"
        "*Telegram:* @Drwed33\n"
        "*Email:* gaila191h@gmail.com\n\n"
        "*Horário:* 8h às 20h",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = str(query.from_user.id)
    qtd = len(carrinhos.get(user_id, []))
    
    keyboard = [
        [InlineKeyboardButton("📱 VER PLANOS", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 CARRINHO ({qtd})", callback_data='carrinho')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')]
    ]
    
    query.edit_message_text(
        "🛍️ *Menu Principal*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def limpar(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = str(query.from_user.id)
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    query.answer("Carrinho limpo!", show_alert=True)
    ver_carrinho(update, context)

def iniciar_bot():
    """Inicia o bot do Telegram"""
    print("🤖 Iniciando bot...")
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("suporte", suporte))
    
    # Callback handlers
    dp.add_handler(CallbackQueryHandler(mostrar_planos, pattern='^planos$'))
    dp.add_handler(CallbackQueryHandler(ver_plano, pattern='^ver_'))
    dp.add_handler(CallbackQueryHandler(adicionar_carrinho, pattern='^add_'))
    dp.add_handler(CallbackQueryHandler(ver_carrinho, pattern='^carrinho$'))
    dp.add_handler(CallbackQueryHandler(pagar, pattern='^pagar$'))
    dp.add_handler(CallbackQueryHandler(confirmar_pagamento, pattern='^pago_'))
    dp.add_handler(CallbackQueryHandler(suporte, pattern='^suporte$'))
    dp.add_handler(CallbackQueryHandler(menu, pattern='^menu$'))
    dp.add_handler(CallbackQueryHandler(limpar, pattern='^limpar$'))
    
    print("✅ Bot configurado")
    updater.start_polling()
    updater.idle()

def iniciar_servidor():
    """Inicia servidor Flask"""
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Iniciando servidor na porta {port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Configurar logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Iniciar em threads separadas
    import threading
    
    # Thread para o bot
    bot_thread = threading.Thread(target=iniciar_bot, daemon=True)
    bot_thread.start()
    
    # Thread para o Flask (main thread)
    iniciar_servidor()
