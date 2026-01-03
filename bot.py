import os
import logging
import qrcode
import io
import random
import string
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

@app_web.route('/health')
def health():
    return "✅ OK"

def run_web():
    app_web.run(host='0.0.0.0', port=5000)

# ========== DADOS DOS PLANOS ==========
PLANOS = {
    '11': {'nome': 'VIVO DDD 11', 'preco': 25.00, 'dados': '66GB'},
    '12': {'nome': 'VIVO DDD 12', 'preco': 25.00, 'dados': '66GB'},
    '31': {'nome': 'VIVO DDD 31', 'preco': 25.00, 'dados': '66GB'},
    '61': {'nome': 'VIVO DDD 61', 'preco': 25.00, 'dados': '66GB'},
    '75': {'nome': 'VIVO DDD 75', 'preco': 25.00, 'dados': '66GB'},
    '88': {'nome': 'VIVO DDD 88', 'preco': 25.00, 'dados': '66GB'},
}

carrinhos = {}
pedidos = {}

# ========== FUNÇÕES PIX ==========
def gerar_codigo_pix(valor, pedido_id):
    """Gera código PIX que pode copiar e colar"""
    codigo = f"""PIX PARA PAGAMENTO:
    
NOME: {PIX_NOME}
CHAVE PIX: {PIX_CHAVE}
VALOR: R$ {valor:.2f}
PEDIDO: {pedido_id}
CIDADE: {PIX_CIDADE}

INSTRUÇÕES:
1. Abra seu app do banco
2. Vá em PIX > Pagar
3. Cole esta chave: {PIX_CHAVE}
4. Digite o valor: R$ {valor:.2f}
5. Confirme o pagamento

⚠️ Após pagar, clique em "JÁ PAGUEI" no bot."""
    
    return codigo

def gerar_qr_pix(valor, pedido_id):
    """Gera QR Code do PIX"""
    texto_qr = f"PIX:{PIX_CHAVE}:{valor:.2f}:{pedido_id}:{PIX_NOME}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(texto_qr)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

def gerar_pedido_id():
    """Gera ID único para pedido"""
    return f"ESIM{random.randint(10000, 99999)}"

