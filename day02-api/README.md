# Day 2 - Event API (HTTP Service)

## Objectives
- Build a simple HTTP API
- Create a Deployment
- Expose via Service
- Use labels and selectors
- Inject environment variables

## CKAD Skills Covered
- Core Concepts (20%)
- Pod Design (20%)

---

## Application Code

Simple Python Flask API that responds with a configurable message.

**File: `app.py`**

```python
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
```

**File: `requirements.txt`**

```
Flask==3.0.0
```

---

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8080

CMD ["python", "app.py"]
```

---

## Build & Load Image

```bash
cd ~/projects/homelab/ckad-project/day02-api

# Build image
docker build -t event-api:v1 .

# Make image available in cluster
# (Push to registry or load locally depending on your setup)
# Example: docker tag event-api:v1 your-registry/event-api:v1 && docker push your-registry/event-api:v1

# Verify (if using local registry or loaded)
kubectl run test --image=event-api:v1 --dry-run=client -o yaml
```

---

## Kubernetes Manifests

### Deployment

**File: `deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-api
  namespace: dev
  labels:
    app: event-api
    tier: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: event-api
  template:
    metadata:
      labels:
        app: event-api
        tier: backend
    spec:
      containers:
      - name: api
        image: event-api:v1
        imagePullPolicy: Never  # Use local image
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: MESSAGE
          value: "Hello from CKAD Event API!"
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

**Key Exam Concepts:**
- `selector.matchLabels` must match `template.metadata.labels`
- `imagePullPolicy: Never` for local images
- Resource requests/limits are exam favorites
- Labels enable querying: `k get pods -l app=event-api`

### Service

**File: `service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: event-api
  namespace: dev
  labels:
    app: event-api
spec:
  type: ClusterIP
  selector:
    app: event-api  # Must match pod labels
  ports:
  - port: 80        # Service port
    targetPort: 8080  # Container port
    protocol: TCP
    name: http
```

**Key Exam Concepts:**
- `selector` matches pod labels from Deployment
- `port` (service) vs `targetPort` (container)
- ClusterIP = internal only (default)

---

## Deploy

```bash
cd ~/projects/homelab/ckad-project/day02-api/k8s

# Apply manifests
k apply -f deployment.yaml
k apply -f service.yaml

# Verify deployment
k get deployments -n dev
k get pods -n dev -o wide
k get svc -n dev

# Check labels
k get pods -n dev --show-labels
k get pods -n dev -l app=event-api
```

---

## Test

### Option 1: Port Forward

```bash
k port-forward svc/event-api 8080:80 -n dev

# In another terminal:
curl localhost:8080
# Expected: {"message":"Hello from CKAD Event API!","service":"event-api","version":"v1"}

curl localhost:8080/health
# Expected: {"status":"healthy"}
```

### Option 2: From Another Pod

```bash
# Create test pod
k run test-pod --image=curlimages/curl -n dev -- sleep 3600

# Exec into it
k exec -it test-pod -n dev -- sh

# Inside pod:
curl http://event-api
curl http://event-api.dev.svc.cluster.local
exit

# Cleanup
k delete pod test-pod -n dev
```

---

## Common Exam Tasks

### 1. Scale Deployment

```bash
# Imperative
k scale deployment event-api --replicas=3 -n dev

# Verify
k get pods -n dev -l app=event-api

# Declarative (exam prefers this)
k edit deployment event-api -n dev
# Change replicas: 3
```

### 2. Update Environment Variable

```bash
k set env deployment/event-api MESSAGE="Updated message!" -n dev

# Verify rollout
k rollout status deployment/event-api -n dev

# Test
k port-forward svc/event-api 8080:80 -n dev
curl localhost:8080
```

### 3. View Rollout History

```bash
k rollout history deployment/event-api -n dev

# Rollback if needed
k rollout undo deployment/event-api -n dev
```

### 4. Get Specific Pod Info

```bash
# Get pod by label
k get pods -n dev -l app=event-api

# Get pod YAML
k get pod <POD_NAME> -n dev -o yaml

# Describe pod
k describe pod <POD_NAME> -n dev

# Get logs
k logs -f deployment/event-api -n dev
```

---

## Debugging Scenarios

### Scenario 1: Pods Not Starting

```bash
k get pods -n dev
# STATUS: ImagePullBackOff or ErrImagePull

k describe pod <POD_NAME> -n dev
# Look for: Failed to pull image "event-api:v1"

# Fix: Ensure image is available in cluster
# (Push to registry or load locally)
```

### Scenario 2: Service Not Routing

```bash
k get endpoints -n dev
# If endpoints are empty, selector doesn't match pod labels

k get pods --show-labels -n dev
k get svc event-api -n dev -o yaml

# Fix: Ensure service selector matches pod labels
```

### Scenario 3: Wrong Port

```bash
curl localhost:8080
# Connection refused

k get svc event-api -n dev
# Check port vs targetPort

k get pods -n dev -o yaml | grep containerPort
# Ensure targetPort matches containerPort
```

---

## Speed Commands (Exam Practice)

```bash
# Create deployment from scratch
k create deployment event-api --image=event-api:v1 -n dev --dry-run=client -o yaml > deploy.yaml

# Expose deployment
k expose deployment event-api --port=80 --target-port=8080 -n dev --dry-run=client -o yaml > svc.yaml

# Edit deployment
k edit deploy event-api -n dev

# Delete and recreate (speed practice)
k delete -f deployment.yaml -f service.yaml
k apply -f deployment.yaml -f service.yaml
```

---

## Verification Checklist

- [ ] Image built and available in cluster
- [ ] Deployment created with 2 replicas
- [ ] Pods are Running
- [ ] Service created (ClusterIP)
- [ ] Can curl service from test pod
- [ ] Labels are correct
- [ ] Environment variable MESSAGE is injected
- [ ] Can scale deployment
- [ ] Can view logs

---

## Key Takeaways

1. **Labels are Everything**: They connect Deployments → Pods → Services
2. **Selectors Must Match**: Service selector = Pod labels
3. **Ports Matter**: containerPort → targetPort → port
4. **Resource Limits**: Always set them (exam favorites)
5. **imagePullPolicy**: Use `Never` for local images

---

## Next: Day 3

Tomorrow you'll externalize configuration using:
- ConfigMaps
- Secrets
- Environment variables
- Mounted volumes

**Estimated time:** 45-60 minutes
