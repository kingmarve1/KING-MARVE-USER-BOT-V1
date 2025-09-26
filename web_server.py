from flask import Flask
import threading
import time

app = Flask(__name__)

@app.route('/')
def home():
    return "🌑 𝐊𝐈𝐍̃𝐆 𝐌𝐀̊𝐑𝐕𝐄̈ 𝐔𝐒𝐄𝐑 𝐁𝐎𝐓 is running!"

@app.route('/ping')
def ping():
    return "Pong! 🏓"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    thread = threading.Thread(target=run_flask)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    keep_alive()