# ========== FUNÇÕES DO BOT ==========
async def start(update: Update, context):
    user_id = str(update.effective_user.id)
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    keyboard = [
        [InlineKeyboardButton("📱 VER PLANOS", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 CARRINHO ({len(carrinhos[user_id])})", callback_data='carrinho')],
        [InlineKeyboardButton("❓ COMO FUNCIONA", callback_data='instrucoes')],
        [InlineKeyboardButton("🆘 SUPORTE TÉCNICO", callback_data='suporte')]
    ]
    
    await update.message.reply_text(
        "🛍️ *LOJA DE E-SIM VIVO*\n\n"
        "📱 *66GB de internet*\n"
        "💰 *R$25,00 por plano*\n"
        "⚡ *Ativação em 2 minutos*\n\n"
        "*Escolha uma opção abaixo:*",
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
        "📋 *PLANOS DISPONÍVEIS:*\n\n"
        "Escolha o DDD desejado:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def ver_plano(update: Update, context):
    query = update.callback_query
    ddd = query.data.split('_')[1]
    
    keyboard = [
        [InlineKeyboardButton("✅ ADICIONAR AO CARRINHO", callback_data=f'add_{ddd}')],
        [InlineKeyboardButton("📋 VER OUTROS PLANOS", callback_data='planos')]
    ]
    
    await query.edit_message_text(
        f"📱 *{PLANOS[ddd]['nome']}*\n\n"
        f"• Dados: {PLANOS[ddd]['dados']}\n"
        f"• Chamadas: Ilimitadas\n"
        f"• WhatsApp: Ilimitado\n"
        f"• Validade: 30 dias\n"
        f"• Valor: R$ {PLANOS[ddd]['preco']:.2f}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def adicionar_carrinho(update: Update, context):
    query = update.callback_query
    ddd = query.data.split('_')[1]
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    # Adicionar como dicionário para guardar mais informações
    carrinhos[user_id].append({
        'ddd': ddd,
        'nome': PLANOS[ddd]['nome'],
        'preco': PLANOS[ddd]['preco']
    })
    
    keyboard = [
        [InlineKeyboardButton(f"🛒 VER CARRINHO ({len(carrinhos[user_id])})", callback_data='carrinho')],
        [InlineKeyboardButton("📋 CONTINUAR COMPRANDO", callback_data='planos')]
    ]
    
    await query.edit_message_text(
        f"✅ *{PLANOS[ddd]['nome']}*\n"
        f"Adicionado ao carrinho!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def ver_carrinho(update: Update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        await query.edit_message_text(
            "🛒 *CARRINHO VAZIO*\n\n"
            "Adicione algum plano primeiro.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 VER PLANOS", callback_data='planos')]]),
            parse_mode='Markdown'
        )
        return
    
    itens = carrinhos[user_id]
    total = sum(item['preco'] for item in itens)
    texto = "\n".join([f"• {item['nome']} - R${item['preco']:.2f}" for item in itens])
    
    keyboard = [
        [InlineKeyboardButton("💰 PAGAR COM PIX", callback_data='finalizar')],
        [InlineKeyboardButton("🗑️ LIMPAR CARRINHO", callback_data='limpar')]
    ]
    
    await query.edit_message_text(
        f"🛒 *SEU CARRINHO:*\n\n{texto}\n\n"
        f"💰 *TOTAL: R$ {total:.2f}*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def finalizar_compra(update: Update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        await query.answer("❌ Carrinho vazio!", show_alert=True)
        return
    
    # Verificar se há itens no carrinho
    if not carrinhos[user_id]:
        await query.answer("❌ Carrinho vazio!", show_alert=True)
        return
    
    pedido_id = gerar_pedido_id()
    itens = carrinhos[user_id].copy()
    total = sum(item['preco'] for item in itens)
    
    # SALVAR PEDIDO CORRETAMENTE
    pedidos[pedido_id] = {
        'user_id': user_id,
        'itens': itens,  # Agora salva a lista completa
        'total': total,
        'pago': False,
        'data': datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    
    print(f"✅ Pedido salvo: {pedido_id}, Itens: {len(itens)}, Total: {total}")
    
    keyboard = [
        [InlineKeyboardButton("💰 GERAR PIX", callback_data=f'pagar_{pedido_id}')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='carrinho')]
    ]
    
    await query.edit_message_text(
        f"💰 *FINALIZAR COMPRA*\n\n"
        f"📦 Pedido: #{pedido_id}\n"
        f"💰 Valor: R$ {total:.2f}\n\n"
        f"Clique em 'GERAR PIX' para receber o QR Code e código PIX.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def pagar_pix(update: Update, context):
    query = update.callback_query
    data = query.data
    print(f"DEBUG: pagar_pix chamado com data: {data}")
    
    if '_' not in data:
        await query.answer("❌ Erro no pedido!", show_alert=True)
        return
    
    pedido_id = query.data.split('_')[1]
    print(f"DEBUG: Pedido ID extraído: {pedido_id}")
    
    if pedido_id not in pedidos:
        print(f"DEBUG: Pedido {pedido_id} não encontrado em pedidos")
        print(f"DEBUG: Pedidos existentes: {list(pedidos.keys())}")
        await query.answer("❌ Pedido não encontrado!", show_alert=True)
        return
    
    pedido = pedidos[pedido_id]
    total = pedido['total']
    print(f"DEBUG: Pedido encontrado: {pedido_id}, Total: {total}")
    
    try:
        # Gerar QR Code
        qr_img = gerar_qr_pix(total, pedido_id)
        codigo_pix = gerar_codigo_pix(total, pedido_id)
        
        # Enviar QR Code
        await query.message.reply_photo(
            photo=qr_img,
            caption=f"💰 *PAGAMENTO PIX*\n\n"
                   f"📦 Pedido: #{pedido_id}\n"
                   f"💰 Valor: R$ {total:.2f}\n\n"
                   f"*Como pagar:*\n"
                   f"1. Abra seu app do banco\n"
                   f"2. Escaneie o QR Code\n"
                   f"3. OU use o código abaixo",
            parse_mode='Markdown'
        )
        
        # Enviar código PIX (pode copiar)
        await query.message.reply_text(
            f"📋 *CÓDIGO PIX (Copie e Cole):*\n\n"
            f"```\n{codigo_pix}\n```\n\n"
            f"*Após pagar, clique no botão abaixo:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ JÁ PAGUEI", callback_data=f'pago_{pedido_id}')]])
        )
        
        await query.edit_message_text(
            f"✅ *PIX GERADO!*\n\n"
            f"📦 Pedido: #{pedido_id}\n"
            f"💰 Valor: R$ {total:.2f}\n\n"
            f"Verifique suas mensagens para o QR Code.",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"ERRO ao gerar PIX: {e}")
        await query.answer(f"❌ Erro: {str(e)}", show_alert=True)

