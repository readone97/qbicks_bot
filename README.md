# qbicks_bot
a crypto analysis bot using Vybe network API




Setup Instructions
Prerequisites
Python 3.8 or higher

Telegram account and bot token (created via BotFather)

Vybe Network API key (sign up on Vybe Network platform)

Installation
Clone or download the project repository.

Install required Python packages:

bash
pip install python-telegram-bot requests matplotlib seaborn numpy
Set environment variables or directly update the script with your credentials:

TELEGRAM_BOT_TOKEN - your Telegram bot token.

VYBE_API_KEY - your Vybe Network API key.

Running the Bot
Ensure your system has internet access.

Run the bot script:

bash
python app.py
Interact with the bot on Telegram by sending commands (commands implementation is assumed in the full script).

Usage
Use Telegram commands to request price, details, or trend data for supported tokens.

Inline buttons may be provided for easy navigation and selection.

Trend plots are sent as images for better visualization.
