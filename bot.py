import os
import logging
import qrcode
import io
import random
import asyncio
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== CONFIGURAÇÃO ==========
TOKEN = os.getenv('TELEGRAM_TOKEN')
if not TOKEN:
    print("❌ ERRO: TELEGRAM_TOKEN não configurado!")
    exit(1)

# Configuração PIX
PIX_CHAVE = "gaila191h@gmail.com"
PIX_NOME = "Solineia G de Souza"
PIX_CIDADE = "Belo Horizonte"

# ========== FLASK APP ==========
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "🤖 Bot eSIM Online"

@app_web.route('/health')
def health():
    return "✅ Bot está online", 200

# ========== DADOS DOS PLANOS (ATUALIZADO) ==========
PLANOS = {
    '31': {'nome': 'VIVO DDD 31', 'preco': 20.00, 'dados': '66GB'},
    '21': {'nome': 'VIVO DDD 21', 'preco': 20.00, 'dados': '66GB'},
    '55': {'nome': 'VIVO DDD 55', 'preco': 20.00, 'dados': '66GB'},
    # Adicione mais DDDs se necessário
}

carrinhos = {}
pedidos = {}

# ========== FUNÇÕES ==========
def gerar_qr_pix(valor, pedido_id):
    """Gera QR Code PIX"""
    texto_qr = f"PIX:{PIX_CHAVE}:{valor}:{pedido_id}"
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
    esim_data = f"LPA:1$rsp-server.com$IMSI310260{iccid}"
    
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
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    qtd = len(carrinhos[user_id])
    
    keyboard = [
        [InlineKeyboardButton("📱 VER PLANOS", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 CARRINHO ({qtd})", callback_data='carrinho')],
        [InlineKeyboardButton("❓ AJUDA", callback_data='ajuda')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')]
    ]
    
    await update.message.reply_text(
        "🛍️ *LOJA E-SIM VIVO*\n\n"
        "📱 66GB por R$20\n"
        "⚡ Ativação em 2min\n"
        "✅ DDDs: 31, 21, 55\n\n"
        "Escolha uma opção:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def mostrar_planos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for ddd in ['31', '21', '55']:  # Ordem específica
        if ddd in PLANOS:
            plano = PLANOS[ddd]
            keyboard.append([InlineKeyboardButton(
                f"📱 {plano['nome']} - {plano['dados']} - R${plano['preco']:.2f}",
                callback_data=f'ver_{ddd}'
            )])
    
    keyboard.append([InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')])
    
    await query.edit_message_text(
        "📋 *PLANOS DISPONÍVEIS:*\n\n"
        "1️⃣ *VIVO DDD 31* - 66GB - R$20,00\n"
        "2️⃣ *VIVO DDD 21* - 66GB - R$20,00\n"
        "3️⃣ *VIVO DDD 55* - 66GB - R$20,00\n\n"
        "*Escolha o DDD desejado:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def ver_plano(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    ddd = query.data.split('_')[1]
    plano = PLANOS[ddd]
    
    keyboard = [
        [InlineKeyboardButton("✅ ADICIONAR AO CARRINHO", callback_data=f'add_{ddd}')],
        [InlineKeyboardButton("📋 VER TODOS OS PLANOS", callback_data='planos')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    await query.edit_message_text(
        f"📱 *{plano['nome']}*\n\n"
        f"💾 *Dados:* {plano['dados']}\n"
        f"💰 *Valor:* R${plano['preco']:.2f}\n"
        f"📶 *Operadora:* VIVO\n\n"
        f"*Benefícios:*\n"
        f"✅ Internet 4G/5G\n"
        f"✅ Ligações ilimitadas\n"
        f"✅ Validade: 30 dias\n"
        f"✅ Ativação imediata\n\n"
        f"*Instruções:*\n"
        f"1. Adicione ao carrinho\n"
        f"2. Pague com PIX\n"
        f"3. Receba QR Code\n"
        f"4. Ative em 2 minutos",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def adicionar_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    ddd = query.data.split('_')[1]
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    carrinhos[user_id].append(ddd)
    qtd = len(carrinhos[user_id])
    
    keyboard = [
        [InlineKeyboardButton(f"🛒 VER CARRINHO ({qtd})", callback_data='carrinho')],
        [InlineKeyboardButton("➕ ADICIONAR MAIS PLANOS", callback_data='planos')],
        [InlineKeyboardButton("💰 FINALIZAR COMPRA (R${})".format(qtd * 20), callback_data='finalizar')]
    ]
    
    await query.edit_message_text(
        f"✅ *{PLANOS[ddd]['nome']}* adicionado ao carrinho!\n\n"
        f"*Itens no carrinho:* {qtd}\n"
        f"*Total parcial:* R${qtd * 20:.2f}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def ver_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        keyboard = [[InlineKeyboardButton("📱 VER PLANOS", callback_data='planos')]]
        await query.edit_message_text(
            "🛒 *Carrinho vazio*\n\n"
            "Adicione planos para começar!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    itens = carrinhos[user_id]
    total = len(itens) * 20.00
    texto = "\n".join([f"• {PLANOS[ddd]['nome']} - R$20,00" for ddd in itens])
    
    keyboard = [
        [InlineKeyboardButton("💰 PAGAR COM PIX (R${})".format(total), callback_data='pagar')],
        [InlineKeyboardButton("🗑️ LIMPAR CARRINHO", callback_data='limpar')],
        [InlineKeyboardButton("📱 CONTINUAR COMPRANDO", callback_data='planos')]
    ]
    
    await query.edit_message_text(
        f"🛒 *Seu Carrinho:*\n\n{texto}\n\n"
        f"*Quantidade:* {len(itens)} item(s)\n"
        f"💰 *Total:* R${total:.2f}\n\n"
        f"*Próximo passo:* Clique em PAGAR COM PIX",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def pagar_pix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        await query.answer("Seu carrinho está vazio!", show_alert=True)
        return
    
    pedido_id = gerar_pedido_id()
    total = len(carrinhos[user_id]) * 20.00  # R$20 por item
    
    # Salvar pedido
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
    await query.message.reply_photo(
        photo=qr_img,
        caption=f"💰 *QR CODE PIX*\n\n*Pedido:* #{pedido_id}\n*Valor:* R${total:.2f}",
        parse_mode='Markdown'
    )
    
    # Enviar instruções
    keyboard = [
        [InlineKeyboardButton("✅ JÁ PAGUEI", callback_data=f'pago_{pedido_id}')],
        [InlineKeyboardButton("🆘 AJUDA COM PAGAMENTO", callback_data='ajuda_pagamento')],
        [InlineKeyboardButton("⬅️ VOLTAR AO CARRINHO", callback_data='carrinho')]
    ]
    
    await query.message.reply_text(
        f"📋 *DETALHES DO PAGAMENTO*\n\n"
        f"*Pedido:* #{pedido_id}\n"
        f"*Valor:* R${total:.2f}\n"
        f"*Chave PIX:* {PIX_CHAVE}\n"
        f"*Nome:* {PIX_NOME}\n"
        f"*Cidade:* {PIX_CIDADE}\n\n"
        f"*Instruções:*\n"
        f"1. Abra seu app bancário\n"
        f"2. Vá em PIX > Pagar\n"
        f"3. Cole a chave: {PIX_CHAVE}\n"
        f"4. Digite: R${total:.2f}\n"
        f"5. Confirme o pagamento\n\n"
        f"⚠️ *Após pagar, clique em JÁ PAGUEI*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    await query.edit_message_text(
        f"✅ *PAGAMENTO GERADO*\n\n"
        f"*Pedido:* #{pedido_id}\n"
        f"*Valor:* R${total:.2f}\n\n"
        f"Verifique as mensagens acima com o QR Code e instruções.",
        parse_mode='Markdown'
    )

async def confirmar_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    pedido_id = query.data.split('_')[1]
    
    if pedido_id not in pedidos:
        await query.answer("Pedido não encontrado!", show_alert=True)
        return
    
    pedido = pedidos[pedido_id]
    
    if pedido['pago']:
        await query.answer("Este pedido já foi pago e entregue!", show_alert=True)
        return
    
    # Marcar como pago
    pedido['pago'] = True
    pedido['data_pagamento'] = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Limpar carrinho
    user_id = pedido['user_id']
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    # Gerar e enviar eSIMs
    for ddd in pedido['itens']:
        qr_esim = gerar_esim_qr(ddd, pedido_id)
        
        await query.message.reply_photo(
            photo=qr_esim,
            caption=f"🎉 *E-SIM ENTREGUE!*\n\n"
                   f"*Pedido:* #{pedido_id}\n"
                   f"*Plano:* {PLANOS[ddd]['nome']}\n"
                   f"*Dados:* 66GB\n"
                   f"*Valor:* R$20,00\n\n"
                   f"*Instruções de ativação:*\n"
                   f"1. Abra a câmera do celular\n"
                   f"2. Aponte para o QR Code\n"
                   f"3. Siga as instruções na tela\n\n"
                   f"⏰ *Validade:* 30 dias\n"
                   f"⚡ *Ative em até 24 horas*",
            parse_mode='Markdown'
        )
    
    # Confirmação final
    keyboard = [
        [InlineKeyboardButton("📱 COMPRAR MAIS", callback_data='planos')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')],
        [InlineKeyboardButton("📋 MEUS PEDIDOS", callback_data='meus_pedidos')]
    ]
    
    await query.edit_message_text(
        f"✅ *PAGAMENTO CONFIRMADO!*\n\n"
        f"*Pedido:* #{pedido_id}\n"
        f"*Status:* ✅ Pago e entregue\n"
        f"*Data:* {pedido['data_pagamento']}\n"
        f"*Itens:* {len(pedido['itens'])} plano(s)\n"
        f"*Total pago:* R${pedido['total']:.2f}\n\n"
        f"🎉 *Seus QR Codes eSIM foram enviados acima!*\n\n"
        f"*Problemas?* Clique em SUPORTE",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# ========== SUPORTE FUNCIONAL ==========
async def suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """BOTÃO DE SUPORTE FUNCIONAL"""
    query = update.callback_query
    await query.answer()
    
    texto = "🆘 *SUPORTE TÉCNICO:*\n\n"
    texto += "*WhatsApp:* 33 98451-8052\n"
    texto += "*Telegram:* @Drwed33\n"
    texto += "*Email:* gaila191h@gmail.com\n\n"
    texto += "*Responsável:* Solineia Guimaraes\n"
    texto += "*Horário:* 8h às 20h\n\n"
    texto += "_Clique nos botões abaixo para contato direto_"
    
    keyboard = [
        [InlineKeyboardButton("📞 WHATSAPP", url='https://wa.me/5533984518052')],
        [InlineKeyboardButton("📱 TELEGRAM", url='https://t.me/Drwed33')],
        [InlineKeyboardButton("📧 EMAIL", url='mailto:gaila191h@gmail.com')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    await query.edit_message_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    texto = "❓ *AJUDA / INSTRUÇÕES:*\n\n"
    texto += "*VALOR:* R$20 por chip\n"
    texto += "*DDDs:* 31, 21, 55\n"
    texto += "*DADOS:* 66GB cada\n"
    texto += "*VALIDADE:* 30 dias\n\n"
    texto += "*COMO ATIVAR:*\n"
    texto += "1. Compre o chip\n"
    texto += "2. Receba QR Code\n"
    texto += "3. Escaneie com a câmera\n"
    texto += "4. Ative em 2 minutos\n\n"
    texto += "*iPhone:* Configurações > Celular\n"
    texto += "*Android:* Configurações > Conexões"
    
    keyboard = [
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    await query.edit_message_text(
        texto,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "🛍️ *Menu Principal*\n\n"
        "📱 *Planos VIVO:* R$20,00\n"
        "💾 *Dados:* 66GB cada\n"
        "📍 *DDDs:* 31, 21, 55\n\n"
        "Escolha uma opção:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def limpar_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    await query.answer("🛒 Carrinho limpo!", show_alert=True)
    await ver_carrinho(update, context)

async def meus_pedidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # Filtrar pedidos do usuário
    pedidos_usuario = {pid: p for pid, p in pedidos.items() if p['user_id'] == user_id}
    
    if not pedidos_usuario:
        keyboard = [[InlineKeyboardButton("📱 COMPRAR AGORA", callback_data='planos')]]
        await query.edit_message_text(
            "📭 *Você ainda não fez nenhum pedido*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    texto = "📋 *MEUS PEDIDOS:*\n\n"
    for pid, p in pedidos_usuario.items():
        status = "✅ PAGO" if p['pago'] else "⏳ AGUARDANDO"
        texto += f"• *#{pid}* - {p['data']} - R${p['total']:.2f} - {status}\n"
    
    keyboard = [
        [InlineKeyboardButton("📱 COMPRAR MAIS", callback_data='planos')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    await query.edit_message_text(
        f"{texto}\n*Total de pedidos:* {len(pedidos_usuario)}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def ajuda_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💰 *AJUDA COM PAGAMENTO PIX*\n\n"
        "*Problemas comuns:*\n\n"
        "1. *QR Code não escaneia:*\n"
        "   • Aumente o brilho da tela\n"
        "   • Mantenha distância de 15-20cm\n\n"
        "2. *Pagamento não confirmou:*\n"
        "   • Aguarde 5 minutos\n"
        "   • Verifique seu extrato\n\n"
        "3. *Chave PIX:* gaila191h@gmail.com\n\n"
        "*Ainda com problemas?*",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 WHATSAPP", url='https://wa.me/5533984518052')],
            [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
        ]),
        parse_mode='Markdown'
    )

async def finalizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        await query.answer("Seu carrinho está vazio!", show_alert=True)
        return
    
    await pagar_pix(update, context)

# ========== CONFIGURAÇÃO DO BOT ==========
def setup_handlers(application):
    """Configura todos os handlers"""
    
    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("suporte", suporte))
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(mostrar_planos, pattern='^planos$'))
    application.add_handler(CallbackQueryHandler(ver_plano, pattern='^ver_'))
    application.add_handler(CallbackQueryHandler(adicionar_carrinho, pattern='^add_'))
    application.add_handler(CallbackQueryHandler(ver_carrinho, pattern='^carrinho$'))
    application.add_handler(CallbackQueryHandler(pagar_pix, pattern='^pagar$'))
    application.add_handler(CallbackQueryHandler(finalizar, pattern='^finalizar$'))
    application.add_handler(CallbackQueryHandler(confirmar_pagamento, pattern='^pago_'))
    application.add_handler(CallbackQueryHandler(ajuda, pattern='^ajuda$'))
    application.add_handler(CallbackQueryHandler(suporte, pattern='^suporte$'))
    application.add_handler(CallbackQueryHandler(menu, pattern='^menu$'))
    application.add_handler(CallbackQueryHandler(limpar_carrinho, pattern='^limpar$'))
    application.add_handler(CallbackQueryHandler(meus_pedidos, pattern='^meus_pedidos$'))
    application.add_handler(CallbackQueryHandler(ajuda_pagamento, pattern='^ajuda_pagamento$'))

# ========== INICIAR BOT ==========
async def main():
    """Função principal para iniciar o bot"""
    print("🤖 Iniciando Bot eSIM VIVO...")
    print(f"💰 Valor: R$20,00")
    print(f"📍 DDDs: 31, 21, 55")
    print(f"💾 Dados: 66GB cada")
    
    # Criar application
    application = Application.builder().token(TOKEN).build()
    
    # Configurar handlers
    setup_handlers(application)
    
    print("✅ Bot configurado com sucesso!")
    
    # Iniciar polling
    await application.run_polling(drop_pending_updates=True)

def run_bot():
    """Função para rodar o bot"""
    asyncio.run(main())

if __name__ == '__main__':
    # Configurar logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    print("🚀 Iniciando bot...")
    run_bot()

