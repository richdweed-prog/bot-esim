import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== CONFIGURAÇÃO ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ========== DADOS DOS PLANOS ==========
PLANOS = ['11', '12', '31', '61', '75', '88']
carrinhos = {}

# ========== FUNÇÕES DO BOT ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Inicia o bot"""
    user_id = str(update.effective_user.id)
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    keyboard = [
        [InlineKeyboardButton("📱 Ver Planos", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 Carrinho ({len(carrinhos[user_id])})", callback_data='carrinho')],
        [InlineKeyboardButton("❓ Ajuda", callback_data='ajuda')],
        [InlineKeyboardButton("📞 Suporte", callback_data='suporte')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🛍️ *Bem-vindo à Loja de eSIM!*\n\n"
        "📱 Chip digital VIVO\n"
        "💾 66GB de internet\n"
        "💰 R$25,00\n"
        "⚡ Ativação imediata!\n\n"
        "Escolha uma opção abaixo:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def ver_planos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra todos os planos disponíveis"""
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for ddd in PLANOS:
        keyboard.append([
            InlineKeyboardButton(
                f"📱 VIVO DDD {ddd} - 66GB - R$25,00",
                callback_data=f'plano_{ddd}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data='menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📋 *Planos Disponíveis:*\n\n"
        "Escolha o DDD desejado:\n\n"
        "Todos os planos incluem:\n"
        "• 66GB de internet\n"
        "• Chamadas ilimitadas\n"
        "• WhatsApp ilimitado\n"
        "• Validade: 30 dias",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def detalhes_plano(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra detalhes de um plano específico"""
    query = update.callback_query
    ddd = query.data.split('_')[1]
    
    keyboard = [
        [InlineKeyboardButton("✅ Adicionar ao Carrinho", callback_data=f'add_{ddd}')],
        [InlineKeyboardButton("📋 Ver Outros Planos", callback_data='planos')],
        [InlineKeyboardButton("🛒 Ir para Carrinho", callback_data='carrinho')],
        [InlineKeyboardButton("⬅️ Menu Principal", callback_data='menu')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📱 *DETALHES DO PLANO*\n\n"
        f"• *Operadora:* VIVO\n"
        f"• *DDD:* {ddd}\n"
        f"• *Dados:* 66GB\n"
        f"• *Chamadas:* Ilimitadas\n"
        f"• *WhatsApp:* Ilimitado\n"
        f"• *Validade:* 30 dias\n"
        f"• *Valor:* R$ 25,00\n\n"
        f"*💡 Como funciona:*\n"
        f"1. Você compra este plano\n"
        f"2. Enviamos o QR Code do eSIM\n"
        f"3. Você escaneia no seu celular\n"
        f"4. Internet pronta em 2 minutos!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def adicionar_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adiciona um plano ao carrinho"""
    query = update.callback_query
    ddd = query.data.split('_')[1]
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    carrinhos[user_id].append(ddd)
    
    total_itens = len(carrinhos[user_id])
    total_valor = total_itens * 25.00
    
    keyboard = [
        [InlineKeyboardButton(f"🛒 Ver Carrinho ({total_itens})", callback_data='carrinho')],
        [InlineKeyboardButton("📋 Continuar Comprando", callback_data='planos')],
        [InlineKeyboardButton("💳 Finalizar Compra", callback_data='finalizar')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ *PLANO ADICIONADO AO CARRINHO!*\n\n"
        f"*VIVO DDD {ddd}*\n"
        f"66GB - R$ 25,00\n\n"
        f"*Total no carrinho:* R$ {total_valor:.2f}\n"
        f"*Itens:* {total_itens}\n\n"
        f"Clique em 'Finalizar Compra' para pagar.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def ver_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra o carrinho do usuário"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        keyboard = [
            [InlineKeyboardButton("📋 Ver Planos", callback_data='planos')],
            [InlineKeyboardButton("⬅️ Menu Principal", callback_data='menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🛒 *SEU CARRINHO ESTÁ VAZIO*\n\n"
            "Você ainda não adicionou nenhum plano.\n"
            "Clique abaixo para ver nossos planos:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    itens = carrinhos[user_id]
    total_itens = len(itens)
    total_valor = total_itens * 25.00
    
    # Contar quantos de cada DDD
    contagem = {}
    for ddd in itens:
        contagem[ddd] = contagem.get(ddd, 0) + 1
    
    itens_text = "\n".join([f"• VIVO DDD {ddd} - {quantidade}x - R$ {quantidade * 25:.2f}" for ddd, quantidade in contagem.items()])
    
    keyboard = [
        [InlineKeyboardButton("💳 Finalizar Compra", callback_data='finalizar')],
        [InlineKeyboardButton("🗑️ Limpar Carrinho", callback_data='limpar')],
        [InlineKeyboardButton("➕ Adicionar Mais Planos", callback_data='planos')],
        [InlineKeyboardButton("⬅️ Menu Principal", callback_data='menu')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🛒 *SEU CARRINHO DE COMPRAS*\n\n"
        f"{itens_text}\n\n"
        f"*Total de itens:* {total_itens}\n"
        f"*Valor total:* R$ {total_valor:.2f}\n\n"
        f"_Após o pagamento, enviaremos o QR Code por aqui._",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def finalizar_compra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finaliza a compra"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        await query.answer("❌ Seu carrinho está vazio! Adicione um plano primeiro.", show_alert=True)
        return
    
    itens = carrinhos[user_id]
    total_itens = len(itens)
    total_valor = total_itens * 25.00
    
    keyboard = [
        [InlineKeyboardButton("💰 Pagar com PIX (Recomendado)", callback_data='pagar_pix')],
        [InlineKeyboardButton("💳 Pagar com Cartão", callback_data='pagar_cartao')],
        [InlineKeyboardButton("⬅️ Voltar ao Carrinho", callback_data='carrinho')],
        [InlineKeyboardButton("📋 Continuar Comprando", callback_data='planos')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💰 *FINALIZAR COMPRA*\n\n"
        f"*Resumo do pedido:*\n"
        f"• Itens: {total_itens} plano(s)\n"
        f"• Valor total: R$ {total_valor:.2f}\n\n"
        f"*Escolha a forma de pagamento:*\n\n"
        f"💰 *PIX* (Instantâneo)\n"
        f"• QR Code ou chave PIX\n"
        f"• Aprovação em segundos\n\n"
        f"💳 *Cartão de Crédito/Débito*\n"
        f"• Parcele em até 12x\n"
        f"• Pagamento seguro\n\n"
        f"_Após a confirmação do pagamento, enviaremos o QR Code do eSIM._",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra informações de ajuda"""
    query = update.callback_query
    
    keyboard = [[InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "❓ *PERGUNTAS FREQUENTES*\n\n"
        
        "*1. O que é eSIM?*\n"
        "É um chip digital que funciona igual ao físico, mas sem plástico.\n\n"
        
        "*2. Como ativo o eSIM?*\n"
        "1. Compre o plano\n"
        "2. Receba o QR Code\n"
        "3. Vá em Configurações > Celular > Adicionar Plano\n"
        "4. Escaneie o QR Code\n"
        "5. Ative a linha\n\n"
        
        "*3. Funciona no meu celular?*\n"
        "✅ iPhone XR ou superior\n"
        "✅ Samsung S20 ou superior\n"
        "✅ Google Pixel 3 ou superior\n"
        "✅ Qualquer celular com eSIM\n\n"
        
        "*4. Quando recebo o QR Code?*\n"
        "Imediatamente após a confirmação do pagamento.\n\n"
        
        "*5. Tem garantia?*\n"
        "Sim! 7 dias para arrependimento.\n\n"
        
        "_Dúvidas? Use a opção Suporte no menu._",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra informações de suporte"""
    query = update.callback_query
    
    keyboard = [[InlineKeyboardButton("⬅️ Voltar ao Menu", callback_data='menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📞 *SUPORTE E ATENDIMENTO*\n\n"
        "*Horário de atendimento:*\n"
        "• Segunda a Sexta: 8h às 20h\n"
        "• Sábado: 9h às 18h\n"
        "• Domingo: 10h às 16h\n\n"
        
        "*Canais de atendimento:*\n"
        "• WhatsApp: (11) 99999-9999\n"
        "• Email: suporte@esimloja.com.br\n"
        "• Telegram: @suporteesim\n\n"
        
        "*Tempo de resposta:*\n"
        "• WhatsApp: até 5 minutos\n"
        "• Email: até 2 horas\n\n"
        
        "_Estamos aqui para te ajudar!_",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Volta ao menu principal"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    items_count = len(carrinhos.get(user_id, []))
    
    keyboard = [
        [InlineKeyboardButton("📱 Ver Planos Disponíveis", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 Meu Carrinho ({items_count})", callback_data='carrinho')],
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
    """Limpa o carrinho"""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    await query.answer("✅ Carrinho limpo com sucesso!", show_alert=True)
    await menu_principal(update, context)

# ========== FUNÇÃO PRINCIPAL ==========
def main():
    """Função principal que inicia o bot"""
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    if not TOKEN:
        print("❌ ERRO: Token do Telegram não encontrado!")
        print("Configure a variável de ambiente TELEGRAM_TOKEN no Render")
        return
    
    print("🤖 Iniciando Bot de Venda de eSIM...")
    print(f"📱 Token: {TOKEN[:10]}...")
    
    try:
        # Criar aplicação
        application = Application.builder().token(TOKEN).build()
        
        # Registrar handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("menu", menu_principal))
        
        # Callback handlers
        application.add_handler(CallbackQueryHandler(ver_planos, pattern='^planos$'))
        application.add_handler(CallbackQueryHandler(detalhes_plano, pattern='^plano_'))
        application.add_handler(CallbackQueryHandler(adicionar_carrinho, pattern='^add_'))
        application.add_handler(CallbackQueryHandler(ver_carrinho, pattern='^carrinho$'))
        application.add_handler(CallbackQueryHandler(finalizar_compra, pattern='^finalizar$'))
        application.add_handler(CallbackQueryHandler(ajuda, pattern='^ajuda$'))
        application.add_handler(CallbackQueryHandler(suporte, pattern='^suporte$'))
        application.add_handler(CallbackQueryHandler(menu_principal, pattern='^menu$'))
        application.add_handler(CallbackQueryHandler(limpar_carrinho, pattern='^limpar$'))
        
        # Iniciar bot
        print("✅ Bot configurado com sucesso!")
        print("⚡ Iniciando polling...")
        print("📱 O bot está online! Aguardando mensagens...")
        
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            close_loop=False
        )
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")
        print("🔧 Verifique:")
        print("1. Token está correto?")
        print("2. Internet está funcionando?")
        print("3. Versão do python-telegram-bot compatível?")

if __name__ == '__main__':
    main()
