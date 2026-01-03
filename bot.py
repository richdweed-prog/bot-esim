import os
import logging
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

PLANOS = {
    '11': {'dados': '66GB', 'valor': 25.00},
    '12': {'dados': '66GB', 'valor': 25.00},
    '31': {'dados': '66GB', 'valor': 25.00},
    '61': {'dados': '66GB', 'valor': 25.00},
    '75': {'dados': '66GB', 'valor': 25.00},
    '88': {'dados': '66GB', 'valor': 25.00},
}

carrinhos = {}

def start(bot, update):
    user_id = update.effective_user.id
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    keyboard = [
        [InlineKeyboardButton("📱 Ver Planos", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 Carrinho ({len(carrinhos[user_id])})", callback_data='carrinho')],
        [InlineKeyboardButton("❓ Ajuda", callback_data='ajuda')],
        [InlineKeyboardButton("📞 Suporte", callback_data='suporte')]
    ]
    
    update.message.reply_text(
        "🛍️ *Bem-vindo à Loja de eSIM!*\n66GB por R$25\nAtivação imediata!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def planos(bot, update):
    query = update.callback_query
    query.answer()
    
    keyboard = []
    for ddd in PLANOS:
        keyboard.append([InlineKeyboardButton(f"VIVO DDD {ddd} - 66GB - R$25", callback_data=f'plano_{ddd}')])
    
    keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data='menu')])
    
    query.edit_message_text(
        "📋 *Planos Disponíveis:*\nEscolha o DDD:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def plano_detail(bot, update):
    query = update.callback_query
    ddd = query.data.split('_')[1]
    
    keyboard = [
        [InlineKeyboardButton("✅ Adicionar ao Carrinho", callback_data=f'add_{ddd}')],
        [InlineKeyboardButton("📋 Ver Planos", callback_data='planos')],
        [InlineKeyboardButton("🛒 Carrinho", callback_data='carrinho')],
    ]
    
    query.edit_message_text(
        f"📱 *VIVO DDD {ddd}*\n66GB - R$25,00\nChamadas ilimitadas\nWhatsApp ilimitado",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def add_carrinho(bot, update):
    query = update.callback_query
    ddd = query.data.split('_')[1]
    user_id = query.from_user.id
    
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    carrinhos[user_id].append(ddd)
    
    keyboard = [
        [InlineKeyboardButton(f"🛒 Carrinho ({len(carrinhos[user_id])})", callback_data='carrinho')],
        [InlineKeyboardButton("📋 Mais Planos", callback_data='planos')],
        [InlineKeyboardButton("💳 Pagar", callback_data='pagar')]
    ]
    
    query.edit_message_text(
        f"✅ *Adicionado!*\nVIVO DDD {ddd}\n66GB - R$25,00",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def ver_carrinho(bot, update):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        query.edit_message_text(
            "🛒 *Carrinho vazio*",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 Ver Planos", callback_data='planos')]])
        )
        return
    
    itens = carrinhos[user_id]
    total = len(itens) * 25.00
    itens_text = "\n".join([f"• VIVO DDD {ddd} - R$25,00" for ddd in itens])
    
    keyboard = [
        [InlineKeyboardButton("💳 Pagar", callback_data='pagar')],
        [InlineKeyboardButton("🗑️ Limpar", callback_data='limpar')],
        [InlineKeyboardButton("📋 Planos", callback_data='planos')]
    ]
    
    query.edit_message_text(
        f"🛒 *Seu Carrinho*\n\n{itens_text}\n\n*Total: R$ {total:.2f}*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def ajuda(bot, update):
    query = update.callback_query
    query.edit_message_text(
        "❓ *Ajuda*\n1. Escolha o DDD\n2. Adicione ao carrinho\n3. Pague\n4. Receba QR Code\n5. Ative no celular",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data='menu')]])
    )

def suporte(bot, update):
    query = update.callback_query
    query.edit_message_text(
        "📞 *Suporte*\nWhatsApp: (33) 984518052\nEmail: richdweed@gmail.com",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data='menu')]])
    )

def menu(bot, update):
    query = update.callback_query
    user_id = query.from_user.id
    items_count = len(carrinhos.get(user_id, []))
    
    keyboard = [
        [InlineKeyboardButton("📱 Ver Planos", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 Carrinho ({items_count})", callback_data='carrinho')],
        [InlineKeyboardButton("❓ Ajuda", callback_data='ajuda')],
        [InlineKeyboardButton("📞 Suporte", callback_data='suporte')]
    ]
    
    query.edit_message_text(
        "🛍️ *Menu Principal*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

def main():
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    if not TOKEN:
        print("❌ ERRO: Token não encontrado!")
        return
    
    print("🤖 Iniciando Bot de eSIM...")
    
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(planos, pattern='planos'))
    dp.add_handler(CallbackQueryHandler(plano_detail, pattern='^plano_'))
    dp.add_handler(CallbackQueryHandler(add_carrinho, pattern='^add_'))
    dp.add_handler(CallbackQueryHandler(ver_carrinho, pattern='carrinho'))
    dp.add_handler(CallbackQueryHandler(ajuda, pattern='ajuda'))
    dp.add_handler(CallbackQueryHandler(suporte, pattern='suporte'))
    dp.add_handler(CallbackQueryHandler(menu, pattern='menu'))
    
    print("✅ Bot pronto!")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
