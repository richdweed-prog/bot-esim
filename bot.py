import os
import logging
import qrcode
import io
import random
import threading
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# ========== CONFIGURAÇÃO PIX ==========
PIX_CHAVE = "gaila191h@gmail.com"
PIX_NOME = "Solineia Guimaraes de Souza"
PIX_CIDADE = "Belo Horizonte"

# ========== SERVIDOR WEB ==========
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "🤖 Bot eSIM Online"

def run_web():
    app_web.run(host='0.0.0.0', port=5000)

# ========== DADOS DOS PLANOS ==========
PLANOS = {
    '11': {'nome': 'VIVO DDD 11', 'preco': 25.00},
    '12': {'nome': 'VIVO DDD 12', 'preco': 25.00},
    '31': {'nome': 'VIVO DDD 31', 'preco': 25.00},
    '61': {'nome': 'VIVO DDD 61', 'preco': 25.00},
    '75': {'nome': 'VIVO DDD 75', 'preco': 25.00},
    '88': {'nome': 'VIVO DDD 88', 'preco': 25.00},
}

carrinhos = {}
pedidos = {}

# ========== FUNÇÕES PIX ==========
def gerar_codigo_pix(valor, pedido_id):
    """Gera código PIX copiável"""
    codigo = f"""
    💰 *PAGAMENTO PIX*
    
    👤 Nome: {PIX_NOME}
    🔑 Chave: {PIX_CHAVE}
    💵 Valor: R$ {valor:.2f}
    📦 Pedido: {pedido_id}
    🏙️ Cidade: {PIX_CIDADE}
    
    *INSTRUÇÕES:*
    1️⃣ Abra app do banco
    2️⃣ Vá em PIX > Pagar
    3️⃣ Cole: {PIX_CHAVE}
    4️⃣ Digite: R$ {valor:.2f}
    5️⃣ Confirme pagamento
    
    ⚠️ Após pagar, clique em JÁ PAGUEI
    """
    return codigo

def gerar_qr_pix(valor, pedido_id):
    """Gera QR Code do PIX"""
    texto_qr = f"PIX:{PIX_CHAVE}:{valor}:{pedido_id}"
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

# ========== FUNÇÕES DO BOT ==========
async def start(update: Update, context):
    user_id = str(update.effective_user.id)
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    keyboard = [
        [InlineKeyboardButton("📱 VER PLANOS", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 CARRINHO ({len(carrinhos[user_id])})", callback_data='carrinho')],
        [InlineKeyboardButton("❓ AJUDA", callback_data='ajuda')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')]
    ]
    
    await update.message.reply_text(
        "🛍️ *LOJA E-SIM VIVO*\n\n"
        "📱 66GB por R$25\n"
        "⚡ Ativação em 2min\n\n"
        "Escolha uma opção:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def mostrar_planos(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for ddd in PLANOS:
        keyboard.append([InlineKeyboardButton(
            f"📱 {PLANOS[ddd]['nome']} - R${PLANOS[ddd]['preco']}",
            callback_data=f'ver_{ddd}'
        )])
    
    keyboard.append([InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')])
    
    await query.edit_message_text(
        "📋 Escolha o DDD:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def ver_plano(update: Update, context):
    query = update.callback_query
    ddd = query.data.split('_')[1]
    
    keyboard = [
        [InlineKeyboardButton("✅ ADICIONAR", callback_data=f'add_{ddd}')],
        [InlineKeyboardButton("📋 VER PLANOS", callback_data='planos')]
    ]
    
    await query.edit_message_text(
        f"📱 {PLANOS[ddd]['nome']}\n"
        f"💾 66GB internet\n"
        f"💰 R${PLANOS[ddd]['preco']:.2f}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def adicionar_carrinho(update: Update, context):
    query = update.callback_query
    ddd = query.data.split('_')[1]
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    carrinhos[user_id].append(ddd)
    
    keyboard = [
        [InlineKeyboardButton(f"🛒 CARRINHO ({len(carrinhos[user_id])})", callback_data='carrinho')],
        [InlineKeyboardButton("📋 MAIS PLANOS", callback_data='planos')]
    ]
    
    await query.edit_message_text(
        f"✅ {PLANOS[ddd]['nome']} adicionado!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def ver_carrinho(update: Update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        await query.edit_message_text(
            "🛒 Carrinho vazio",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 PLANOS", callback_data='planos')]])
        )
        return
    
    itens = carrinhos[user_id]
    total = len(itens) * 25.00
    texto = "\n".join([f"• {PLANOS[ddd]['nome']}" for ddd in itens])
    
    keyboard = [
        [InlineKeyboardButton("💰 PAGAR COM PIX", callback_data='pagar')],
        [InlineKeyboardButton("🗑️ LIMPAR", callback_data='limpar')]
    ]
    
    await query.edit_message_text(
        f"🛒 Seu Carrinho:\n{texto}\n\n💰 Total: R${total:.2f}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def pagar_pix(update: Update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        await query.answer("Carrinho vazio!", show_alert=True)
        return
    
    pedido_id = gerar_pedido_id()
    total = len(carrinhos[user_id]) * 25.00
    
    pedidos[pedido_id] = {
        'user_id': user_id,
        'itens': carrinhos[user_id].copy(),
        'total': total,
        'pago': False
    }
    
    # Gerar QR Code
    qr_img = gerar_qr_pix(total, pedido_id)
    codigo_pix = gerar_codigo_pix(total, pedido_id)
    
    # Enviar QR Code
    await query.message.reply_photo(
        photo=qr_img,
        caption=f"💰 *PIX*\n\nPedido: #{pedido_id}\nValor: R${total:.2f}"
    )
    
    # Enviar código
    await query.message.reply_text(
        f"📋 *CÓDIGO PIX:*\n\n```\n{codigo_pix}\n```\n\n"
        f"Após pagar, clique:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ JÁ PAGUEI", callback_data=f'pago_{pedido_id}')]])
    )
    
    await query.edit_message_text(
        f"✅ PIX gerado!\nPedido: #{pedido_id}\nValor: R${total:.2f}"
    )

async def confirmar_pagamento(update: Update, context):
    query = update.callback_query
    pedido_id = query.data.split('_')[1]
    
    if pedido_id not in pedidos:
        await query.answer("Pedido não encontrado!", show_alert=True)
        return
    
    pedido = pedidos[pedido_id]
    pedido['pago'] = True
    
    # Limpar carrinho
    user_id = pedido['user_id']
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    # Gerar eSIM
    qr_esim = qrcode.QRCode()
    qr_esim.add_data(f"eSIM:VIVO:{pedido_id}")
    img_esim = qr_esim.make_image()
    img_bytes = io.BytesIO()
    img_esim.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    await query.message.reply_photo(
        photo=img_bytes,
        caption=f"🎉 *E-SIM ENTREGUE!*\n\nPedido: #{pedido_id}\nAtive em 2min!"
    )
    
    await query.edit_message_text(
        f"✅ Pagamento confirmado!\nSeu eSIM foi enviado!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ COMPRAR MAIS", callback_data='planos')]])
    )

async def ajuda(update: Update, context):
    """INSTRUÇÕES para conectar o chip"""
    query = update.callback_query
    
    texto = "❓ *COMO ATIVAR SEU E-SIM:*\n\n"
    texto += "1. Escolha DDD\n"
    texto += "2. Adicione ao carrinho\n"
    texto += "3. Pague com PIX\n"
    texto += "4. Receba QR Code eSIM\n"
    texto += "5. Ative no celular\n\n"
    texto += "*Para iPhone:* Configurações > Celular > Adicionar Plano\n"
    texto += "*Para Android:* Configurações > Rede e Internet > eSIM\n\n"
    texto += "⚡ Ativação em 2 minutos"
    
    await query.edit_message_text(
        texto,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]]),
        parse_mode='Markdown'
    )

