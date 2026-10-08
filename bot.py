import logging
import os
from datetime import datetime, date
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ----------------------------
# Logging setup
# ----------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ----------------------------
# /start command
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets the user and explains how to use the bot."""
    user = update.effective_user
    name = user.first_name if user and user.first_name else "there"
    await update.message.reply_text(
        f"Hello {name}! 👋\n\n"
        "I am an *Age Calculator Bot* 🎂\n\n"
        "Send me your birthdate in this format:\n"
        "`DD.MM.YYYY`\n\n"
        "Example: `15.08.1995`\n\n"
        "I will tell you exactly how old you are and how many days "
        "until your next birthday! 🎉",
        parse_mode="Markdown",
    )


# ----------------------------
# /help command
# ----------------------------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 *How to use this bot:*\n\n"
        "1. Send your birthdate as `DD.MM.YYYY`\n"
        "2. Example: `15.08.1995`\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/age - Ask for your birthdate again",
        parse_mode="Markdown",
    )


# ----------------------------
# /age command (re-prompt)
# ----------------------------
async def age_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Please send me your birthdate in the format `DD.MM.YYYY`.\n"
        "Example: `15.08.1995`",
        parse_mode="Markdown",
    )


# ----------------------------
# Core: calculate age from message
# ----------------------------
async def calculate_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the user's message and calculates their age."""
    user_input = update.message.text.strip()

    try:
        birth_date = datetime.strptime(user_input, "%d.%m.%Y").date()
        today = date.today()

        # Validate birthdate is not in the future
        if birth_date > today:
            await update.message.reply_text(
                "⚠️ Your birthdate cannot be in the future!\n"
                "Please send it again in the format `DD.MM.YYYY`.",
                parse_mode="Markdown",
            )
            return

        # Calculate age
        age = (
            today.year
            - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
        )

        # Days until next birthday
        try:
            next_birthday = date(today.year, birth_date.month, birth_date.day)
        except ValueError:
            # Handles Feb 29 birthdays on non-leap years
            next_birthday = date(today.year, 3, 1)

        if next_birthday < today:
            try:
                next_birthday = date(today.year + 1, birth_date.month, birth_date.day)
            except ValueError:
                next_birthday = date(today.year + 1, 3, 1)

        days_until = (next_birthday - today).days

        # Total days lived
        total_days = (today - birth_date).days

        # Build response
        response = (
            f"🎂 *Your Age:* {age} years old\n"
            f"📆 *Total days lived:* {total_days:,} days\n"
        )

        if days_until == 0:
            response += "\n🥳 *Happy Birthday!* 🎉🎈"
        elif days_until == 1:
            response += "\n🎁 Your birthday is *tomorrow*! 🎉"
        else:
            response += f"\n⏳ Next birthday in *{days_until}* days."

        await update.message.reply_text(response, parse_mode="Markdown")

    except ValueError:
        await update.message.reply_text(
            "❌ I didn't understand that.\n\n"
            "Please send your birthdate in the format `DD.MM.YYYY`.\n"
            "Example: `15.08.1995`",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await update.message.reply_text(
            "⚠️ Sorry, something went wrong. Please try again."
        )


# ----------------------------
# Main entry point
# ----------------------------
def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Exiting.")
        return

    application = Application.builder().token(token).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("age", age_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, calculate_age)
    )

    logger.info("Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