async def confirmar_pagamento(update: Update, context):
    query = update.callback_query
    pedido_id = query.data.split('_')[1]
    
    if pedido_id not in pedidos:
        await query.answer("❌ Pedido não encontrado!", show_alert=True)
        return
    
    pedido = pedidos[pedido_id]
    pedido['pago'] = True
    pedido['data_pagamento'] = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Limpar carrinho
    user_id = pedido['user_id']
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    # Gerar QR Code do eSIM
    qr_esim = qrcode.QRCode()
    qr_esim.add_data(f"eSIM:VIVO:{pedido_id}:ATIVAR:{user_id}")
    img_esim = qr_esim.make_image()
    img_bytes = io.BytesIO()
    img_esim.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Enviar eSIM
    await query.message.reply_photo(
        photo=img_bytes,
        caption=f"🎉 *PAGAMENTO CONFIRMADO!*\n\n"
               f"📦 Pedido: #{pedido_id}\n"
               f"✅ Status: Pago ✓\n\n"
               f"📱 *SEU E-SIM ESTÁ PRONTO!*\n\n"
               f"*Como ativar:*\n"
               f"1. Configurações > Celular\n"
               f"2. 'Adicionar Plano'\n"
               f"3. Escanear QR Code acima\n"
               f"4. Ativar linha\n\n"
               f"⚡ Internet ativa em 2 minutos!",
        parse_mode='Markdown'
    )
    
    await query.edit_message_text(
        f"✅ *PAGAMENTO CONFIRMADO!*\n\n"
        f"📦 Pedido: #{pedido_id}\n"
        f"💰 Valor: R$ {pedido['total']:.2f}\n\n"
        f"📱 O QR Code do seu eSIM foi enviado!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ COMPRAR MAIS", callback_data='planos')]]),
        parse_mode='Markdown'
    )

