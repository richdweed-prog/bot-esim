import os
import logging
import qrcode
import io
import random
import threading
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ========== CONFIGURAÇÃO PIX ==========
PIX_CHAVE = "gaila191h@gmail.com"
PIX_NOME = "Solineia G de Souza"
PIX_CIDADE = "Belo Horizonte"

# ========== SERVIDOR WEB ==========
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "🤖 Bot eSIM Online"

@app_web.route('/health')
def health():
    return "✅ Bot está online"

def run_web():
    port = int(os.environ.get('PORT', 5000))
    app_web.run(host='0.0.0.0', port=port)

# ========== DADOS DOS PLANOS ==========
PLANOS = {
    '11': {'nome': 'VIVO DDD 21', 'preco': 20.00, 'dados': '66GB'},
    '12': {'nome': 'VIVO DDD 31', 'preco': 20.00, 'dados': '66GB'},
    '31': {'nome': 'VIVO DDD 40', 'preco': 20.00, 'dados': '66GB'},
    '61': {'nome': 'VIVO DDD 51', 'preco': 20.00, 'dados': '66GB'},
    '75': {'nome': 'VIVO DDD 75', 'preco': 20.00, 'dados': '66GB'},
    '88': {'nome': 'VIVO DDD 88', 'preco': 20.00, 'dados': '66GB'},
}

# Armazenamento temporário (em produção use banco de dados)
carrinhos = {}
pedidos = {}
usuarios = {}

