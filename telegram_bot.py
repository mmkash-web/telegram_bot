import base64
import nest_asyncio
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Allow nested event loops (useful for environments like Jupyter)
nest_asyncio.apply()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
API_USERNAME = os.getenv('API_USERNAME')
API_PASSWORD = os.getenv('API_PASSWORD')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Verify that all required environment variables are set
if not all([API_USERNAME, API_PASSWORD, BOT_TOKEN]):
    logger.error("API_USERNAME, API_PASSWORD, and BOT_TOKEN must be set in the environment.")
    raise EnvironmentError("Required environment variables not set. Please check your .env file.")

# Create Basic Auth token
credentials = f"{API_USERNAME}:{API_PASSWORD}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()
basic_auth_token = f"Basic {encoded_credentials}"

# Define packages with callback_data matching dictionary keys
data_packages = {
    'data_1': ('1GB, 1hr @ Ksh 19', 19),
    'data_2': ('250MB, 24hrs @ Ksh 20', 20),
    'data_3': ('1GB, 24hrs @ Ksh 99', 99),
    'data_4': ('1.5GB, 3hrs @ Ksh 49', 49),
    'data_5': ('350MB, 7 days @ Ksh 47', 47),
    'data_6': ('1.25GB, till midnight @ Ksh 55', 55),
    'data_7': ('2.5GB, 7 days @ Ksh 300', 300),
    'data_8': ('6GB, 7 days @ Ksh 700', 700),
    'data_9': ('1.2GB, 30days @ Ksh 250', 250),
    'data_10': ('2.5GB, 30days @ Ksh 500', 500),
    'data_11': ('10GB, 30days @ Ksh 1,001', 1001)
}

sms_packages = {
    'sms_1': ('20 SMS, 1day @ Ksh 5', 5),
    'sms_2': ('200 SMS, 1day @ Ksh 10', 10),
    'sms_3': ('100 SMS, 7day @ Ksh 21', 21),
    'sms_4': ('1,000 SMS, 7day @ Ksh 30', 30),
    'sms_5': ('1,500 SMS, 30day @ Ksh 101', 101),
    'sms_6': ('3,500 SMS, 30day @ Ksh 201', 201)
}

minutes_packages = {
     'min_1': ('50 flex, till midnight @ Ksh 50', 50),
    'min_2': ('300min, 30day @ Ksh 499', 499),
    'min_3': ('8GB+400min, 30day @ Ksh 999', 999),
    'min_4': ('800min, 30day @ Ksh 1,000', 1000)
}

