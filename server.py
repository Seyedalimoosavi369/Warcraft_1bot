from flask import Flask, send_file
import os

app = Flask(__name__)

@app.route('/')
def index():
    return send_file(os.path.join(os.path.dirname(__file__), 'index.html'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
