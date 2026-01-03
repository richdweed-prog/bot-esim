import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

# ========== SERVIDOR WEB (para Render) ==========
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "🤖 Bot de eSIM está online!"

def run_web_server():
    app_web.run(host='0.0.0.0', port=5000)

# ========== CONFIGURAÇÃO BOT ==========
logging.basicConfig(level=logging.INFO)

PLANOS = {
    '11': {'nome': 'VIVO DDD 11', 'preco': 25.00},
    '12': {'nome': 'VIVO DDD 12', 'preco': 25.00},
    '31': {'nome': 'VIVO DDD 31', 'preco': 25.00},
    '61': {'nome': 'VIVO DDD 61', 'preco': 25.00},
    '75': {'nome': 'VIVO DDD 75', 'preco': 25.00},
    '88': {'nome': 'VIVO DDD 88', 'preco': 25.00},
}

carrinhos = {}

# ========== FUNÇÕES BOT ==========
async def start(update: Update, context):
    user_id = str(update.effective_user.id)
    if user_id not in carrinhos:
        carrinhos[user_id] = []
    
    keyboard = [
        [InlineKeyboardButton("📱 Ver Planos", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 Carrinho ({len(carrinhos[user_id])})", callback_data='carrinho')],
        [InlineKeyboardButton("❓ Ajuda", callback_data='ajuda')]
    ]
    
    await update.message.reply_text(
        "🛍️ *LOJA E-SIM*\n66GB VIVO por R$25\nAtivação em 2min!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def mostrar_planos(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for ddd in PLANOS:
        keyboard.append([InlineKeyboardButton(
            f"{PLANOS[ddd]['nome']} - R${PLANOS[ddd]['preco']}",
            callback_data=f'ver_{ddd}'
        )])
    keyboard.append([InlineKeyboardButton("⬅️ Voltar", callback_data='menu')])
    
    await query.edit_message_text(
        "📋 Escolha o DDD:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def ver_plano(update: Update, context):
    query = update.callback_query
    ddd = query.data.split('_')[1]
    
    keyboard = [
        [InlineKeyboardButton("✅ Adicionar", callback_data=f'add_{ddd}')],
        [InlineKeyboardButton("📋 Ver Planos", callback_data='planos')]
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
        [InlineKeyboardButton(f"🛒 Carrinho ({len(carrinhos[user_id])})", callback_data='carrinho')],
        [InlineKeyboardButton("📋 Mais Planos", callback_data='planos')]
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
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 Planos", callback_data='planos')]])
        )
        return
    
    itens = carrinhos[user_id]
    total = len(itens) * 25.00
    texto = "\n".join([f"• {PLANOS[ddd]['nome']}" for ddd in itens])
    
    keyboard = [
        [InlineKeyboardButton("💰 Pagar", callback_data='pagar')],
        [InlineKeyboardButton("🗑️ Limpar", callback_data='limpar')]
    ]
    
    await query.edit_message_text(
        f"🛒 Seu Carrinho:\n{texto}\n\n💰 Total: R${total:.2f}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def pagar(update: Update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id not in carrinhos or not carrinhos[user_id]:
        await query.answer("Carrinho vazio!", show_alert=True)
        return
    
    keyboard = [[InlineKeyboardButton("✅ Simular Pagamento", callback_data='pago_123')]]
    await query.edit_message_text(
        "💰 *PAGAMENTO*\n\n"
        "Escolha:\n"
        "• PIX\n"
        "• Cartão\n\n"
        "_Simulação ativada_",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def confirmar_pagamento(update: Update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if user_id in carrinhos:
        carrinhos[user_id] = []
    
    await query.edit_message_text(
        "✅ *PAGAMENTO CONFIRMADO!*\n\n"
        "📱 Seu eSIM foi enviado!\n"
        "⚡ Ative em 2 minutos",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ Comprar Mais", callback_data='planos')]]),
        parse_mode='Markdown'
    )

async def ajuda(update: Update, context):
    query = update.callback_query
    await query.edit_message_text(
        "❓ *AJUDA*\n\n"
        "1. Escolha DDD\n"
        "2. Adicione ao carrinho\n"
        "3. Pague\n"
        "4. Receba eSIM\n\n"
        "📞 Suporte: @suporte",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Voltar", callback_data='menu')]])
    )

async def menu(update: Update, context):
    query = update.callback_query
    user_id = str(query.from_user.id)
    qtd = len(carrinhos.get(user_id, []))
    
    keyboard = [
        [InlineKeyboardButton("📱 Ver Planos", callback_data='planos')],
        [InlineKeyboardButton(f"🛒 Carrinho ({qtd})", callback_data='carrinho')],
        [InlineKeyboardButton("❓ Ajuda", callback_data='ajuda')]
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
    
    await query.answer("Carrinho limpo!")
    await menu(update, context)

# ========== MAIN COM SERVIDOR WEB ==========
def main():
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    
    if not TOKEN:
        print("❌ ERRO: Configure TELEGRAM_TOKEN!")
        return
    
    # Iniciar servidor web em thread separada
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    print("🌐 Servidor web iniciado na porta 5000")
    
    # Iniciar bot
    print("🤖 Iniciando bot...")
    
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(mostrar_planos, pattern='^planos$'))
    app.add_handler(CallbackQueryHandler(ver_plano, pattern='^ver_'))
    app.add_handler(CallbackQueryHandler(adicionar_carrinho, pattern='^add_'))
    app.add_handler(CallbackQueryHandler(ver_carrinho, pattern='^carrinho$'))
    app.add_handler(CallbackQueryHandler(pagar, pattern='^pagar$'))
    app.add_handler(CallbackQueryHandler(confirmar_pagamento, pattern='^pago_'))
    app.add_handler(CallbackQueryHandler(ajuda, pattern='^ajuda$'))
    app.add_handler(CallbackQueryHandler(menu, pattern='^menu$'))
    app.add_handler(CallbackQueryHandler(limpar_carrinho, pattern='^limpar$'))
    
    print("✅ Bot pronto e online!")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
