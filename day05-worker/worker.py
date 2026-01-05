import os
import time
import redis

# Read configuration from environment
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/data')
WORKER_NAME = os.getenv('WORKER_NAME', 'worker-1')

print(f"[{WORKER_NAME}] Starting worker...")
print(f"[{WORKER_NAME}] Connecting to Redis at {REDIS_HOST}:{REDIS_PORT}")

# Connect to Redis
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.ping()
    print(f"[{WORKER_NAME}] Connected to Redis successfully!")
except Exception as e:
    print(f"[{WORKER_NAME}] Failed to connect to Redis: {e}")
    exit(1)

# Worker loop
counter = 0
while True:
    counter += 1
    
    # Check for messages in Redis list
    message = r.lpop('work_queue')
    
    if message:
        print(f"[{WORKER_NAME}] Processing: {message}")
        
        # Write to output file
        output_file = f"{OUTPUT_DIR}/output.txt"
        with open(output_file, 'a') as f:
            f.write(f"[{WORKER_NAME}] Processed: {message}\n")
        
        print(f"[{WORKER_NAME}] Completed: {message}")
    else:
        # No work, just heartbeat
        if counter % 10 == 0:
            print(f"[{WORKER_NAME}] Waiting for work... (checked {counter} times)")
    
    time.sleep(1)
