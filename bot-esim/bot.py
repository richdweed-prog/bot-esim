import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== CONFIGURAÇÃO ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ========== DADOS DOS PLANOS ==========
PLANOS = {
    '11': {'operadora': 'VIVO', 'ddd': '11', 'dados': '66GB', 'valor': 25.00},
    '12': {'operadora': 'VIVO', 'ddd': '12', 'dados': '66GB', 'valor': 25.00},
    '31': {'operadora': 'VIVO', 'ddd': '31', 'dados': '66GB', 'valor': 25.00},
    '61': {'operadora': 'VIVO', 'ddd': '61', 'dados': '66GB', 'valor': 25.00},
    '75': {'operadora': 'VIVO', 'ddd': '75', 'dados': '66GB', 'valor': 25.00},
    '88': {'operadora': 'VIVO', 'ddd': '88', 'dados': '66GB', 'valor': 25.00},
}

# ========== BANCO DE DADOS EM MEMÓRIA ==========
carrinhos = {}

# ========== FUNÇÕES DO BOT ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    # Inicializar carrinho se não existir
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    keyboard = [
        [InlineKeyboardButton("📱 Ver Planos Disponíveis", callback_data='ver_planos')],
        [InlineKeyboardButton(f"🛒 Meu Carrinho ({len(carrinhos[user_id])})", callback_data='ver_carrinho')],
        [InlineKeyboardButton("❓ Como Funciona", callback_data='ajuda')],
        [InlineKeyboardButton("📞 Suporte", callback_data='suporte')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🛍️ *Bem-vindo à Loja de eSIM!*\n\n"
        "Aqui você compra seu chip digital com internet.\n"
        "Escolha uma opção abaixo:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def ver_planos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for ddd, plano in PLANOS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"📱 VIVO DDD {ddd} - {plano['dados']} - R${plano['valor']}",
                callback_data=f'plano_{ddd}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data='voltar_inicio')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📋 *Planos Disponíveis:*\n\n"
        "Escolha o DDD desejado:\n\n"
        "TODOS COM:\n"
        "• 66GB de internet\n"
        "• Chamadas ilimitadas\n"
        "• WhatsApp ilimitado\n"
        "• Ativação imediata",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def detalhes_plano(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    ddd = query.data.split('_')[1]
    plano = PLANOS[ddd]
    
    keyboard = [
        [InlineKeyboardButton("✅ Adicionar ao Carrinho", callback_data=f'add_{ddd}')],
        [InlineKeyboardButton("📋 Ver Outros Planos", callback_data='ver_planos')],
        [InlineKeyboardButton("🛒 Ir para Carrinho", callback_data='ver_carrinho')],
        [InlineKeyboardButton("⬅️ Menu Principal", callback_data='voltar_inicio')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📱 *DETALHES DO PLANO*\n\n"
        f"• *Operadora:* {plano['operadora']}\n"
        f"• *DDD:* {plano['ddd']}\n"
        f"• *Dados:* {plano['dados']}\n"
        f"• *Chamadas:* Ilimitadas\n"
        f"• *WhatsApp:* Ilimitado\n"
        f"• *Validade:* 30 dias\n"
        f"• *Valor:* R$ {plano['valor']:.2f}\n\n"
        f"*💡 Como funciona:*\n"
        f"1. Você compra\n"
        f"2. Enviamos QR Code do eSIM\n"
        f"3. Você escaneia no celular\n"
        f"4. Internet pronta em 2 minutos!\n\n"
        f"_Compatível com iPhone e Android recentes._",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def adicionar_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    ddd = query.data.split('_')[1]
    plano = PLANOS[ddd].copy()
    user_id = str(query.from_user.id)
    
    # Adicionar ao carrinho
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    carrinhos[user_id].append(plano)
    
    total = sum(item['valor'] for item in carrinhos[user_id])
    
    keyboard = [
        [InlineKeyboardButton(f"🛒 Ver Carrinho ({len(carrinhos[user_id])})", callback_data='ver_carrinho')],
        [InlineKeyboardButton("📋 Continuar Comprando", callback_data='ver_planos')],
        [InlineKeyboardButton("💳 Finalizar Compra", callback_data='finalizar')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ *PLANO ADICIONADO!*\n\n"
        f"*{plano['operadora']} DDD {plano['ddd']}*\n"
        f"{plano['dados']} - R$ {plano['valor']:.2f}\n\n"
        f"*Total no carrinho:* R$ {total:.2f}\n"
        f"*Itens:* {len(carrinhos[user_id])}\n\n"
        f"_Clique em 'Finalizar Compra' para pagar._",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def ver_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        keyboard = [
            [InlineKeyboardButton("📋 Ver Planos", callback_data='ver_planos')],
            [InlineKeyboardButton("⬅️ Menu Principal", callback_data='voltar_inicio')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🛒 *CARRINHO VAZIO*\n\n"
            "Você ainda não adicionou nenhum plano.\n"
            "Clique abaixo para ver nossos planos:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    itens = carrinhos[user_id]
    total = sum(item['valor'] for item in itens)
    
    itens_text = "\n".join([
        f"• {item['operadora']} DDD {item['ddd']} - R$ {item['valor']:.2f}"
        for item in itens
    ])
    
    keyboard = [
        [InlineKeyboardButton("💳 Finalizar Compra", callback_data='finalizar')],
        [InlineKeyboardButton("🗑️ Limpar Carrinho", callback_data='limpar_carrinho')],
        [InlineKeyboardButton("➕ Adicionar Mais", callback_data='ver_planos')],
        [InlineKeyboardButton("⬅️ Menu Principal", callback_data='voltar_inicio')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🛒 *SEU CARRINHO*\n\n"
        f"{itens_text}\n\n"
        f"*Total: R$ {total:.2f}*\n"
        f"*Quantidade: {len(itens)} plano(s)*\n\n"
        f"_Após o pagamento, enviaremos o QR Code por aqui._",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def finalizar_compra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        await query.answer("Seu carrinho está vazio!", show_alert=True)
        return
    
    total = sum(item['valor'] for item in carrinhos[user_id])
    
    keyboard = [
        [InlineKeyboardButton("💰 Pagar com PIX", callback_data='pagar_pix')],
        [InlineKeyboardButton("💳 Pagar com Cartão", callback_data='pagar_cartao')],
        [InlineKeyboardButton("⬅️ Voltar", callback_data='ver_carrinho')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💰 *FINALIZAR COMPRA*\n\n"
        f"*Total:* R$ {total:.2f}\n\n"
        f"Escolha a forma de pagamento:\n\n"
        f"*💰 PIX* (Recomendado)\n"
        f"• Pagamento instantâneo\n"
        f"• QR Code ou chave\n\n"
        f"*💳 Cartão*\n"
        f"• Crédito ou débito\n"
        f"• Parcele em até 12x\n\n"
        f"_Pagamento 100% seguro._",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data='voltar_inicio')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "❓ *PERGUNTAS FREQUENTES*\n\n"
        
        "*1. O que é eSIM?*\n"
        "Chip digital que funciona igual físico, mas sem plástico.\n\n"
        
        "*2. Como ativo o eSIM?*\n"
        "1. Compre o plano\n"
        "2. Receba QR Code\n"
        "3. Abra configurações do celular\n"
        "4. Escaneie o QR Code\n"
        "5. Ative a linha\n\n"
        
        "*3. Funciona no meu celular?*\n"
        "✅ iPhone XR ou superior\n"
        "✅ Samsung S20 ou superior\n"
        "✅ Google Pixel 3 ou superior\n"
        "✅ Outros com eSIM\n\n"
        
        "*4. Quando recebo o QR Code?*\n"
        "Imediatamente após a confirmação do pagamento.\n\n"
        
        "*5. Posso cancelar?*\n"
        "Sim, em 7 dias por lei de arrependimento.\n\n"
        
        "_Dúvidas? Clique em Suporte no menu._",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("⬅️ Voltar", callback_data='voltar_inicio')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📞 *SUPORTE*\n\n"
        "*Horário de atendimento:*\n"
        "• Segunda a Sexta: 8h às 20h\n"
        "• Sábado: 9h às 18h\n"
        "• Domingo: 10h às 16h\n\n"
        
        "*Canais de atendimento:*\n"
        "• WhatsApp: (11) 99999-9999\n"
        "• Email: suporte@esim.com.br\n"
        "• Telegram: @suporteesim\n\n"
        
        "_Estamos aqui para te ajudar!_",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def voltar_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    items_count = len(carrinhos.get(user_id, []))
    
    keyboard = [
        [InlineKeyboardButton("📱 Ver Planos Disponíveis", callback_data='ver_planos')],
        [InlineKeyboardButton(f"🛒 Meu Carrinho ({items_count})", callback_data='ver_carrinho')],
        [InlineKeyboardButton("❓ Como Funciona", callback_data='ajuda')],
        [InlineKeyboardButton("📞 Suporte", callback_data='suporte')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🛍️ *MENU PRINCIPAL*\n\n"
        "Escolha uma opção abaixo:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def limpar_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    await query.answer("Carrinho limpo!", show_alert=True)
    await voltar_inicio(update, context)

# ========== FUNÇÃO PRINCIPAL ==========
def main():
    # COLOQUE SEU TOKEN AQUI!
    TOKEN = "8563239036:AAEtaHnxgZiKA5lVvq1d_9IN92GnGooXrc8"  # ← SUBSTITUA PELO SEU TOKEN REAL
    
    if TOKEN == "SEU_TOKEN_AQUI":
        print("❌ ERRO: Você precisa colocar seu token do Telegram!")
        print("1. Abra o Telegram e busque por @BotFather")
        print("2. Crie um bot com /newbot")
        print("3. Copie o token que ele te der")
        print("4. Cole no código onde diz 'SEU_TOKEN_AQUI'")
        return
    
    print("🤖 Iniciando Bot de eSIM...")
    
    # Criar aplicação
    application = Application.builder().token(TOKEN).build()
    
    # Registrar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", voltar_inicio))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(ver_planos, pattern='^ver_planos$'))
    application.add_handler(CallbackQueryHandler(detalhes_plano, pattern='^plano_'))
    application.add_handler(CallbackQueryHandler(adicionar_carrinho, pattern='^add_'))
    application.add_handler(CallbackQueryHandler(ver_carrinho, pattern='^ver_carrinho$'))
    application.add_handler(CallbackQueryHandler(finalizar_compra, pattern='^finalizar$'))
    application.add_handler(CallbackQueryHandler(ajuda, pattern='^ajuda$'))
    application.add_handler(CallbackQueryHandler(suporte, pattern='^suporte$'))
    application.add_handler(CallbackQueryHandler(voltar_inicio, pattern='^voltar_inicio$'))
    application.add_handler(CallbackQueryHandler(limpar_carrinho, pattern='^limpar_carrinho$'))
    
    # Iniciar bot
    print("✅ Bot pronto!")
    print("📱 Acesse o Telegram e busque pelo seu bot")
    print("⚡ Bot funcionando...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()