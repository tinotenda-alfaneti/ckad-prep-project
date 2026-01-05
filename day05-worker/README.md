# Day 5 - Worker (Queue Consumer)

## Objectives
- Build a worker that connects to Redis
- Demonstrate service-to-service networking
- Use DNS for service discovery
- Write output to mounted volume

## CKAD Skills Covered
- Services & Networking (20%)
- Configuration

---

## Application Code

Simple Python worker that consumes messages from Redis and writes output.

**File: `worker.py`**

```python
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
```

**File: `requirements.txt`**

```
redis==5.0.1
```

---

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker.py .

CMD ["python", "-u", "worker.py"]
```

**Note:** `-u` flag makes Python output unbuffered (important for log streaming)

---

## Build & Load Image

```bash
cd ~/projects/homelab/ckad-project/day05-worker

# Build
docker build -t worker:v1 .

# Make image available in cluster
# (Push to registry or load locally)

# Verify
kubectl run test --image=worker:v1 --dry-run=client -o yaml
```

---

## Kubernetes Manifests

### ConfigMap for Worker

**File: `configmap.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: worker-config
  namespace: dev
data:
  REDIS_HOST: "redis"  # Service name (DNS)
  REDIS_PORT: "6379"
  OUTPUT_DIR: "/data"
```

### Deployment

**File: `deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker
  namespace: dev
  labels:
    app: worker
spec:
  replicas: 2  # Multiple workers can process queue
  selector:
    matchLabels:
      app: worker
  template:
    metadata:
      labels:
        app: worker
    spec:
      containers:
      - name: worker
        image: worker:v1
        imagePullPolicy: Never
        envFrom:
        - configMapRef:
            name: worker-config
        env:
        - name: WORKER_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name  # Pod name as worker ID
        volumeMounts:
        - name: output
          mountPath: /data
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
      volumes:
      - name: output
        emptyDir: {}  # Temporary storage for output
```

**Key Concepts:**
- **fieldRef**: Inject pod metadata (name, namespace, IP) as env var
- **emptyDir**: Temporary volume (lost on pod deletion)
- **DNS**: Worker connects to Redis via service name `redis`

---

## Deploy

```bash
cd ~/projects/homelab/ckad-project/day05-worker/k8s

# Apply manifests
k apply -f configmap.yaml
k apply -f deployment.yaml

# Verify
k get pods -n dev
k logs -f deployment/worker -n dev

# Should see:
# [worker-xxx] Starting worker...
# [worker-xxx] Connected to Redis successfully!
# [worker-xxx] Waiting for work...
```

---

## Test Service-to-Service Communication

### Send Work to Queue

```bash
# Connect to Redis
k exec -it deployment/redis -n dev -- redis-cli

# Push messages to queue
RPUSH work_queue "Process image 1"
RPUSH work_queue "Process image 2"
RPUSH work_queue "Send email to user@example.com"

# Check queue length
LLEN work_queue
# Output: 3

exit
```

### Watch Workers Process

```bash
# Stream logs from all worker pods
k logs -f deployment/worker -n dev --all-containers=true

# You should see:
# [worker-xxx] Processing: Process image 1
# [worker-xxx] Completed: Process image 1
# [worker-yyy] Processing: Process image 2
# [worker-yyy] Completed: Process image 2
```

### Verify Output File

```bash
# Exec into worker pod
k exec -it deployment/worker -n dev -- sh

# Check output file
cat /data/output.txt
# Shows processed messages

exit
```

---

## DNS Resolution

Kubernetes provides automatic DNS for services:

| DNS Name | Scope | Example |
|----------|-------|---------|
| `redis` | Same namespace | `redis` |
| `redis.dev` | Specific namespace | `redis.dev` |
| `redis.dev.svc.cluster.local` | Fully qualified | `redis.dev.svc.cluster.local` |

### Test DNS

```bash
# Exec into worker
k exec -it deployment/worker -n dev -- sh

# Test DNS resolution
nslookup redis
# Shows IP address of redis service

nslookup redis.dev.svc.cluster.local

# Ping (if available)
ping -c 3 redis

