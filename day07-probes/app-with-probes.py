import os
import time
from flask import Flask, jsonify

app = Flask(__name__)

# Simulate app state
start_time = time.time()
healthy = True
ready = True

@app.route('/')
def home():
    return jsonify({
        'service': 'event-api',
        'message': os.getenv('MESSAGE', 'Hello!'),
        'uptime': int(time.time() - start_time)
    })

@app.route('/health')
def health():
    """Liveness probe endpoint"""
    if healthy:
        return jsonify({'status': 'healthy'}), 200
    else:
        return jsonify({'status': 'unhealthy'}), 500

@app.route('/ready')
def ready_check():
    """Readiness probe endpoint"""
    if ready:
        return jsonify({'status': 'ready'}), 200
    else:
        return jsonify({'status': 'not ready'}), 503

@app.route('/startup')
def startup():
    """Startup probe endpoint"""
    uptime = time.time() - start_time
    if uptime > 5:  # App needs 5 seconds to start
        return jsonify({'status': 'started'}), 200
    else:
        return jsonify({'status': 'starting'}), 503

# Admin endpoints for testing
@app.route('/fail')
def fail():
    """Make liveness probe fail"""
    global healthy
    healthy = False
    return jsonify({'message': 'Liveness will now fail'})

@app.route('/unready')
def unready():
    """Make readiness probe fail"""
    global ready
    ready = False
    return jsonify({'message': 'Readiness will now fail'})

@app.route('/recover')
def recover():
    """Recover all probes"""
    global healthy, ready
    healthy = True
    ready = True
    return jsonify({'message': 'All probes recovered'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
