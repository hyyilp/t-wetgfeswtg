import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from dotenv import load_dotenv
from google import genai
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()
TOKEN = os.getenv("TOKEN")
API_KEY = os.getenv("APIKEY")
PORT = int(os.getenv("PORT", "8080"))
client = genai.Client(api_key=API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ПРИВІТ , Я ПРАЦЮЮ!")


async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    que = update.message.text
    await update.message.reply_text("Думаю над цим .....")
    response = await client.aio.models.generate_content(model="gemini-3.6-flash",
                                                        contents=que)
    answer = "".join(
        character for character in (response.text or "")
        if character.isalnum() or character.isspace()
    )
    if not answer:
        answer = "The response was empty"
    await  update.message.reply_text(answer)


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK")


def main() -> None:
    health_server = ThreadingHTTPServer(("0.0.0.0", PORT), HealthCheckHandler)
    Thread(target=health_server.serve_forever, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_ai))
    try:
        app.run_polling()
    finally:
        health_server.shutdown()
        health_server.server_close()


if __name__ == "__main__":
    main()