# Define Conversation States
CHOOSING_TYPE, CHOOSING_PACKAGE, GETTING_PHONE = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a welcome message and prompt user to view menu."""
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(
         f"🎄🎅 Merry Christmas Welcome to Bingwa Sokoni Bot by Emmkash Tech! 🎅🎄, {user_first_name}! Send /menu to view deals. 🎉"
    )
    return ConversationHandler.END

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the main menu with deal types."""
    keyboard = [
        [InlineKeyboardButton("Data Deals", callback_data='data')],
        [InlineKeyboardButton("SMS Deals", callback_data='sms')],
        [InlineKeyboardButton("Minutes Deals", callback_data='minutes')],
        [InlineKeyboardButton("Cancel Purchase", callback_data='cancel_purchase')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a deal type:", reply_markup=reply_markup)
    return CHOOSING_TYPE

async def cancel_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the cancellation of a purchase."""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "You have cancelled the purchase. If you need assistance, click here @emmkash. You can restart anytime by sending /menu."
    )
    return ConversationHandler.END

async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the selection of deal type and display relevant packages."""
    query = update.callback_query
    await query.answer()

    deal_type = query.data
    logger.info(f"Deal type selected: {deal_type}")
    context.user_data['deal_type'] = deal_type

    # Select the appropriate packages based on deal type
    if deal_type == 'data':
        packages = data_packages
    elif deal_type == 'sms':
        packages = sms_packages
    elif deal_type == 'minutes':
        packages = minutes_packages
    else:
        await query.message.reply_text("Invalid selection. Please try again.")
        return ConversationHandler.END

    # Create keyboard for packages
    keyboard = []
    for key, value in packages.items():
        keyboard.append([InlineKeyboardButton(value[0], callback_data=key)])
    keyboard.append([InlineKeyboardButton("Cancel Purchase", callback_data='cancel_purchase')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text("🎄🎅 MERRY CHRISTMAS ,🎉 CHAGUA DEAL YAKO:KUMBUKA KUNUNUA NI MARA MOJA KWA SIKU MKUU ", reply_markup=reply_markup)
    return CHOOSING_PACKAGE

async def choose_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the selection of a specific package and prompt for phone number."""
    query = update.callback_query
    await query.answer()

    package_key = query.data
    deal_type = context.user_data.get('deal_type')
    logger.info(f"Package selected: {package_key} for deal type: {deal_type}")

    # Retrieve the selected package based on deal type
    if deal_type == 'data':
        selected_package = data_packages.get(package_key)
    elif deal_type == 'sms':
        selected_package = sms_packages.get(package_key)
    elif deal_type == 'minutes':
        selected_package = minutes_packages.get(package_key)
    else:
        selected_package = None

    if selected_package is None:
        logger.error(f"Invalid package selection: {package_key} for deal type: {deal_type}")
        await query.message.reply_text("Invalid package selection. Please try again.")
        return ConversationHandler.END

    context.user_data['package'] = selected_package

    await query.message.reply_text(
        f"You selected: {selected_package[0]}.\nPlease enter your phone number:"
    )

    return GETTING_PHONE

async def get_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the phone number input and initiate payment."""
    phone_number = update.message.text.strip()
    context.user_data['phone_number'] = phone_number
    selected_package = context.user_data.get('package')

    logger.info(f"Phone number entered: {phone_number}")

    if selected_package is None:
        await update.message.reply_text("No package selected. Please try again.")
        return ConversationHandler.END

    await update.message.reply_text(
        f"Package: {selected_package[0]}\nPhone Number: {phone_number}\n\nProceeding with payment..."
    )

    # Initiate STK Push
    await initiate_stk_push(phone_number, selected_package[1], update)

    # Allow user to choose another type after payment
    return CHOOSING_TYPE

async def initiate_stk_push(phone_number: str, amount: int, update: Update):
    """Initiate STK Push payment via PayHero API."""
    stk_push_url = "https://backend.payhero.co.ke/api/v2/payments"

    payload = {
        "amount": amount,
        "phone_number": phone_number,
        "channel_id": 852,
        "provider": "m-pesa",
        "external_reference": "INV-009",
        "callback_url": "https://softcash.co.ke/billing/callbackurl.php"
    }

    headers = {"Authorization": basic_auth_token}

    try:
        response = requests.post(stk_push_url, json=payload, headers=headers)

        logger.info(f"STK Push Response Status Code: {response.status_code}")
        logger.info(f"STK Push Response Content: {response.text}")

        response_json = response.json()
        logger.info(f"STK Push Response JSON: {response_json}")

        if response.status_code in [200, 201]:
            if response_json.get('success'):
                status = response_json.get('status')
                logger.info(f"STK Push Status: {status}")

                if status == 'SUCCESS':
                    await update.message.reply_text("Payment successful! Thank you for your purchase.🥳✅")
                else:
                    await update.message.reply_text("Payment processing. Please wait for confirmation✅✅🥳 For help, click here @emmkash")
            else:
                await update.message.reply_text("Payment failed. Please try again.")
        else:
            await update.message.reply_text("Error occurred while processing your payment. Please try again.")

    except Exception as e:
        logger.error(f"Error initiating STK push: {e}")
        await update.message.reply_text("An error occurred while processing your payment. Please try again.")

def main() -> None:
    """Start the Telegram bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Define handlers
    menu_handler = CommandHandler('menu', show_menu)
    start_handler = CommandHandler('start', show_menu)  # Link /start to show_menu

    choose_type_handler = CallbackQueryHandler(choose_type, pattern='^(data|sms|minutes)$')
    choose_package_handler = CallbackQueryHandler(choose_package, pattern='^(data_\d+|sms_\d+|min_\d+)$')
    cancel_handler = CallbackQueryHandler(cancel_purchase, pattern='^cancel_purchase$')
    phone_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone_number)

    # Define ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[start_handler, menu_handler],
        states={
            CHOOSING_TYPE: [choose_type_handler],
            CHOOSING_PACKAGE: [choose_package_handler],
            GETTING_PHONE: [phone_handler],
        },
        fallbacks=[cancel_handler]
    )

    # Add handlers to the application
    application.add_handler(conv_handler)

    logger.info("Starting Bingwa Sokoni Bot...")
    application.run_polling()

if __name__ == '__main__':
    main()
