# Day 7 - Health Probes

## Objectives
- Implement liveness probes
- Implement readiness probes
- Implement startup probes
- Understand probe failure behaviors

## CKAD Skills Covered
- Observability (18%)

---

## Probe Types

| Probe | Purpose | Failure Action |
|-------|---------|----------------|
| **Liveness** | Is the app healthy? | Restart container |
| **Readiness** | Can the app serve traffic? | Remove from Service endpoints |
| **Startup** | Has the app started? | Wait before liveness checks |

---

## Updated API with Probes

**File: `app-with-probes.py`**

```python
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
```

---

## Deployment with All Probes

**File: `deployment-with-probes.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-api-probes
  namespace: dev
spec:
  replicas: 2
  selector:
    matchLabels:
      app: event-api-probes
  template:
    metadata:
      labels:
        app: event-api-probes
    spec:
      containers:
      - name: api
        image: event-api:v2  # Updated version with probe endpoints
        imagePullPolicy: Never
        ports:
        - containerPort: 8080
        env:
        - name: MESSAGE
          value: "API with health probes"
        
        # Startup Probe - runs first
        startupProbe:
          httpGet:
            path: /startup
            port: 8080
          initialDelaySeconds: 0
          periodSeconds: 2
          failureThreshold: 30  # 30 * 2s = 60s max startup time
        
        # Liveness Probe - restarts if fails
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3  # Fail 3 times = restart
        
        # Readiness Probe - removes from service if fails
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 3
          failureThreshold: 2  # Fail 2 times = not ready
        
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: event-api-probes
  namespace: dev
spec:
  selector:
    app: event-api-probes
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
```

---

## Probe Mechanisms

### HTTP GET Probe
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
    httpHeaders:
    - name: Custom-Header
      value: HealthCheck
  initialDelaySeconds: 10
  periodSeconds: 5
```

### TCP Socket Probe
```yaml
livenessProbe:
  tcpSocket:
    port: 6379
  initialDelaySeconds: 5
  periodSeconds: 10
```

### Exec Command Probe
```yaml
livenessProbe:
  exec:
    command:
    - cat
    - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## Probe Configuration Fields

| Field | Description | Default |
|-------|-------------|---------|
| `initialDelaySeconds` | Wait before first probe | 0 |
| `periodSeconds` | How often to probe | 10 |
| `timeoutSeconds` | Probe timeout | 1 |
| `successThreshold` | Consecutive successes needed | 1 |
| `failureThreshold` | Consecutive failures before action | 3 |

---

## Test Scenarios

### Build Updated Image

```bash
cd ~/projects/homelab/ckad-project/day07-probes

# Build with probe endpoints
docker build -t event-api:v2 .
# Make image available in cluster
# (Push to registry or load locally)
```

### Deploy

```bash
k apply -f k8s/deployment-with-probes.yaml

# Watch pod status
k get pods -n dev -l app=event-api-probes -w
```

### Test Startup Probe

```bash
POD=$(k get pod -n dev -l app=event-api-probes -o jsonpath='{.items[0].metadata.name}')

# Check startup probe status
k describe pod $POD -n dev | grep -A 10 "Startup"

# Pod won't be Ready until startup probe succeeds
```

### Test Readiness Probe Failure

```bash
# Make pod unready
k exec $POD -n dev -- curl -s localhost:8080/unready

# Check pod status
k get pods -n dev -l app=event-api-probes
# STATUS: Running but 0/1 Ready

# Check endpoints
k get endpoints event-api-probes -n dev
# Pod IP removed from endpoints!

# Service won't route to this pod
k port-forward svc/event-api-probes 8080:80 -n dev
curl localhost:8080  # Routes to other healthy pod only

# Recover
k exec $POD -n dev -- curl -s localhost:8080/recover
```

### Test Liveness Probe Failure

```bash
# Make pod unhealthy
k exec $POD -n dev -- curl -s localhost:8080/fail

# Watch pod restart
k get pods -n dev -l app=event-api-probes -w
# After 3 failures (15 seconds), container restarts

# Check restart count
k get pods -n dev -l app=event-api-probes
# RESTARTS column increments

# View events
k describe pod $POD -n dev | grep -A 5 Events
# Shows: Liveness probe failed
```

---

## Common Exam Scenarios

### Scenario 1: Add Liveness Probe to Existing Deployment

```bash
k edit deployment nginx -n dev
```

```yaml
spec:
  template:
    spec:
      containers:
      - name: nginx
        image: nginx
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Scenario 2: Debug CrashLoopBackOff from Probe

```bash
k get pods -n dev
# STATUS: CrashLoopBackOff

k describe pod <POD> -n dev
# Events: Liveness probe failed: Get http://...:8080/health: dial tcp: connection refused

# Check if port is correct
k get pod <POD> -n dev -o yaml | grep containerPort

# Check if path exists
k logs <POD> -n dev
```

### Scenario 3: Slow Starting App

```yaml
# Use startup probe with long failureThreshold
startupProbe:
  httpGet:
    path: /health
    port: 8080
  periodSeconds: 10
  failureThreshold: 30  # 5 minutes max
```

---

## Redis with TCP Probe

**File: `redis-with-probe.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: dev
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        
        livenessProbe:
          tcpSocket:
            port: 6379
          initialDelaySeconds: 5
          periodSeconds: 10
        
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## Speed Commands

```bash
# Add liveness probe via kubectl
k set probe deployment/myapp --liveness --get-url=http://:8080/health --initial-delay-seconds=10 -n dev

# Add readiness probe
k set probe deployment/myapp --readiness --get-url=http://:8080/ready --initial-delay-seconds=5 -n dev

# Remove probe
k set probe deployment/myapp --liveness --remove=true -n dev
```

---

## Verification Checklist

- [ ] Deployment with all three probe types created
- [ ] Startup probe passes before liveness starts
- [ ] Readiness failure removes pod from endpoints
- [ ] Liveness failure restarts container
- [ ] Can trigger probe failures via endpoints
- [ ] Understand initialDelay, period, threshold
- [ ] Know all three probe mechanisms (HTTP, TCP, Exec)

---

## Key Takeaways

1. **Startup**: Protects slow-starting apps from premature liveness kills
2. **Liveness**: Restarts deadlocked/unhealthy containers
3. **Readiness**: Controls Service traffic routing
4. **Probe types**: HTTP GET (most common), TCP Socket, Exec Command
5. **failureThreshold**: Number of consecutive failures before action
6. **initialDelaySeconds**: Critical for avoiding false failures at startup
7. **Exam tip**: Liveness kills pods, Readiness removes from Service

---

## Next: Day 8

Tomorrow you'll create **batch Jobs**:
- One-off task execution
- Job completion and failure handling
- Parallelism and backoff

**Estimated time:** 30-45 minutes
