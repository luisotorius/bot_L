import logging
from telegram.ext import Application
from config import TOKEN, PROXY_URL
from handlers.commands import get_conv_handler

logging.basicConfig(level=logging.INFO)
#asdf
def main():
    builder = Application.builder().token(TOKEN)
    if PROXY_URL:
        # Usa HTTP(S) proxy si está configurado
        builder = builder.proxy_url(PROXY_URL)
    app = builder.build()

    app.add_handler(get_conv_handler())

    app.run_polling()

if __name__ == "__main__":
    main()
