import base64
import asyncio
import nest_asyncio
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Allow nested event loops
nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your API username and password from environment variables
API_USERNAME = os.getenv('API_USERNAME')
API_PASSWORD = os.getenv('API_PASSWORD')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Check if required environment variables are set
if not all([API_USERNAME, API_PASSWORD, BOT_TOKEN]):
    logger.error("API_USERNAME, API_PASSWORD, and BOT_TOKEN must be set in the environment.")
    raise EnvironmentError("Required environment variables not set.")

# Concatenating username and password with a colon
credentials = f"{API_USERNAME}:{API_PASSWORD}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()
basic_auth_token = f"Basic {encoded_credentials}"

# Data packages available for purchase (sorted by expiry)
data_packages = {
    'data_6': ('1GB @ Ksh 19 (valid for 1 hour)', 19),
    'data_3': ('1.5GB @ Ksh 50 (valid for 3 hours)', 50),
    'data_1': ('1.25GB @ Ksh 55 (valid till midnight)', 55),
    'data_4': ('350MB @ Ksh 49 (valid for 7 days)', 49),
    'data_2': ('2.5GB @ Ksh 300 (valid for 7 days)', 300),
    'data_5': ('6GB @ Ksh 700 (valid for 7 days)', 700),
    'data_7': ('250MB @ Ksh 20 (valid for 24 hours)', 20),
    'data_8': ('1GB @ Ksh 99 (valid for 24 hours)', 99)
}

# SMS packages available for purchase (sorted by expiry)
sms_packages = {
    'sms_3': ('20 SMS @ Ksh 5 (valid for 24 hours)', 5),
    'sms_2': ('200 SMS @ Ksh 10 (valid for 24 hours)', 10),
    'sms_1': ('1000 SMS @ Ksh 30 (valid for 7 days)', 30)
}

# Minutes packages available for purchase (sorted by expiry)
minutes_packages = {
    'min_1': ('34MIN @ Ksh 18 (expiry: midnight)', 18),
    'min_2': ('50MIN @ Ksh 51', 51),
    'min_3': ('100MIN @ Ksh 102 (valid for 2 days)', 102),
    'min_4': ('200MIN @ Ksh 250', 250)
}

# Conversation states
CHOOSING_PACKAGE, GETTING_PHONE, CHOOSING_TYPE = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(f"WELCOME TO BINGWA SOKONI BOT BY EMMKASH TECH 🥳🎉, {user_first_name}! SEND /menu TO VIEW DEAL.")
    return ConversationHandler.END

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Data Deals", callback_data='data')],
        [InlineKeyboardButton("SMS Deals", callback_data='sms')],
        [InlineKeyboardButton("Minutes Deals", callback_data='minutes')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a deal type:", reply_markup=reply_markup)
    return CHOOSING_TYPE

async def cancel_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()  # Acknowledge the callback query
    await update.callback_query.message.reply_text("Purchase has been cancelled. You can start again by sending /menu.")
    return ConversationHandler.END  # End the conversation

async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    deal_type = query.data
    context.user_data['deal_type'] = deal_type

    if deal_type == 'data':
        keyboard = [[InlineKeyboardButton(text=value[0], callback_data=key)] for key, value in data_packages.items()]
    elif deal_type == 'sms':
        keyboard = [[InlineKeyboardButton(text=value[0], callback_data=key)] for key, value in sms_packages.items()]
    elif deal_type == 'minutes':
        keyboard = [[InlineKeyboardButton(text=value[0], callback_data=key)] for key, value in minutes_packages.items()]
    
    # Add cancel button at the bottom
    keyboard.append([InlineKeyboardButton("Cancel Purchase", callback_data='cancel_purchase')])

    # Send the message with the deals and buttons vertically centered
    await query.message.reply_text("AVAILABLE DEALS. KUMBUKA KUNUNUA NI MARA MOJA KWA SIKU:✅", reply_markup=InlineKeyboardMarkup(keyboard))

    return CHOOSING_PACKAGE

async def choose_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    package_number = query.data
    deal_type = context.user_data['deal_type']

    if deal_type == 'data':
        context.user_data['package'] = data_packages[package_number]
    elif deal_type == 'sms':
        context.user_data['package'] = sms_packages[package_number]
    elif deal_type == 'minutes':
        context.user_data['package'] = minutes_packages[package_number]

    await query.message.reply_text(f"You selected: {context.user_data['package'][0]}. Please enter your phone number:")
    return GETTING_PHONE

async def get_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone_number = update.message.text
    context.user_data['phone_number'] = phone_number
    selected_package = context.user_data['package']

    await update.message.reply_text(f"Package: {selected_package[0]}\nPhone Number: {phone_number}\n\nProceeding with payment...")

    # Initiate STK push
    await initiate_stk_push(phone_number, selected_package[1], update)

    return ConversationHandler.END

async def initiate_stk_push(phone_number: str, amount: int, update: Update):
    stk_push_url = "https://backend.payhero.co.ke/api/v2/payments"

    payload = {
        "amount": amount,
        "phone_number": phone_number,
        "channel_id": 852,
        "provider": "m-pesa",
        "external_reference": "INV-009",
        "callback_url": "https://softcash.co.ke/billing/callbackurl.php"
    }

    try:
        response = requests.post(stk_push_url, json=payload, headers={"Authorization": basic_auth_token})

        # Log the status code and response content for debugging
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Content: {response.text}")

        response_json = response.json()
        logger.info(f"Response JSON: {response_json}")

        if response.status_code in [200, 201]:
            if response_json.get('success'):
                status = response_json.get('status')
                logger.info(f"STK Push Status: {status}")

                if status == 'QUEUED':
                    await update.message.reply_text("Please enter your M-Pesa PIN to proceed with payment.✅ For help, click here @emmkash.")
                elif status == 'SUCCESS':
                    await update.message.reply_text("Payment successful! Thank you for your purchase. Enjoy your data! 🎉")
                else:
                    await update.message.reply_text(f"Payment status: {status}. Please try again.")
            else:
                await update.message.reply_text(f"Payment failed: {response_json.get('message')}. Please try again.")
        else:
            await update.message.reply_text("Failed to initiate payment. Please try again later.")
    except Exception as e:
        logger.error(f"Error during STK push: {e}")
        await update.message.reply_text("An error occurred while processing your request. Please try again later.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('menu', show_menu)],
        states={
            CHOOSING_TYPE: [CallbackQueryHandler(choose_type)],
            CHOOSING_PACKAGE: [CallbackQueryHandler(choose_package)],
            GETTING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone_number)],
        },
        fallbacks=[CommandHandler('cancel', cancel_purchase), CallbackQueryHandler(cancel_purchase, pattern='cancel_purchase')]
    )

    application.add_handler(conv_handler)

    application.run_polling()

if __name__ == '__main__':
    main()
