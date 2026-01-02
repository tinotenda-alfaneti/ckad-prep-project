import os
from flask import Flask, jsonify

app = Flask(__name__)

# Read from environment variable
MESSAGE = os.getenv('MESSAGE', 'Hello from Event API!')

@app.route('/')
def home():
    return jsonify({
        'service': 'event-api',
        'message': MESSAGE,
        'version': 'v1'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