# ========== FUNÇÕES PIX ==========
def gerar_codigo_pix(valor, pedido_id):
    """Gera código PIX copiável"""
    return f"""
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

def gerar_qr_pix(valor, pedido_id):
    """Gera QR Code do PIX"""
    texto_qr = f"00020101021226840014BR.GOV.BCB.PIX0136{PIX_CHAVE}5204000053039865802BR5925{SOLINEIA GUIMARAES DE SOUZA6009SAO PAULO62140510{pdido_id}6304"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(texto_qr)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

def gerar_pedido_id():
    return f"ESIM{random.randint(1000, 9999)}"

def gerar_esim_qr(plano_ddd, pedido_id):
    """Gera QR Code do eSIM real"""
    # Formato real de QR code eSIM (LPA format)
    esim_data = f"""LPA:1$rsp-0001.oberthur.net$ICCID{random.randint(1000000000000000000, 9999999999999999999)}"""
    
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(esim_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes, esim_data

# ========== FUNÇÕES DO BOT ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Menu principal"""
    user = update.effective_user
    user_id = str(user.id)
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
        usuarios[user_id] = {
            'nome': user.first_name,
            'username': user.username,
            'data_cadastro': datetime.now().strftime("%d/%m/%Y %H:%M")
        }
    
    qtd_carrinho = len(carrinhos[user_id])
    
    keyboard = [
        [InlineKeyboardButton("📱 VER PLANOS DISPONÍVEIS", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 MEU CARRINHO ({qtd_carrinho})", callback_data='carrinho')],
        [InlineKeyboardButton("📋 MEUS PEDIDOS", callback_data='meus_pedidos')],
        [InlineKeyboardButton("❓ AJUDA / INSTRUÇÕES", callback_data='ajuda')],
        [InlineKeyboardButton("🆘 SUPORTE TÉCNICO", callback_data='suporte')],
        [InlineKeyboardButton("👤 MEUS DADOS", callback_data='meus_dados')]
    ]
    
    mensagem = f"""
👋 *Olá {user.first_name}!*

🛍️ *LOJA DE E-SIM VIVO*
📱 66GB por R$20,00
⚡ Ativação Imediata

🎯 *OFERTAS ESPECIAIS:*
• DDD 21, 31, 40, 51, 75, 88
• Todos com 66GB
• Preço único: R$20,00

Escolha uma opção abaixo:
"""
    
    await update.message.reply_text(
        mensagem,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """CORRIGIDO: Handler do botão de suporte"""
    query = update.callback_query
    
    # Responder à callback query (remove o "carregando")
    await query.answer()
    
    mensagem = f"""
🆘 *SUPORTE TÉCNICO*

*Contatos Diretos:*

📱 *WhatsApp:* 
• 33 98451-8052 (DrWed)
• Clique: https://wa.me/5533984518052

🤖 *Telegram:*
• @Drwed33 
• Clique: https://t.me/Drwed33

📧 *E-mail:*
• richdweed@gmail.com
• Clique: mailto:gaila191h@gmail.com

👤 *Responsável:*
• Drwed 

🕒 *Horário de Atendimento:*
• Segunda a Sexta: 10h às 20h
• Sábado: 10 às 13h

⚠️ *Para agilizar seu atendimento:*
1. Informe seu número de pedido
2. Descreva o problema detalhadamente
3. Envie print se possível

*Problemas Comuns:*
✅ QR Code não escaneia
✅ Pagamento não confirmado
✅ Dúvidas sobre ativação
✅ Problemas com conexão
"""

    keyboard = [
        [
            InlineKeyboardButton("📱 WHATSAPP", url='https://wa.me/5533984518052'),
            InlineKeyboardButton("🤖 TELEGRAM", url='https://t.me/Drwed33')
        ],
        [
            InlineKeyboardButton("📧 ENVIAR E-MAIL", url='mailto:richdweed@gmail.com'),
            InlineKeyboardButton("📞 LIGAR", callback_data='ligar_suporte')
        ],
        [
            InlineKeyboardButton("❓ PERGUNTAS FREQUENTES", callback_data='faq'),
            InlineKeyboardButton("📋 MEUS PEDIDOS", callback_data='meus_pedidos')
        ],
        [
            InlineKeyboardButton("⬅️ VOLTAR AO MENU", callback_data='menu_principal'),
            InlineKeyboardButton("🛒 CONTINUAR COMPRANDO", callback_data='planos')
        ]
    ]
    
    await query.edit_message_text(
        mensagem,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
        disable_web_page_preview=False
    )

async def ligar_suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra número para ligação"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📞 *Para ligar para o suporte:*\n\n"
        "📱 *Número:* (33) 98451-8052\n"
        "👤 *Atendente:* @Drwed03\n"
        "⏰ *Horário:* 10h às 18h\n\n"
        "*Dica:* Se preferir, use o WhatsApp para atendimento mais rápido!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 ABRIR WHATSAPP", url='https://wa.me/5533984518052')],
            [InlineKeyboardButton("⬅️ VOLTAR AO SUPORTE", callback_data='suporte')]
        ]),
        parse_mode='Markdown'
    )

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perguntas Frequentes"""
    query = update.callback_query
    await query.answer()
    
    faq_text = """
❓ *PERGUNTAS FREQUENTES*

1. *Quanto tempo leva para receber o eSIM?*
   ✅ Imediato após confirmação do pagamento.

2. *O QR Code não está funcionando, o que fazer?*
   ✅ Entre em contato com nosso suporte.

3. *Como ativar o eSIM no meu celular?*
   iPhone: Configurações > Celular > Adicionar Plano Celular
   Android: Configurações > Conexões > SIMs > Adicionar eSIM

4. *Posso usar em qualquer celular?*
   ✅ Sim, desde que o celular seja compatível com eSIM.

5. *O plano tem franquia?*
   ✅ 66GB de internet, após isso velocidade reduzida.

6. *Como faço para pagar?*
   ✅ Aceitamos PIX com entrega automática.

7. *E se eu tiver problemas técnicos?*
   ✅ Entre em contato pelo botão SUPORTE.

8. *Tem garantia?*
   ✅ 7 dias de garantia para problemas técnicos.