exit
```

---

## Common Exam Tasks

### Task 1: Change Redis Host

```bash
# Update ConfigMap
k edit configmap worker-config -n dev
# Change REDIS_HOST: "redis" to "redis.dev.svc.cluster.local"

# Restart workers to pick up change
k rollout restart deployment worker -n dev

# Verify
k logs -f deployment/worker -n dev
```

### Task 2: Scale Workers

```bash
# Scale up
k scale deployment worker --replicas=5 -n dev

# Verify
k get pods -n dev -l app=worker

# Push more work
k exec -it deployment/redis -n dev -- redis-cli
RPUSH work_queue "Task 1" "Task 2" "Task 3" "Task 4" "Task 5"
exit

# Watch distributed processing
k logs -f deployment/worker -n dev --all-containers=true
```

### Task 3: Debug Connection Issues

```bash
# Worker can't connect to Redis
k logs deployment/worker -n dev
# Error: Failed to connect to Redis: [Errno -2] Name or service not known

# Check service exists
k get svc redis -n dev
# If not found, create it

# Check endpoints
k get endpoints redis -n dev
# Should show pod IPs

# Check if Redis pod is running
k get pods -n dev -l app=redis
```

### Task 4: Use Persistent Volume for Output

```yaml
# Replace emptyDir with PVC for persistent output
volumes:
- name: output
  persistentVolumeClaim:
    claimName: worker-output-pvc
```

---

## Service Types Comparison

| Type | Access | Use Case | Exam Frequency |
|------|--------|----------|----------------|
| ClusterIP | Internal only | Default, service-to-service | High |
| NodePort | External via node IP:port | Quick external access | Medium |
| LoadBalancer | External via cloud LB | Production external access | Low (CKAD) |
| ExternalName | DNS alias | External service mapping | Low |

---

## Testing Network Connectivity

```bash
# Create debug pod
k run netdebug --image=nicolaka/netshoot -n dev -- sleep 3600

# Exec into it
k exec -it netdebug -n dev -- bash

# Test connectivity
curl http://event-api
curl http://redis:6379  # Won't work (not HTTP)
nc -zv redis 6379  # Port check
nslookup redis
dig redis

exit

# Cleanup
k delete pod netdebug -n dev
```

---

## fieldRef Examples

Inject pod metadata as environment variables:

```yaml
env:
- name: POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name

- name: POD_NAMESPACE
  valueFrom:
    fieldRef:
      fieldPath: metadata.namespace

- name: POD_IP
  valueFrom:
    fieldRef:
      fieldPath: status.podIP

- name: NODE_NAME
  valueFrom:
    fieldRef:
      fieldPath: spec.nodeName
```

---

## Speed Commands (Exam Practice)

```bash
# Create configmap for service hostname
k create cm svc-config --from-literal=REDIS_HOST=redis -n dev

# Create deployment with configmap
k create deploy worker --image=worker:v1 -n dev --dry-run=client -o yaml > deploy.yaml
# Edit to add envFrom configMapRef

# Quick debug pod
k run debug --image=busybox -n dev -it --rm -- sh

# Test service connectivity
k run curl --image=curlimages/curl -n dev -it --rm -- curl http://event-api
```

---

## Verification Checklist

- [ ] Worker image built and loaded
- [ ] ConfigMap created with Redis connection details
- [ ] Worker deployment running
- [ ] Workers connect to Redis successfully
- [ ] Can push messages to Redis queue
- [ ] Workers process messages
- [ ] Output written to /data/output.txt
- [ ] DNS resolution works (redis resolves)
- [ ] Can scale workers
- [ ] Multiple workers process queue concurrently

---

## Key Takeaways

1. **Service Discovery**: Use service name as hostname (DNS)
2. **DNS**: `service`, `service.namespace`, `service.namespace.svc.cluster.local`
3. **fieldRef**: Inject pod metadata as env vars
4. **emptyDir**: Fast temporary storage (per-pod)
5. **Queue Pattern**: Multiple workers consume from shared Redis queue
6. **Logs**: Use `-f` for streaming, `--all-containers` for all pods
7. **Exam tip**: Know how to debug network connectivity (nslookup, curl, endpoints)

---
