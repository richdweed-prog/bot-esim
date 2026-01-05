import os
import logging
import qrcode
import io
import random
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# Configuração
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot eSIM Online"

@app.route('/health')
def health():
    return "✅ OK", 200

# Dados
PLANOS = {
    '31': {'nome': 'VIVO DDD 31', 'preco': 20.00},
    '21': {'nome': 'VIVO DDD 21', 'preco': 20.00},
    '55': {'nome': 'VIVO DDD 55', 'preco': 20.00},
}

carrinhos = {}
pedidos = {}

# Funções
def gerar_qr_pix(valor, pedido_id):
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(f"PIX:gaila191h@gmail.com:{valor}:{pedido_id}")
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def gerar_pedido_id():
    return f"ESIM{random.randint(1000, 9999)}"

# Handlers
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
        "🛍️ *LOJA E-SIM VIVO* 🚀\n\n"
        "💰 R$20,00 por chip\n"
        "📍 DDDs: 31, 21, 55\n"
        "💾 66GB cada\n"
        "⚡ Ativação imediata\n\n"
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
        "📋 *PLANOS DISPONÍVEIS:*\n\n"
        "1️⃣ VIVO DDD 31 - R$20\n"
        "2️⃣ VIVO DDD 21 - R$20\n"
        "3️⃣ VIVO DDD 55 - R$20\n\n"
        "Todos com 66GB de internet.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def ver_plano(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    ddd = query.data.split('_')[1]
    
    keyboard = [
        [InlineKeyboardButton("✅ ADICIONAR AO CARRINHO", callback_data=f'add_{ddd}')],
        [InlineKeyboardButton("📋 VER TODOS", callback_data='planos')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    query.edit_message_text(
        f"📱 *{PLANOS[ddd]['nome']}*\n\n"
        f"💰 *Valor:* R$20,00\n"
        f"💾 *Dados:* 66GB\n"
        f"⏰ *Validade:* 30 dias\n"
        f"⚡ *Ativação:* Imediata",
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
        [InlineKeyboardButton("➕ ADICIONAR MAIS", callback_data='planos')],
        [InlineKeyboardButton("💰 FINALIZAR COMPRA", callback_data='pagar')]
    ]
    
    query.edit_message_text(
        f"✅ *{PLANOS[ddd]['nome']}* adicionado!\n\n"
        f"*Itens no carrinho:* {len(carrinhos[user_id])}\n"
        f"*Total:* R${len(carrinhos[user_id]) * 20:.2f}",
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
    total = len(itens) * 20.00
    
    keyboard = [
        [InlineKeyboardButton(f"💰 PAGAR R${total:.2f}", callback_data='pagar')],
        [InlineKeyboardButton("🗑️ LIMPAR CARRINHO", callback_data='limpar')],
        [InlineKeyboardButton("📱 CONTINUAR COMPRANDO", callback_data='planos')]
    ]
    
    query.edit_message_text(
        f"🛒 *SEU CARRINHO*\n\n"
        f"*Itens:* {len(itens)}\n"
        f"💰 *Total:* R${total:.2f}\n\n"
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
    
    pedido_id = gerar_pedido_id()
    total = len(carrinhos[user_id]) * 20.00
    
    pedidos[pedido_id] = {
        'user_id': user_id,
        'total': total,
        'pago': False,
        'data': datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    
    qr_img = gerar_qr_pix(total, pedido_id)
    
    context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=qr_img,
        caption=f"💰 *QR CODE PIX*\n\n*Pedido:* #{pedido_id}\n*Valor:* R${total:.2f}",
        parse_mode='Markdown'
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ JÁ PAGUEI", callback_data=f'pago_{pedido_id}')],
        [InlineKeyboardButton("🆘 AJUDA", callback_data='ajuda_pix')]
    ]
    
    context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"📋 *INSTRUÇÕES DE PAGAMENTO*\n\n"
             f"*Pedido:* #{pedido_id}\n"
             f"*Valor:* R${total:.2f}\n"
             f"*Chave PIX:* gaila191h@gmail.com\n"
             f"*Nome:* Solineia Guimaraes\n\n"
             f"1. Abra seu app bancário\n"
             f"2. Pague o valor acima\n"
             f"3. Clique em JÁ PAGUEI\n\n"
             f"Dúvidas? Clique em AJUDA",
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
    
    keyboard = [
        [InlineKeyboardButton("📱 COMPRAR MAIS", callback_data='planos')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')]
    ]
    
    query.edit_message_text(
        f"✅ *PAGAMENTO CONFIRMADO!*\n\n"
        f"*Pedido:* #{pedido_id}\n"
        f"*Status:* ✅ Entregue\n"
        f"*Data:* {pedido['data']}\n\n"
        f"Seu eSIM foi enviado com sucesso!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def suporte(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📱 WHATSAPP", url='https://wa.me/5533984518052')],
        [InlineKeyboardButton("🤖 TELEGRAM", url='https://t.me/Drwed33')],
        [InlineKeyboardButton("📧 EMAIL", url='mailto:richdweed@gmail.com')],
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

def ajuda_pix(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(
        "💰 *AJUDA COM PIX*\n\n"
        "*Chave PIX:* gaila191h@gmail.com\n"
        "*Nome:* Solineia Guimaraes\n"
        "*Cidade:* Belo Horizonte\n\n"
        "*Problemas?* WhatsApp: 33 98451-8052",
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
        [InlineKeyboardButton("❓ AJUDA", callback_data='ajuda')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')]
    ]
    
    query.edit_message_text(
        "🛍️ *MENU PRINCIPAL*\n\n"
        "Escolha uma opção:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def limpar(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = str(query.from_user.id)
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    query.answer("🛒 Carrinho limpo!", show_alert=True)
    ver_carrinho(update, context)

def ajuda(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    query.edit_message_text(
        "❓ *AJUDA*\n\n"
        "*Como comprar:*\n"
        "1. Escolha DDD\n"
        "2. Adicione ao carrinho\n"
        "3. Pague com PIX\n"
        "4. Receba confirmação\n\n"
        "*Valor:* R$20 por chip\n"
        "*DDDs:* 31, 21, 55\n"
        "*Dados:* 66GB cada",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def error(update: Update, context: CallbackContext):
    print(f"Update {update} caused error {context.error}")

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
    dp.add_handler(CallbackQueryHandler(ver_plano, pattern='^ver_'))
    dp.add_handler(CallbackQueryHandler(adicionar_carrinho, pattern='^add_'))
    dp.add_handler(CallbackQueryHandler(ver_carrinho, pattern='^carrinho$'))
    dp.add_handler(CallbackQueryHandler(pagar, pattern='^pagar$'))
    dp.add_handler(CallbackQueryHandler(confirmar_pagamento, pattern='^pago_'))
    dp.add_handler(CallbackQueryHandler(suporte, pattern='^suporte$'))
    dp.add_handler(CallbackQueryHandler(menu, pattern='^menu$'))
    dp.add_handler(CallbackQueryHandler(limpar, pattern='^limpar$'))
    dp.add_handler(CallbackQueryHandler(ajuda, pattern='^ajuda$'))
    dp.add_handler(CallbackQueryHandler(ajuda_pix, pattern='^ajuda_pix$'))
    
    dp.add_error_handler(error)
    
    print("✅ Bot configurado com sucesso!")
    print("💰 Valor: R$20,00")
    print("📍 DDDs: 31, 21, 55")
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    print("🚀 Iniciando serviços...")
    
    # Rodar Flask e Bot juntos
    import threading
    
    # Thread para Flask
    def run_flask():
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Bot na thread principal
    main()