async def instrucoes_ativacao(update: Update, context):
    """INSTRUÇÕES para conectar o chip"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("🆘 PRECISO DE SUPORTE", callback_data='suporte')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    await query.edit_message_text(
        "❓ *COMO ATIVAR SEU E-SIM:*\n\n"
        
        "*📱 PARA iPHONE:*\n"
        "1. Vá em Ajustes > Celular\n"
        "2. Toque em 'Adicionar Plano Celular'\n"
        "3. Escaneie o QR Code recebido\n"
        "4. Toque em 'Continuar'\n"
        "5. Ative a linha\n\n"
        
        "*📱 PARA ANDROID:*\n"
        "1. Vá em Configurações > Rede e Internet\n"
        "2. Toque em 'eSIM'\n"
        "3. Escolha 'Adicionar eSIM'\n"
        "4. Escaneie o QR Code recebido\n"
        "5. Ative o plano\n\n"
        
        "*⏳ TEMPO DE ATIVAÇÃO:*\n"
        "• Normal: 2 a 5 minutos\n"
        "• Máximo: 15 minutos\n\n"
        
        "*⚠️ PROBLEMAS COMUNS:*\n"
        "• QR Code não escaneia: Aumente o brilho\n"
        "• 'eSIM não suportado': Seu celular não tem eSIM\n"
        "• Sem sinal: Aguarde 10 minutos\n\n"
        
        "_Se ainda tiver problemas, clique em 'Preciso de Suporte'_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def suporte_tecnico(update: Update, context):
    """SUPORTE para resolver problemas técnicos"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("📞 WHATSAPP", url='https://wa.me/5533984518052')],
        [InlineKeyboardButton("📱 TELEGRAM", url='https://t.me/Drwed33')],
        [InlineKeyboardButton("📧 EMAIL", url='mailto:richdweed@gmail.com')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu')]
    ]
    
    await query.edit_message_text(
        "🆘 *SUPORTE TÉCNICO*\n\n"
        
        "*📞 CONTATOS OFICIAIS:*\n"
        "• WhatsApp: 33 98451-8052\n"
        "• Telegram: @Drwed33\n"
        "• Email: richdweed@gmail.com\n\n"
        
        "*👤 RESPONSÁVEL TÉCNICO:*\n"
        "• Nome: Weed do nar\n"
        "• Telegram: @Drwed33\n\n"
        
        "*🕐 HORÁRIO DE ATENDIMENTO:*\n"
        "• Segunda a Sexta: 8h às 20h\n"
        "• Sábado: 9h às 18h\n"
        "• Domingo: 10h às 16h\n\n"
        
        "*⏱️ TEMPO DE RESPOSTA:*\n"
        "• WhatsApp/Telegram: 5-10 minutos\n"
        "• Email: 2-4 horas\n\n"
        
        "*🔧 PROBLEMAS QUE RESOLVEMOS:*\n"
        "• QR Code não funciona\n"
        "• eSIM não ativa\n"
        "• Sem conexão de internet\n"
        "• Dúvidas sobre pagamento\n"
        "• Problemas técnicos\n\n"
        
        "_Entre em contato pelo botão acima_",
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
        [InlineKeyboardButton("❓ COMO FUNCIONA", callback_data='instrucoes')],
        [InlineKeyboardButton("🆘 SUPORTE TÉCNICO", callback_data='suporte')]
    ]
    
    await query.edit_message_text(
        "🛍️ *MENU PRINCIPAL:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def limpar_carrinho(update: Update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    await query.answer("✅ Carrinho limpo!", show_alert=True)
    await menu(update, context)

# ========== MAIN ==========
def main():
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    if not TOKEN:
        print("❌ ERRO: Configure TELEGRAM_TOKEN no Render!")
        return
    
    # Iniciar servidor web
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    print("🌐 Servidor web iniciado")
    
    # Iniciar bot
    print("🤖 Iniciando bot com PIX automático...")
    print(f"💰 PIX Configurado para: {PIX_NOME}")
    
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(mostrar_planos, pattern='^planos$'))
    app.add_handler(CallbackQueryHandler(ver_plano, pattern='^ver_'))
    app.add_handler(CallbackQueryHandler(adicionar_carrinho, pattern='^add_'))
    app.add_handler(CallbackQueryHandler(ver_carrinho, pattern='^carrinho$'))
    app.add_handler(CallbackQueryHandler(finalizar_compra, pattern='^finalizar$'))
    app.add_handler(CallbackQueryHandler(pagar_pix, pattern='^pagar_'))
    app.add_handler(CallbackQueryHandler(confirmar_pagamento, pattern='^pago_'))
    app.add_handler(CallbackQueryHandler(instrucoes_ativacao, pattern='^instrucoes$'))
    app.add_handler(CallbackQueryHandler(suporte_tecnico, pattern='^suporte$'))
    app.add_handler(CallbackQueryHandler(menu, pattern='^menu$'))
    app.add_handler(CallbackQueryHandler(limpar_carrinho, pattern='^limpar$'))
    
    print("✅ Bot PIX automático pronto!")
    print("🚀 Sistema funcionando...")
    
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