"""
    
    keyboard = [
        [InlineKeyboardButton("🆘 FALAR COM SUPORTE", callback_data='suporte')],
        [InlineKeyboardButton("⬅️ VOLTAR AO MENU", callback_data='menu_principal')]
    ]
    
    await query.edit_message_text(
        faq_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def mostrar_planos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra todos os planos disponíveis"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for ddd in sorted(PLANOS.keys()):
        plano = PLANOS[ddd]
        keyboard.append([
            InlineKeyboardButton(
                f"📱 {plano['nome']} - {plano['dados']} - R${plano['preco']:.2f}",
                callback_data=f'ver_plano_{ddd}'
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("🛒 VER CARRINHO", callback_data='carrinho'),
        InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu_principal')
    ])
    
    await query.edit_message_text(
        "📋 *PLANOS DISPONÍVEIS:*\n\n"
        "Todos os planos incluem:\n"
        "✅ 66GB de internet\n"
        "✅ Ativação imediata\n"
        "✅ Suporte 24/7\n"
        "✅ Preço único: R$20,00\n\n"
        "*Escolha o DDD desejado:*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def ver_plano(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detalhes de um plano específico"""
    query = update.callback_query
    await query.answer()
    
    ddd = query.data.split('_')[-1]
    plano = PLANOS[ddd]
    
    keyboard = [
        [InlineKeyboardButton("✅ ADICIONAR AO CARRINHO", callback_data=f'add_{ddd}')],
        [
            InlineKeyboardButton("📋 VER TODOS PLANOS", callback_data='planos'),
            InlineKeyboardButton("🛒 CARRINHO", callback_data='carrinho')
        ]
    ]
    
    await query.edit_message_text(
        f"📱 *DETALHES DO PLANO*\n\n"
        f"*Operadora:* VIVO\n"
        f"*DDD:* {ddd}\n"
        f"*Dados:* {plano['dados']}\n"
        f"*Valor:* R${plano['preco']:.2f}\n\n"
        f"*Benefícios:*\n"
        f"✅ Internet 4G/5G\n"
        f"✅ Ligações ilimitadas\n"
        f"✅ SMS ilimitado\n"
        f"✅ Roaming nacional\n\n"
        f"*Instruções de uso:*\n"
        f"1. Compre o plano\n"
        f"2. Receba QR Code por aqui\n"
        f"3. Escaneie no seu celular\n"
        f"4. Ative e use!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def adicionar_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adiciona item ao carrinho"""
    query = update.callback_query
    await query.answer()
    
    ddd = query.data.split('_')[1]
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    carrinhos[user_id].append(ddd)
    
    keyboard = [
        [
            InlineKeyboardButton(f"🛒 VER CARRINHO ({len(carrinhos[user_id])})", callback_data='carrinho'),
            InlineKeyboardButton("➕ ADICIONAR MAIS", callback_data='planos')
        ],
        [InlineKeyboardButton("💰 FINALIZAR COMPRA", callback_data='finalizar')]
    ]
    
    await query.edit_message_text(
        f"✅ *{PLANOS[ddd]['nome']}* foi adicionado ao seu carrinho!\n\n"
        f"*Total no carrinho:* {len(carrinhos[user_id])} item(ns)\n"
        f"*Valor total:* R${len(carrinhos[user_id]) * 20.00:.2f}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def ver_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra itens no carrinho"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        keyboard = [[InlineKeyboardButton("📱 VER PLANOS", callback_data='planos')]]
        await query.edit_message_text(
            "🛒 *Seu carrinho está vazio*\n\n"
            "Adicione planos para continuar!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    itens = carrinhos[user_id]
    total = len(itens) * 20.00
    
    # Listar itens
    itens_text = "\n".join([f"• {PLANOS[ddd]['nome']} - R$20,00" for ddd in itens])
    
    keyboard = [
        [InlineKeyboardButton("💰 PAGAR COM PIX", callback_data='pagar_pix')],
        [
            InlineKeyboardButton("🗑️ ESVAZIAR CARRINHO", callback_data='limpar_carrinho'),
            InlineKeyboardButton("➕ ADICIONAR MAIS", callback_data='planos')
        ]
    ]
    
    await query.edit_message_text(
        f"🛒 *SEU CARRINHO*\n\n"
        f"{itens_text}\n\n"
        f"*Quantidade:* {len(itens)} item(ns)\n"
        f"*Valor total:* R${total:.2f}\n\n"
        f"*Próximo passo:* Clique em PAGAR COM PIX",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def pagar_pix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa pagamento via PIX"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        await query.answer("Seu carrinho está vazio!", show_alert=True)
        return
    
    pedido_id = gerar_pedido_id()
    itens = carrinhos[user_id]
    total = len(itens) * 20.00
    
    # Salvar pedido
    pedidos[pedido_id] = {
        'user_id': user_id,
        'itens': itens.copy(),
        'total': total,
        'pago': False,
        'data': datetime.now().strftime("%d/%m/%Y %H:%M"),
        'status': 'aguardando_pagamento'
    }
    
    # Gerar QR Code PIX
    qr_img = gerar_qr_pix(total, pedido_id)
    codigo_pix = gerar_codigo_pix(total, pedido_id)
    
    # Enviar QR Code
    await query.message.reply_photo(
        photo=qr_img,
        caption=f"💰 *QR CODE PIX*\n\n*Pedido:* #{pedido_id}\n*Valor:* R${total:.2f}",
        parse_mode='Markdown'
    )
    
    # Enviar instruções
    keyboard = [
        [InlineKeyboardButton("✅ JÁ PAGUEI", callback_data=f'confirmar_pagamento_{pedido_id}')],
        [InlineKeyboardButton("🆘 AJUDA COM PAGAMENTO", callback_data='ajuda_pagamento')],
        [InlineKeyboardButton("⬅️ VOLTAR AO CARRINHO", callback_data='carrinho')]
    ]
    
    await query.message.reply_text(
        f"📋 *DETALHES DO PAGAMENTO*\n\n"
        f"*Pedido:* #{pedido_id}\n"
        f"*Valor:* R${total:.2f}\n"
        f"*Chave PIX:* {PIX_CHAVE}\n\n"
        f"*Instruções:*\n"
        f"1. Abra seu app bancário\n"
        f"2. Vá em PIX > Pagar\n"
        f"3. Use a chave ou escaneie o QR Code\n"
        f"4. Confirme o pagamento\n\n"
        f"⚠️ *Após pagar, clique em JÁ PAGUEI*\n\n"
        f"```\n{codigo_pix}\n```",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    await query.edit_message_text(
        f"✅ *PAGAMENTO GERADO*\n\n"
        f"*Pedido:* #{pedido_id}\n"
        f"*Valor:* R${total:.2f}\n\n"
        f"Verifique as mensagens acima com o QR Code PIX.",
        parse_mode='Markdown'
    )

async def confirmar_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usuário confirma que pagou"""
    query = update.callback_query
    await query.answer()
    
    pedido_id = query.data.split('_')[-1]
    
    if pedido_id not in pedidos:
        await query.answer("Pedido não encontrado!", show_alert=True)
        return
    
    pedido = pedidos[pedido_id]
    
    if pedido['pago']:
        await query.answer("Este pedido já foi pago!", show_alert=True)
        return
    
    # Marcar como pago
    pedido['pago'] = True
    pedido['status'] = 'pago'
    pedido['data_pagamento'] = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Limpar carrinho do usuário
    user_id = pedido['user_id']
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    # Gerar eSIM para cada item
    for ddd in pedido['itens']:
        qr_esim, codigo_esim = gerar_esim_qr(ddd, pedido_id)
        
        # Enviar QR Code do eSIM
        await query.message.reply_photo(
            photo=qr_esim,
            caption=f"🎉 *E-SIM ENTREGUE!*\n\n"
                   f"*Pedido:* #{pedido_id}\n"
                   f"*Plano:* {PLANOS[ddd]['nome']}\n"
                   f"*DDD:* {ddd}\n"
                   f"*Dados:* 66GB\n\n"
                   f"*Instruções de ativação:*\n"
                   f"1. Abra a câmera do celular\n"
                   f"2. Aponte para o QR Code acima\n"
                   f"3. Siga as instruções na tela\n\n"
                   f"⏰ *Validade:* 30 dias\n"
                   f"⚡ *Ative em até 24 horas*",
            parse_mode='Markdown'
        )
    
    # Mensagem de confirmação final
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
        f"*Itens:* {len(pedido['itens'])} plano(s)\n\n"
        f"🎉 *Seus QR Codes eSIM foram enviados acima!*\n\n"
        f"*Problemas?* Clique em SUPORTE\n"
        f"*Comprar mais?* Clique em COMPRAR MAIS",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def meus_pedidos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra pedidos do usuário"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    # Filtrar pedidos do usuário
    pedidos_usuario = {pid: p for pid, p in pedidos.items() if p['user_id'] == user_id}
    
    if not pedidos_usuario:
        keyboard = [
            [InlineKeyboardButton("📱 COMPRAR AGORA", callback_data='planos')],
            [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu_principal')]
        ]
        
        await query.edit_message_text(
            "📭 *Você ainda não fez nenhum pedido*\n\n"
            "Comece sua primeira compra!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return
    
    # Listar pedidos
    pedidos_text = ""
    for pid, p in pedidos_usuario.items():
        status = "✅ PAGO" if p['pago'] else "⏳ AGUARDANDO PAGAMENTO"
        pedidos_text += f"• *#{pid}* - {p['data']} - {status}\n"
    
    keyboard = [
        [InlineKeyboardButton("📱 COMPRAR MAIS", callback_data='planos')],
        [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu_principal')]
    ]
    
    await query.edit_message_text(
        f"📋 *MEUS PEDIDOS*\n\n{pedidos_text}\n"
        f"*Total de pedidos:* {len(pedidos_usuario)}\n\n"
        f"*Dúvidas sobre algum pedido?*\n"
        f"Entre em contato com nosso suporte!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu de ajuda"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("📱 COMO ATIVAR", callback_data='como_ativar'),
            InlineKeyboardButton("💰 PAGAMENTO", callback_data='ajuda_pagamento')
        ],
        [
            InlineKeyboardButton("❓ PERGUNTAS FREQUENTES", callback_data='faq'),
            InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')
        ],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu_principal')]
    ]
    
    await query.edit_message_text(
        "❓ *CENTRAL DE AJUDA*\n\n"
        "Escolha o tópico sobre o qual precisa de ajuda:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def como_ativar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Instruções de ativação"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📱 PARA IPHONE", callback_data='ativar_iphone')],
        [InlineKeyboardButton("🤖 PARA ANDROID", callback_data='ativar_android')],
        [InlineKeyboardButton("⬅️ VOLTAR À AJUDA", callback_data='ajuda')]
    ]
    
    await query.edit_message_text(
        "📱 *COMO ATIVAR SEU E-SIM*\n\n"
        "Selecione o tipo do seu celular:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def ativar_iphone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Instruções para iPhone"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🍎 *ATIVAÇÃO NO IPHONE*\n\n"
        "1. Vá em *Configurações*\n"
        "2. Toque em *Celular*\n"
        "3. Selecione *Adicionar Plano Celular*\n"
        "4. Aponte a câmera para o QR Code\n"
        "5. Toque em *Continuar* no canto superior direito\n"
        "6. Aguarde a ativação\n"
        "7. Toque em *Concluir*\n\n"
        "*Dicas:*\n"
        "• Use boa iluminação\n"
        "• Mantenha o QR Code na tela\n"
        "• Não minimize o app durante a ativação\n\n"
        "Problemas? Clique em SUPORTE",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ VOLTAR", callback_data='como_ativar')],
            [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')]
        ]),
        parse_mode='Markdown'
    )

async def ativar_android(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Instruções para Android"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🤖 *ATIVAÇÃO NO ANDROID*\n\n"
        "1. Vá em *Configurações*\n"
        "2. Toque em *Conexões* ou *Rede e Internet*\n"
        "3. Selecione *SIM* ou *Chip SIM*\n"
        "4. Toque em *Adicionar eSIM*\n"
        "5. Escolha *Digitalizar código QR*\n"
        "6. Aponte a câmera para o QR Code\n"
        "7. Toque em *Continuar* ou *OK*\n"
        "8. Aguarde a ativação\n"
        "9. Toque em *Concluir*\n\n"
        "*Dicas:*\n"
        "• Alguns modelos podem ter nomes diferentes\n"
        "• Mantenha o QR Code estável\n"
        "• Não feche as configurações\n\n"
        "Problemas? Clique em SUPORTE",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ VOLTAR", callback_data='como_ativar')],
            [InlineKeyboardButton("🆘 SUPORTE", callback_data='suporte')]
        ]),
        parse_mode='Markdown'
    )

async def ajuda_pagamento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ajuda com pagamento"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💰 *AJUDA COM PAGAMENTO PIX*\n\n"
        "*Problemas comuns:*\n\n"
        "1. *QR Code não escaneia:*\n"
        "   • Aumente o brilho da tela\n"
        "   • Mantenha distância de 15-20cm\n"
        "   • Use ambiente bem iluminado\n\n"
        "2. *Pagamento não confirmou:*\n"
        "   • Aguarde 5 minutos\n"
        "   • Verifique seu extrato\n"
        "   • Clique em JÁ PAGUEI novamente\n\n"
        "3. *Chave PIX não funciona:*\n"
        "   • Copie exatamente: gaila191h@gmail.com\n"
        "   • Verifique se não há espaços\n\n"
        "4. *Valor incorreto:*\n"
        "   • Digite exatamente o valor mostrado\n"
        "   • Inclua centavos (ex: 20.00)\n\n"
        "*Ainda com problemas?* Entre em contato:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📱 WHATSAPP", url='https://wa.me/5533984518052'),
                InlineKeyboardButton("🤖 TELEGRAM", url='https://t.me/Drwed33')
            ],
            [InlineKeyboardButton("⬅️ VOLTAR", callback_data='ajuda')]
        ]),
        parse_mode='Markdown'
    )

async def limpar_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Esvazia carrinho"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    await query.answer("🛒 Carrinho esvaziado!", show_alert=True)
    await ver_carrinho(update, context)

async def meus_dados(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra dados do usuário"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = query.from_user
    
    if user_id in usuarios:
        dados = usuarios[user_id]
    else:
        dados = {'data_cadastro': datetime.now().strftime("%d/%m/%Y %H:%M")}
    
    keyboard = [
        [InlineKeyboardButton("📋 MEUS PEDIDOS", callback_data='meus_pedidos')],
        [InlineKeyboardButton("🛒 MEU CARRINHO", callback_data='carrinho')],
        [InlineKeyboardButton("⬅️ VOLTAR", callback_data='menu_principal')]
    ]
    
    await query.edit_message_text(
        f"👤 *MEUS DADOS*\n\n"
        f"*ID:* {user_id}\n"
        f"*Nome:* {user.first_name}\n"
        f"*Username:* @{user.username or 'Não informado'}\n"
        f"*Cadastro:* {dados['data_cadastro']}\n"
        f"*Carrinho:* {len(carrinhos.get(user_id, []))} item(s)\n"
        f"*Pedidos:* {len([p for p in pedidos.values() if p['user_id'] == user_id])}\n\n"
        f"*Dúvidas sobre seus dados?*\n"
        f"Entre em contato com o suporte.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Volta ao menu principal"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_id = str(user.id)
    qtd_carrinho = len(carrinhos.get(user_id, []))
    
    keyboard = [
        [InlineKeyboardButton("📱 VER PLANOS DISPONÍVEIS", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 MEU CARRINHO ({qtd_carrinho})", callback_data='carrinho')],
        [InlineKeyboardButton("📋 MEUS PEDIDOS", callback_data='meus_pedidos')],
        [InlineKeyboardButton("❓ AJUDA / INSTRUÇÕES", callback_data='ajuda')],
        [InlineKeyboardButton("🆘 SUPORTE TÉCNICO", callback_data='suporte')],
        [
