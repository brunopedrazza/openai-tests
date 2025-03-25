# OpenAI Integration Projects

This repository contains several Python-based projects that integrate with OpenAI's APIs and other services. Each project serves a different purpose and demonstrates various ways to interact with AI and external services.

## Projects Overview

### 1. ChatGPT Terminal
A command-line interface for interacting with ChatGPT, featuring:
- Direct terminal-based conversations with ChatGPT
- Integration with Google services
- Custom function handling
- Service-based architecture for extensibility

### 2. ChatGPT Voice
A voice interface for ChatGPT that enables:
- Voice input/output with ChatGPT
- Speech-to-text and text-to-speech capabilities
- Interactive voice conversations

### 3. Coinbase Telegram Bot
A Telegram bot that interfaces with Coinbase, providing:
- Cryptocurrency price monitoring
- Automated trading notifications
- Telegram-based commands and interactions

## Prerequisites

- Python 3.x
- Virtual environment (recommended)
- OpenAI API key
- Other service-specific API keys (as needed)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/brunopedrazza/openai-tests.git
cd openai-tests
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```
Then edit `.env` with your API keys and configuration.

## Project-Specific Setup

### ChatGPT Terminal
1. Configure Google credentials (if using Google integration)
2. Run: `python chatgpt-terminal/index.py`

### ChatGPT Voice
1. Ensure your system has audio input/output capabilities
2. Run: `python chatgpt-voice/index.py`

### Coinbase Telegram Bot
1. Set up Telegram bot token
2. Configure Coinbase API credentials
3. Run: `python coinbase-telegram-bot/telegram_bot.py`

## Testing

Run tests for the Coinbase Telegram Bot:
```bash
python coinbase-telegram-bot/tests.py
```

## Environment Variables

Key environment variables needed (see `.env.example` for full list):
- `OPENAI_API_KEY`: Your OpenAI API key
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `COINBASE_API_KEY`: Coinbase API key
- `COINBASE_API_SECRET`: Coinbase API secret

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 