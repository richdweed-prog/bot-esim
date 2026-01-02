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
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    keyboard = [
        [InlineKeyboardButton("📱 Ver Planos", callback_data='ver_planos')],
        [InlineKeyboardButton(f"🛒 Carrinho ({len(carrinhos[user_id])})", callback_data='ver_carrinho')],
        [InlineKeyboardButton("❓ Ajuda", callback_data='ajuda')],
        [InlineKeyboardButton("📞 Suporte", callback_data='suporte')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🛍️ *Bem-vindo à Loja de eSIM!*\n\n"
        "Compre seu chip digital com 66GB de internet.\n"
        "Ativação imediata!",
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
    
    keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data='voltar_inicio')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📋 *Planos Disponíveis:*\n\n"
        "Escolha o DDD:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def detalhes_plano(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    ddd = query.data.split('_')[1]
    plano = PLANOS[ddd]
    
    keyboard = [
        [InlineKeyboardButton("✅ Adicionar ao Carrinho", callback_data=f'add_{ddd}')],
        [InlineKeyboardButton("📋 Ver Planos", callback_data='ver_planos')],
        [InlineKeyboardButton("🛒 Carrinho", callback_data='ver_carrinho')],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"📱 *PLANO VIVO DDD {ddd}*\n\n"
        f"• Dados: {plano['dados']}\n"
        f"• Chamadas: Ilimitadas\n"
        f"• WhatsApp: Ilimitado\n"
        f"• Valor: R$ {plano['valor']:.2f}\n\n"
        f"_Ativação em 2 minutos após pagamento._",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def adicionar_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    ddd = query.data.split('_')[1]
    plano = PLANOS[ddd].copy()
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    carrinhos[user_id].append(plano)
    total = sum(item['valor'] for item in carrinhos[user_id])
    
    keyboard = [
        [InlineKeyboardButton(f"🛒 Carrinho ({len(carrinhos[user_id])})", callback_data='ver_carrinho')],
        [InlineKeyboardButton("📋 Mais Planos", callback_data='ver_planos')],
        [InlineKeyboardButton("💳 Pagar", callback_data='finalizar')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ *Adicionado!*\n\n"
        f"VIVO DDD {ddd}\n"
        f"66GB - R$ {plano['valor']:.2f}\n\n"
        f"Total: R$ {total:.2f}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def ver_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        keyboard = [[InlineKeyboardButton("📋 Ver Planos", callback_data='ver_planos')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🛒 *Carrinho vazio*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    itens = carrinhos[user_id]
    total = sum(item['valor'] for item in itens)
    itens_text = "\n".join([f"• VIVO DDD {item['ddd']} - R$ {item['valor']:.2f}" for item in itens])
    
    keyboard = [
        [InlineKeyboardButton("💳 Pagar", callback_data='finalizar')],
        [InlineKeyboardButton("🗑️ Limpar", callback_data='limpar_carrinho')],
        [InlineKeyboardButton("📋 Planos", callback_data='ver_planos')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🛒 *Seu Carrinho*\n\n{itens_text}\n\n"
        f"*Total: R$ {total:.2f}*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def finalizar_compra(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        await query.answer("Carrinho vazio!", show_alert=True)
        return
    
    total = sum(item['valor'] for item in carrinhos[user_id])
    
    keyboard = [
        [InlineKeyboardButton("💰 PIX", callback_data='pagar_pix')],
        [InlineKeyboardButton("💳 Cartão", callback_data='pagar_cartao')],
        [InlineKeyboardButton("⬅️ Voltar", callback_data='ver_carrinho')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💰 *Pagamento*\n\n"
        f"Total: R$ {total:.2f}\n\n"
        f"Escolha a forma de pagamento:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data='voltar_inicio')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "❓ *Ajuda*\n\n"
        "1. Escolha o DDD\n"
        "2. Adicione ao carrinho\n"
        "3. Faça o pagamento\n"
        "4. Receba o QR Code\n"
        "5. Ative no celular",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    keyboard = [[InlineKeyboardButton("⬅️ Voltar", callback_data='voltar_inicio')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📞 *Suporte*\n\n"
        "WhatsApp: (33) 984518052\n"
        "Email: richdweed@gmail.com",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def voltar_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    items_count = len(carrinhos.get(user_id, []))
    
    keyboard = [
        [InlineKeyboardButton("📱 Ver Planos", callback_data='ver_planos')],
        [InlineKeyboardButton(f"🛒 Carrinho ({items_count})", callback_data='ver_carrinho')],
        [InlineKeyboardButton("❓ Ajuda", callback_data='ajuda')],
        [InlineKeyboardButton("📞 Suporte", callback_data='suporte')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🛍️ *Menu Principal*",
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
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    if not TOKEN:
        print("❌ ERRO: Token não encontrado nas variáveis de ambiente!")
        print("Configure TELEGRAM_TOKEN no Render")
        return
    
    print("🤖 Iniciando Bot de eSIM...")
    
    # Criar aplicação (versão 20.x)
    application = Application.builder().token(TOKEN).build()
    
    # Registrar handlers
    application.add_handler(CommandHandler("start", start))
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
    print("✅ Bot pronto e online!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

