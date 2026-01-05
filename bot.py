import os
import logging
import qrcode
import io
import random
import asyncio
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# ========== CONFIGURAÇÃO ==========
TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TOKEN:
    print("❌ ERRO: TELEGRAM_TOKEN não configurado!")
    print("⚠️ Configure a variável TELEGRAM_TOKEN no Render")
    exit(1)

print(f"✅ Token: {TOKEN[:10]}...")

# Configuração PIX
PIX_CHAVE = "gaila191h@gmail.com"
PIX_NOME = "Solineia G de Souza"
PIX_CIDADE = "Belo Horizonte"

# ========== FLASK APP ==========
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "🤖 Bot eSIM VIVO Online - R$20"

@app_web.route('/health')
def health():
    return "✅ Bot está online", 200

# ========== DADOS DOS PLANOS ==========
PLANOS = {
    '31': {'nome': 'VIVO DDD 31', 'preco': 20.00, 'dados': '66GB'},
    '21': {'nome': 'VIVO DDD 21', 'preco': 20.00, 'dados': '66GB'},
    '55': {'nome': 'VIVO DDD 55', 'preco': 20.00, 'dados': '66GB'},
}

# Armazenamento
carrinhos = {}
pedidos = {}

# ========== FUNÇÕES ==========
def gerar_qr_pix(valor, pedido_id):
    """Gera QR Code PIX"""
    texto_qr = f"PIX:{PIX_CHAVE}:{valor:.2f}:{pedido_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(texto_qr)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def gerar_esim_qr(ddd, pedido_id):
    """Gera QR Code eSIM"""
    iccid = f"895923{random.randint(100000000000, 999999999999)}"
    esim_data = f"LPA:1$esim.vivo.com.br$IMSI310260{iccid}"
    
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(esim_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def gerar_pedido_id():
    return f"ESIM{random.randint(1000, 9999)}"

# ========== HANDLERS DO BOT ==========
def start(update: Update, context: CallbackContext):
    """Comando /start"""
    user = update.effective_user
    user_id = str(user.id)
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    qtd = len(carrinhos[user_id])
    
    keyboard = [
        [InlineKeyboardButton("📱 VER PLANOS VIVO", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 CARRINHO ({qtd})", callback_data='carrinho')],
        [InlineKeyboardButton("❓ AJUDA", callback_data='ajuda')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')]
    ]
    
    update.message.reply_text(
        f"👋 Olá *{user.first_name}*!\n\n"
        "🛍️ *LOJA E-SIM VIVO*\n"
        "💰 *Valor:* R$20,00\n"
        "💾 *Dados:* 66GB\n"
        "📍 *DDDs:* 31, 21, 55\n"
        "⚡ *Ativação:* Imediata\n\n"
        "Escolha uma opção:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def mostrar_planos(update: Update, context: CallbackContext):
    """Mostra planos"""
    query = update.callback_query
    query.answer()
    
    keyboard = []
    for ddd in ['31', '21', '55']:
        plano = PLANOS[ddd]
        keyboard.append([
            InlineKeyboardButton(
                f"📱 {plano['nome']} - R${plano['preco']:.2f}",
                callback_data=f'ver_{ddd}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')])
    
    query.edit_message_text(
        "📋 *PLANOS DISPONÍVEIS:*\n\n"
        "1. VIVO DDD 31 - R$20,00\n"
        "2. VIVO DDD 21 - R$20,00\n"
        "3. VIVO DDD 55 - R$20,00\n\n"
        "Todos com 66GB de internet.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def ver_plano(update: Update, context: CallbackContext):
    """Detalhes do plano"""
    query = update.callback_query
    query.answer()
    
    ddd = query.data.split('_')[1]
    plano = PLANOS[ddd]
    
    keyboard = [
        [InlineKeyboardButton("✅ ADICIONAR AO CARRINHO", callback_data=f'add_{ddd}')],
        [InlineKeyboardButton("📋 VER PLANOS", callback_data='planos')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    query.edit_message_text(
        f"📱 *{plano['nome']}*\n\n"
        f"💾 *Dados:* {plano['dados']}\n"
        f"💰 *Valor:* R${plano['preco']:.2f}\n"
        f"⏰ *Validade:* 30 dias",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def adicionar_carrinho(update: Update, context: CallbackContext):
    """Adiciona ao carrinho"""
    query = update.callback_query
    query.answer()
    
    ddd = query.data.split('_')[1]
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    carrinhos[user_id].append(ddd)
    qtd = len(carrinhos[user_id])
    
    keyboard = [
        [InlineKeyboardButton(f"🛒 VER CARRINHO ({qtd})", callback_data='carrinho')],
        [InlineKeyboardButton("➕ ADICIONAR MAIS", callback_data='planos')],
        [InlineKeyboardButton("💰 PAGAR", callback_data='pagar')]
    ]
    
    query.edit_message_text(
        f"✅ *{PLANOS[ddd]['nome']}* adicionado!\n\n"
        f"*Itens no carrinho:* {qtd}\n"
        f"*Total:* R${qtd * 20:.2f}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def ver_carrinho(update: Update, context: CallbackContext):
    """Mostra carrinho"""
    query = update.callback_query
    query.answer()
    
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        keyboard = [[InlineKeyboardButton("📱 VER PLANOS", callback_data='planos')]]
        query.edit_message_text(
            "🛒 *Carrinho vazio*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    itens = carrinhos[user_id]
    total = len(itens) * 20.00
    texto = "\n".join([f"• {PLANOS[ddd]['nome']}" for ddd in itens])
    
    keyboard = [
        [InlineKeyboardButton(f"💰 PAGAR R${total:.2f}", callback_data='pagar')],
        [InlineKeyboardButton("🗑️ LIMPAR", callback_data='limpar')],
        [InlineKeyboardButton("📱 CONTINUAR COMPRANDO", callback_data='planos')]
    ]
    
    query.edit_message_text(
        f"🛒 *Seu Carrinho:*\n\n{texto}\n\n"
        f"💰 *Total:* R${total:.2f}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def pagar(update: Update, context: CallbackContext):
    """Processa pagamento"""
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
        'itens': carrinhos[user_id].copy(),
        'total': total,
        'pago': False,
        'data': datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    
    # Gerar QR Code PIX
    qr_img = gerar_qr_pix(total, pedido_id)
    
    # Enviar QR Code
    context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=qr_img,
        caption=f"💰 *PIX*\n\nPedido: #{pedido_id}\nValor: R${total:.2f}"
    )
    
    # Enviar instruções
    keyboard = [
        [InlineKeyboardButton("✅ JÁ PAGUEI", callback_data=f'pago_{pedido_id}')],
        [InlineKeyboardButton("🆘 AJUDA", callback_data='ajuda_pagamento')]
    ]
    
    context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"📋 *INSTRUÇÕES:*\n\n"
             f"1. Abra seu banco\n"
             f"2. PIX para: {PIX_CHAVE}\n"
             f"3. Valor: R${total:.2f}\n"
             f"4. Após pagar, clique em JÁ PAGUEI",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    query.edit_message_text(
        f"✅ *Pedido criado:* #{pedido_id}\n"
        f"💰 *Valor:* R${total:.2f}",
        parse_mode='Markdown'
    )

def confirmar_pagamento(update: Update, context: CallbackContext):
    """Confirma pagamento"""
    query = update.callback_query
    query.answer()
    
    pedido_id = query.data.split('_')[1]
    
    if pedido_id not in pedidos:
        query.answer("Pedido não encontrado!", show_alert=True)
        return
    
    pedido = pedidos[pedido_id]
    
    if pedido['pago']:
        query.answer("Este pedido já foi pago!", show_alert=True)
        return
    
    # Marcar como pago
    pedido['pago'] = True
    pedido['data_pagamento'] = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Limpar carrinho
    user_id = pedido['user_id']
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    # Gerar eSIMs
    for ddd in pedido['itens']:
        qr_esim = gerar_esim_qr(ddd, pedido_id)
        
        context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=qr_esim,
            caption=f"🎉 *E-SIM ENTREGUE!*\n\nPedido: #{pedido_id}\nPlano: {PLANOS[ddd]['nome']}"
        )
    
    keyboard = [
        [InlineKeyboardButton("📱 COMPRAR MAIS", callback_data='planos')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')]
    ]
    
    query.edit_message_text(
        f"✅ *Pagamento confirmado!*\n\n"
        f"*Pedido:* #{pedido_id}\n"
        f"*Status:* ✅ Entregue\n"
        f"*Data:* {pedido['data_pagamento']}\n\n"
        f"Seus QR Codes foram enviados acima.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def ajuda(update: Update, context: CallbackContext):
    """Menu de ajuda"""
    query = update.callback_query
    query.answer()
    
    texto = "❓ *AJUDA*\n\n"
    texto += "*Como comprar:*\n"
    texto += "1. Escolha DDD\n"
    texto += "2. Adicione ao carrinho\n"
    texto += "3. Pague com PIX\n"
    texto += "4. Receba QR Code\n\n"
    texto += "*Valor:* R$20 por chip\n"
    texto += "*Dados:* 66GB\n"
    texto += "*DDDs:* 31, 21, 55"
    
    keyboard = [
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    query.edit_message_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def suporte(update: Update, context: CallbackContext):
    """Menu de suporte"""
    query = update.callback_query
    query.answer()
    
    texto = "🆘 *SUPORTE*\n\n"
    texto += "*WhatsApp:* 33 98451-8052\n"
    texto += "*Telegram:* @Drwed33\n"
    texto += "*Email:* gaila191h@gmail.com\n\n"
    texto += "*Horário:* 8h às 20h"
    
    keyboard = [
        [
            InlineKeyboardButton("📱 WHATSAPP", url='https://wa.me/5533984518052'),
            InlineKeyboardButton("🤖 TELEGRAM", url='https://t.me/Drwed33')
        ],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    query.edit_message_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def menu(update: Update, context: CallbackContext):
    """Volta ao menu"""
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
        "🛍️ *Menu Principal*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def limpar(update: Update, context: CallbackContext):
    """Limpa carrinho"""
    query = update.callback_query
    query.answer()
    
    user_id = str(query.from_user.id)
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    query.answer("Carrinho limpo!", show_alert=True)
    ver_carrinho(update, context)

def ajuda_pagamento(update: Update, context: CallbackContext):
    """Ajuda com pagamento"""
    query = update.callback_query
    query.answer()
    
    query.edit_message_text(
        "💰 *AJUDA PIX*\n\n"
        "*Chave:* gaila191h@gmail.com\n"
        "*Nome:* Solineia Guimaraes\n\n"
        "*Problemas?*\n"
        "WhatsApp: 33 98451-8052",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 WHATSAPP", url='https://wa.me/5533984518052')],
            [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
        ]),
        parse_mode='Markdown'
    )

# ========== MAIN ==========
def main():
    """Função principal"""
    print("=" * 50)
    print("🤖 BOT E-SIM VIVO")
    print(f"💰 Valor: R$20,00")
    print(f"📍 DDDs: 31, 21, 55")
    print(f"💾 Dados: 66GB")
    print("=" * 50)
    
    # Criar updater
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Adicionar handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("suporte", suporte))
    
    # Callback handlers
    dp.add_handler(CallbackQueryHandler(mostrar_planos, pattern='^planos$'))
    dp.add_handler(CallbackQueryHandler(ver_plano, pattern='^ver_'))
    dp.add_handler(CallbackQueryHandler(adicionar_carrinho, pattern='^add_'))
    dp.add_handler(CallbackQueryHandler(ver_carrinho, pattern='^carrinho$'))
    dp.add_handler(CallbackQueryHandler(pagar, pattern='^pagar$'))
    dp.add_handler(CallbackQueryHandler(confirmar_pagamento, pattern='^pago_'))
    dp.add_handler(CallbackQueryHandler(ajuda, pattern='^ajuda$'))
    dp.add_handler(CallbackQueryHandler(suporte, pattern='^suporte$'))
    dp.add_handler(CallbackQueryHandler(menu, pattern='^menu$'))
    dp.add_handler(CallbackQueryHandler(limpar, pattern='^limpar$'))
    dp.add_handler(CallbackQueryHandler(ajuda_pagamento, pattern='^ajuda_pagamento$'))
    
    print("✅ Bot configurado")
    print("🚀 Iniciando bot...")
    
    # Iniciar bot
    updater.start_polling()
    updater.idle()

def run_flask():
    """Roda Flask"""
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Iniciando servidor web na porta {port}")
    app_web.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Configurar logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Iniciar bot (no Render, Flask é iniciado pelo gunicorn)
    main()
