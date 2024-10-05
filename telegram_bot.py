import base64
import asyncio
import nest_asyncio
import requests  # Import requests for making API calls
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from dotenv import load_dotenv  # Import dotenv to load environment variables
import os  # Import os to access environment variables

# Load environment variables from .env file
load_dotenv()

# Allow nested event loops
nest_asyncio.apply()

# Your API username and password from environment variables
API_USERNAME = os.getenv('API_USERNAME')
API_PASSWORD = os.getenv('API_PASSWORD')

# Concatenating username and password with a colon
credentials = f"{API_USERNAME}:{API_PASSWORD}"

# Base64 encode the credentials
encoded_credentials = base64.b64encode(credentials.encode()).decode()

# Creating the Basic Auth token
basic_auth_token = f"Basic {encoded_credentials}"

# Data packages available for purchase
data_packages = {
    "1": ("1.25GB @ Ksh 55 (valid till midnight)", 55),
    "2": ("1.5GB @ Ksh 50 (valid for 3 hours)", 50),
    "3": ("250MB @ Ksh 20 (valid for 24 hours)", 20),
    "4": ("1GB @ Ksh 99 (valid for 24 hours)", 99),
    "5": ("2.5GB @ Ksh 300 (valid for 7 days)", 300),
    "6": ("350MB @ Ksh 49 (valid for 7 days)", 49),
    "7": ("6GB @ Ksh 700 (valid for 7 days)", 700),
    "8": ("1GB @ Ksh 19 (valid for 1 hour)", 19),
}

# SMS packages available for purchase
sms_packages = {
    "1": ("20 SMS @ Ksh 5 (valid for 24 hours)", 5),
    "2": ("200 SMS @ Ksh 10 (valid for 24 hours)", 10),
    "3": ("1000 SMS @ Ksh 30 (valid for 7 days)", 30),
}

# Minutes packages available for purchase
minutes_packages = {
    "1": ("34MIN @ Ksh 18 (expiry: midnight)", 18),
    "2": ("50MIN @ Ksh 51", 51),
    "3": ("100MIN @ Ksh 102 (valid for 2 days)", 102),
}

# Conversation states
CHOOSING_PACKAGE, GETTING_PHONE, CHOOSING_TYPE = range(3)

# Function to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_first_name = update.effective_user.first_name  # Get the user's first name
    await update.message.reply_text(f"WELCOME TO BINGWA SOKONI BOT BY EMMKASH TECH 🥳🎉, {user_first_name}! SEND /menu TO VIEW DEAL.")
    return ConversationHandler.END

# Function to show the main menu
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        [InlineKeyboardButton("Data Deals", callback_data='data')],
        [InlineKeyboardButton("SMS Deals", callback_data='sms')],
        [InlineKeyboardButton("Minutes Deals", callback_data='minutes')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Select a deal type:", reply_markup=reply_markup)
    return CHOOSING_TYPE

# Function to handle the selection of deal type
async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    deal_type = query.data  # Get the type of deal from the callback data
    context.user_data['deal_type'] = deal_type  # Store the selected deal type

    if deal_type == 'data':
        keyboard = [[InlineKeyboardButton(text=value[0], callback_data=key)] for key, value in data_packages.items()]
        await query.message.reply_text("AVAILABLE DEALS. KUMBUKA KUNUNUA NI MARA MOJA KWA SIKU:✅", reply_markup=InlineKeyboardMarkup(keyboard))
    elif deal_type == 'sms':
        keyboard = [[InlineKeyboardButton(text=value[0], callback_data=key)] for key, value in sms_packages.items()]
        await query.message.reply_text("AVAILABLE DEALS. KUMBUKA KUNUNUA NI MARA MOJA KWA SIKU:✅", reply_markup=InlineKeyboardMarkup(keyboard))
    elif deal_type == 'minutes':
        keyboard = [[InlineKeyboardButton(text=value[0], callback_data=key)] for key, value in minutes_packages.items()]
        await query.message.reply_text("AVAILABLE DEALS. KUMBUKA KUNUNUA NI MARA MOJA KWA SIKU:✅", reply_markup=InlineKeyboardMarkup(keyboard))

    return CHOOSING_PACKAGE

# Function to handle package selection via buttons
async def choose_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    package_number = query.data  # Get the package number from the callback data
    deal_type = context.user_data['deal_type']

    if deal_type == 'data':
        context.user_data['package'] = data_packages[package_number]
    elif deal_type == 'sms':
        context.user_data['package'] = sms_packages[package_number]
    elif deal_type == 'minutes':
        context.user_data['package'] = minutes_packages[package_number]

    await query.message.reply_text(f"You selected: {context.user_data['package'][0]}. Please enter your phone number:")
    return GETTING_PHONE

# Function to handle phone number input
async def get_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone_number = update.message.text

    # You may want to add phone number validation here
    context.user_data['phone_number'] = phone_number
    selected_package = context.user_data['package']
    await update.message.reply_text(f"Package: {selected_package[0]}\nPhone Number: {phone_number}\n\nProceeding with payment...")

    # Initiate STK push
    await initiate_stk_push(phone_number, selected_package[1], update)

    # Reset the conversation
    return ConversationHandler.END

# Function to initiate the STK push
async def initiate_stk_push(phone_number: str, amount: int, update: Update):
    stk_push_url = "https://backend.payhero.co.ke/api/v2/payments"  # Replace with your actual API endpoint

    payload = {
        "amount": amount,
        "phone_number": phone_number,
        "channel_id": 852,  # Use the provided channel ID
        "provider": "m-pesa",  # Use the provided provider
        "external_reference": "INV-009",  # Unique external reference for the transaction
        "callback_url": "https://softcash.co.ke/billing/callbackurl.php"  # Your callback URL
    }

    try:
        response = requests.post(stk_push_url, json=payload, headers={"Authorization": basic_auth_token})

        # Log the status code and response content for debugging
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")

        response_json = response.json()

        # Log the complete response for additional debugging
        print(f"Response JSON: {response_json}")

        # Check if the response indicates success
        if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
            if response_json.get('success'):
                # Log the status for debugging
                status = response_json.get('status')
                print(f"STK Push Status: {status}")

                # Handle both successful and queued statuses
                if status == 'QUEUED':
                    await update.message.reply_text("Please enter your mpesa pin to pay.✅for help click here @emmkash.")
                elif status == 'SUCCESS':
                    await update.message.reply_text("Payment successful! Thank you for your purchase. Enjoy your data! 🎉")
                else:
                    await update.message.reply_text("Payment was unsuccessful. Please try again later.❌")
            else:
                await update.message.reply_text("Payment was unsuccessful. Please try again later.❌")
        else:
            await update.message.reply_text("Failed to initiate payment. Please try again later.❌")

    except Exception as e:
        # Log the exception for debugging
        print(f"An error occurred: {e}")
        await update.message.reply_text("An error occurred while processing your request. Please try again later.❌")

# Function to handle errors
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

# Main function to run the bot
if __name__ == "__main__":
    # Create the Application and add handlers
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", show_menu))
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_TYPE: [CallbackQueryHandler(choose_type)],
            CHOOSING_PACKAGE: [CallbackQueryHandler(choose_package)],
            GETTING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone_number)],
        },
        fallbacks=[CommandHandler("start", start)],
    ))

    # Set error handler
    app.add_error_handler(error_handler)

    # Run the bot
    app.run_polling()
