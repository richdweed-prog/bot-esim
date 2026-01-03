import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

PLANOS = {
    '11': {'valor': 25.00},
    '12': {'valor': 25.00},
    '31': {'valor': 25.00},
    '61': {'valor': 25.00},
    '75': {'valor': 25.00},
    '88': {'valor': 25.00},
}

carrinhos = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📱 Ver Planos", callback_data='planos')],
        [InlineKeyboardButton("🛒 Carrinho", callback_data='carrinho')],
        [InlineKeyboardButton("❓ Ajuda", callback_data='ajuda')],
        [InlineKeyboardButton("📞 Suporte", callback_data='suporte')]
    ]
    await update.message.reply_text("🛍️ Loja de eSIM! 66GB por R$25", reply_markup=InlineKeyboardMarkup(keyboard))

async def planos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(f"VIVO DDD {ddd} - R$25", callback_data=f'ddd_{ddd}')] for ddd in PLANOS]
    keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data='menu')])
    await query.edit_message_text("📋 Planos:", reply_markup=InlineKeyboardMarkup(keyboard))

async def detalhe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    ddd = query.data.split('_')[1]
    keyboard = [
        [InlineKeyboardButton("✅ Adicionar", callback_data=f'add_{ddd}')],
        [InlineKeyboardButton("📋 Planos", callback_data='planos')],
        [InlineKeyboardButton("🛒 Carrinho", callback_data='carrinho')],
    ]
    await query.edit_message_text(f"📱 VIVO DDD {ddd}\n66GB - R$25", reply_markup=InlineKeyboardMarkup(keyboard))

async def add_carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    ddd = query.data.split('_')[1]
    user_id = str(query.from_user.id)
    if user_id not in carrinhos: carrinhos[user_id] = []
    carrinhos[user_id].append(ddd)
    keyboard = [
        [InlineKeyboardButton(f"🛒 Carrinho ({len(carrinhos[user_id])})", callback_data='carrinho')],
        [InlineKeyboardButton("📋 Mais Planos", callback_data='planos')],
        [InlineKeyboardButton("💳 Pagar", callback_data='pagar')]
    ]
    await query.edit_message_text(f"✅ VIVO DDD {ddd} adicionado!", reply_markup=InlineKeyboardMarkup(keyboard))

async def carrinho(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    if user_id not in carrinhos or not carrinhos[user_id]:
        await query.edit_message_text("🛒 Carrinho vazio", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 Planos", callback_data='planos')]]))
        return
    itens = carrinhos[user_id]
    total = len(itens) * 25
    itens_text = "\n".join([f"• VIVO DDD {ddd} - R$25" for ddd in itens])
    keyboard = [
        [InlineKeyboardButton("💳 Pagar", callback_data='pagar')],
        [InlineKeyboardButton("🗑️ Limpar", callback_data='limpar')],
        [InlineKeyboardButton("📋 Planos", callback_data='planos')]
    ]
    await query.edit_message_text(f"🛒 Seu Carrinho:\n{itens_text}\n\nTotal: R${total}", reply_markup=InlineKeyboardMarkup(keyboard))

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("❓ Escolha DDD → Adicione → Pague → Receba QR Code", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data='menu')]]))

async def suporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.edit_message_text("📞 WhatsApp: (33) 98451-8052", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data='menu')]]))

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    items = len(carrinhos.get(user_id, []))
    keyboard = [
        [InlineKeyboardButton("📱 Ver Planos", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 Carrinho ({items})", callback_data='carrinho')],
        [InlineKeyboardButton("❓ Ajuda", callback_data='ajuda')],
        [InlineKeyboardButton("📞 Suporte", callback_data='suporte')]
    ]
    await query.edit_message_text("🛍️ Menu:", reply_markup=InlineKeyboardMarkup(keyboard))

async def limpar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    if user_id in carrinhos: carrinhos[user_id] = []
    await query.answer("Carrinho limpo!")
    await menu(update, context)

def main():
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    if not TOKEN:
        print("❌ Token não encontrado!")
        return
    
    print("🤖 Iniciando Bot...")
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(planos, pattern='^planos$'))
    app.add_handler(CallbackQueryHandler(detalhe, pattern='^ddd_'))
    app.add_handler(CallbackQueryHandler(add_carrinho, pattern='^add_'))
    app.add_handler(CallbackQueryHandler(carrinho, pattern='^carrinho$'))
    app.add_handler(CallbackQueryHandler(ajuda, pattern='^ajuda$'))
    app.add_handler(CallbackQueryHandler(suporte, pattern='^suporte$'))
    app.add_handler(CallbackQueryHandler(menu, pattern='^menu$'))
    app.add_handler(CallbackQueryHandler(limpar, pattern='^limpar$'))
    
    print("✅ Bot pronto!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