async def suporte(update: Update, context):
    """SUPORTE para resolver problemas"""
    query = update.callback_query
    
    texto = "🆘 *SUPORTE TÉCNICO:*\n\n"
    texto += "*WhatsApp:* 33 98451-8052\n"
    texto += "*Telegram:* @Drwed33\n"
    texto += "*Email:* richdweed@gmail.com\n\n"
    texto += "*Responsável:* Solineia Guimaraes\n"
    texto += "*Horário:* 8h às 20h\n\n"
    texto += "_Clique nos botões abaixo para contato direto_"
    
    keyboard = [
        [InlineKeyboardButton("📞 WHATSAPP", url='https://wa.me/5533984518052')],
        [InlineKeyboardButton("📱 TELEGRAM", url='https://t.me/Drwed33')],
        [InlineKeyboardButton("📧 EMAIL", url='mailto:richdweed@gmail.com')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    await query.edit_message_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def menu(update: Update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    qtd = len(carrinhos.get(user_id, []))
    
    keyboard = [
        [InlineKeyboardButton("📱 VER PLANOS", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 CARRINHO ({qtd})", callback_data='carrinho')],
        [InlineKeyboardButton("❓ AJUDA", callback_data='ajuda')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')]
    ]
    
    await query.edit_message_text(
        "🛍️ Menu Principal:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def limpar_carrinho(update: Update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    await query.answer("Carrinho limpo!", show_alert=True)
    await menu(update, context)

# ========== MAIN ==========
def main():
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    if not TOKEN:
        print("❌ ERRO: Configure TELEGRAM_TOKEN!")
        return
    
    # Iniciar servidor web
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    print("🌐 Servidor web iniciado")
    
    # Iniciar bot
    print("🤖 Bot iniciando...")
    
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(mostrar_planos, pattern='^planos$'))
    app.add_handler(CallbackQueryHandler(ver_plano, pattern='^ver_'))
    app.add_handler(CallbackQueryHandler(adicionar_carrinho, pattern='^add_'))
    app.add_handler(CallbackQueryHandler(ver_carrinho, pattern='^carrinho$'))
    app.add_handler(CallbackQueryHandler(pagar_pix, pattern='^pagar$'))
    app.add_handler(CallbackQueryHandler(confirmar_pagamento, pattern='^pago_'))
    app.add_handler(CallbackQueryHandler(ajuda, pattern='^ajuda$'))
    app.add_handler(CallbackQueryHandler(suporte, pattern='^suporte$'))
    app.add_handler(CallbackQueryHandler(menu, pattern='^menu$'))
    app.add_handler(CallbackQueryHandler(limpar_carrinho, pattern='^limpar$'))
    
    print("✅ Bot pronto!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
