import os
import logging
import qrcode
import io
import random
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# ========== CONFIGURAÇÃO ==========
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot eSIM Online"

@app.route('/health')
def health():
    return "✅ OK", 200

# ========== DADOS ==========
PLANOS = {
    '31': 'VIVO DDD 31 - R$20',
    '21': 'VIVO DDD 21 - R$20', 
    '55': 'VIVO DDD 55 - R$20'
}

carrinhos = {}

# ========== FUNÇÕES ==========
def gerar_qr_pix(valor, pedido_id):
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(f"PIX:gaila191h@gmail.com:{valor}:{pedido_id}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

# ========== HANDLERS ==========
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = str(user.id)
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    qtd = len(carrinhos[user_id])
    
    keyboard = [
        [InlineKeyboardButton("📱 VER PLANOS", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 CARRINHO ({qtd})", callback_data='carrinho')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')]
    ]
    
    update.message.reply_text(
        f"👋 Olá {user.first_name}!\n\n"
        "🛍️ *LOJA E-SIM VIVO*\n"
        "💰 R$20 por chip\n"
        "📍 DDDs: 31, 21, 55\n"
        "⚡ Ativação imediata\n\n"
        "Escolha uma opção:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def mostrar_planos(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📱 VIVO DDD 31 - R$20", callback_data='add_31')],
        [InlineKeyboardButton("📱 VIVO DDD 21 - R$20", callback_data='add_21')],
        [InlineKeyboardButton("📱 VIVO DDD 55 - R$20", callback_data='add_55')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    query.edit_message_text(
        "📋 *PLANOS DISPONÍVEIS:*\n\n"
        "Selecione um DDD:",
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
        f"✅ *{PLANOS[ddd]}* adicionado!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def ver_carrinho(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        keyboard = [[InlineKeyboardButton("📱 VER PLANOS", callback_data='planos')]]
        query.edit_message_text("🛒 *Carrinho vazio*", 
                              reply_markup=InlineKeyboardMarkup(keyboard),
                              parse_mode='Markdown')
        return
    
    itens = carrinhos[user_id]
    total = len(itens) * 20
    
    keyboard = [
        [InlineKeyboardButton(f"💰 PAGAR R${total}", callback_data='pagar')],
        [InlineKeyboardButton("🗑️ LIMPAR", callback_data='limpar')]
    ]
    
    query.edit_message_text(
        f"🛒 *SEU CARRINHO*\n\n"
        f"*Itens:* {len(itens)}\n"
        f"💰 *Total:* R${total}\n\n"
        f"Clique em PAGAR para finalizar.",
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
    
    pedido_id = f"ESIM{random.randint(1000, 9999)}"
    total = len(carrinhos[user_id]) * 20
    
    qr_img = gerar_qr_pix(total, pedido_id)
    
    context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=qr_img,
        caption=f"💰 *QR CODE PIX*\n\n*Pedido:* #{pedido_id}\n*Valor:* R${total}"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ JÁ PAGUEI", callback_data=f'pago_{pedido_id}')]
    ]
    
    context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"📋 *INSTRUÇÕES*\n\n"
             f"*Pedido:* #{pedido_id}\n"
             f"*Valor:* R${total}\n"
             f"*Chave PIX:* gaila191h@gmail.com\n\n"
             f"1. Pague o PIX acima\n"
             f"2. Clique em JÁ PAGUEI",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def confirmar_pagamento(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    pedido_id = query.data.split('_')[1]
    
    user_id = str(query.from_user.id)
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    keyboard = [
        [InlineKeyboardButton("📱 COMPRAR MAIS", callback_data='planos')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')]
    ]
    
    query.edit_message_text(
        f"✅ *PAGAMENTO CONFIRMADO!*\n\n"
        f"*Pedido:* #{pedido_id}\n"
        f"Seu eSIM foi enviado!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def suporte(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📱 WHATSAPP", url='https://wa.me/5533984518052')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    query.edit_message_text(
        "🆘 *SUPORTE*\n\n"
        "*WhatsApp:* 33 98451-8052\n"
        "*Telegram:* @Drwed33\n"
        "*Email:* gaila191h@gmail.com",
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
        "🛍️ *MENU PRINCIPAL*",
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

def main():
    """Função principal"""
    print("🤖 Iniciando Bot eSIM VIVO...")
    
    if not TOKEN:
        print("❌ ERRO: TELEGRAM_TOKEN não configurado!")
        return
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("suporte", suporte))
    
    # Callback handlers
    dp.add_handler(CallbackQueryHandler(mostrar_planos, pattern='^planos$'))
    dp.add_handler(CallbackQueryHandler(adicionar_carrinho, pattern='^add_'))
    dp.add_handler(CallbackQueryHandler(ver_carrinho, pattern='^carrinho$'))
    dp.add_handler(CallbackQueryHandler(pagar, pattern='^pagar$'))
    dp.add_handler(CallbackQueryHandler(confirmar_pagamento, pattern='^pago_'))
    dp.add_handler(CallbackQueryHandler(suporte, pattern='^suporte$'))
    dp.add_handler(CallbackQueryHandler(menu, pattern='^menu$'))
    dp.add_handler(CallbackQueryHandler(limpar, pattern='^limpar$'))
    
    print("✅ Bot configurado!")
    print("💰 Valor: R$20")
    print("📍 DDDs: 31, 21, 55")
    
    updater.start_polling()
    updater.idle()

def run_flask():
    """Roda Flask"""
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Servidor web na porta {port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Iniciar Flask em thread separada
    import threading
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Bot na thread principal
    main()
