import json
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
import os
from tests import tools, create_order

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize OpenAI client
client = OpenAI()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hi! Send me your crypto trading instructions.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the user's message and execute the trading logic."""
    try:
        user_input = update.message.text
        
        # Create the messages array for the OpenAI API
        messages = [{
            "role": "user",
            "content": user_input
        }]

        try:
            # Get the completion from OpenAI
            completion = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
            )
        except Exception as e:
            await update.message.reply_text(
                "Sorry, I'm having trouble understanding your request. Please try rephrasing it.\n"
                "For example: 'Buy $100 worth of BTC' or 'Sell all my ETH'"
            )
            logging.error(f"OpenAI API error: {str(e)}")
            return

        try:
            tool_call = completion.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
        except (IndexError, json.JSONDecodeError, AttributeError) as e:
            await update.message.reply_text(
                "I couldn't process your trading instruction. Please make sure to specify:\n"
                "1. Action (buy/sell)\n"
                "2. Amount (a number or 'all')\n"
                "3. Cryptocurrency (e.g., BTC, ETH)\n\n"
                "Example: 'Buy $500 worth of ETH' or 'Sell all my BTC'"
            )
            logging.error(f"Tool call processing error: {str(e)}")
            return

        try:
            # Execute the trade
            result = create_order(args["action"], args["amountInDollars"], args["asset"])
            
            if not result.get("success", False):
                error_message = result.get("error", "Unknown error occurred")
                await update.message.reply_text(
                    f"❌ Trading error: {error_message}\n"
                    "Please check your balance and try again."
                )
                return

            messages.append(completion.choices[0].message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })

            # Get the final response
            try:
                completion_2 = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=tools,
                )
                await update.message.reply_text(completion_2.choices[0].message.content)
            except Exception as e:
                # If we can't get the nice formatted message, at least show the successful result
                await update.message.reply_text(
                    f"✅ Trade executed successfully!\n"
                    f"Order ID: {result['order_id']}\n"
                    f"Product: {result['product_id']}\n"
                    f"Side: {result['side']}\n"
                    f"Price: ${result['price']}\n"
                    f"Amount: {result['rounded_amount']}"
                )

        except KeyError as e:
            await update.message.reply_text(
                "I couldn't understand some parts of your trading instruction. Please make sure to specify:\n"
                "1. Action (buy/sell)\n"
                "2. Amount (a number or 'all')\n"
                "3. Cryptocurrency (e.g., BTC, ETH)\n\n"
                "Example: 'Buy $500 worth of ETH' or 'Sell all my BTC'"
            )
            logging.error(f"Missing required argument: {str(e)}")
            return
        except Exception as e:
            await update.message.reply_text(
                "❌ An error occurred while executing your trade. Please try again.\n"
                "If the problem persists, make sure you have sufficient balance and the trading pair is available."
            )
            logging.error(f"Trade execution error: {str(e)}")
            return

    except Exception as e:
        await update.message.reply_text(
            "❌ Something went wrong. Please try again later.\n"
            "If the problem persists, contact support."
        )
        logging.error(f"Unexpected error: {str(e)}")
        return

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(os.environ['TELEGRAM_CB_ORDER_BOT_TOKEN']).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 