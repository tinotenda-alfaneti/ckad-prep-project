# Day 6 - Multi-Container Pods

## Objectives
- Implement init containers
- Implement sidecar containers
- Share volumes between containers
- Understand container startup order

## CKAD Skills Covered
- Multi-Container Pods (10%)
- Pod Design

---

## Init Containers

Init containers run **before** app containers and must complete successfully.

**Common use cases:**
- Wait for dependencies (database, services)
- Pre-populate data
- Setup configuration
- Security checks

### Example: Wait for Redis

**File: `pod-with-init.yaml`**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: worker-with-init
  namespace: dev
  labels:
    app: worker
spec:
  initContainers:
  # Init container 1: Wait for Redis
  - name: wait-for-redis
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      echo "Waiting for Redis to be ready..."
      until nc -z redis 6379; do
        echo "Redis not available, waiting..."
        sleep 2
      done
      echo "Redis is ready!"
  
  # Init container 2: Pre-populate config
  - name: setup-config
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      echo "Setting up configuration..."
      echo "worker_id=$(date +%s)" > /config/worker.conf
      echo "Config created!"
    volumeMounts:
    - name: config
      mountPath: /config
  
  containers:
  # Main application container
  - name: worker
    image: worker:v1
    imagePullPolicy: Never
    envFrom:
    - configMapRef:
        name: worker-config
    volumeMounts:
    - name: config
      mountPath: /config
    - name: output
      mountPath: /data
  
  volumes:
  - name: config
    emptyDir: {}
  - name: output
    emptyDir: {}
```

**Key Concepts:**
- Init containers run **sequentially** (one after another)
- All init containers must succeed before app containers start
- Init containers can use different images
- Shared volumes allow data transfer between init and app containers

---

## Sidecar Containers

Sidecar containers run **alongside** the main container.

**Common use cases:**
- Log shipping
- Metrics collection
- Proxies (service mesh)
- File syncing

### Example: Log Shipper Sidecar

**File: `pod-with-sidecar.yaml`**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: worker-with-sidecar
  namespace: dev
  labels:
    app: worker
spec:
  containers:
  # Main application container
  - name: worker
    image: worker:v1
    imagePullPolicy: Never
    envFrom:
    - configMapRef:
        name: worker-config
    volumeMounts:
    - name: logs
      mountPath: /var/log/worker
    - name: output
      mountPath: /data
    # Modified to log to file
    command:
    - sh
    - -c
    - |
      python -u worker.py 2>&1 | tee /var/log/worker/app.log
  
  # Sidecar: Log processor
  - name: log-processor
    image: busybox:1.36
    command:
    - sh
    - -c
    - |
      echo "Log processor started"
      while true; do
        if [ -f /logs/app.log ]; then
          # Count lines every 10 seconds
          LINES=$(wc -l < /logs/app.log)
          echo "[LOG-PROCESSOR] Total log lines: $LINES"
        fi
        sleep 10
      done
    volumeMounts:
    - name: logs
      mountPath: /logs
  
  volumes:
  - name: logs
    emptyDir: {}
  - name: output
    emptyDir: {}
```

---

## Deployment with Init + Sidecar

**File: `deployment-multicontainer.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker-multi
  namespace: dev
spec:
  replicas: 1
  selector:
    matchLabels:
      app: worker-multi
  template:
    metadata:
      labels:
        app: worker-multi
    spec:
      initContainers:
      # Wait for Redis to be available
      - name: wait-redis
        image: busybox:1.36
        command:
        - sh
        - -c
        - |
          echo "Checking Redis availability..."
          until nc -z redis 6379; do
            echo "Waiting for redis:6379..."
            sleep 2
          done
          echo "Redis is ready!"
      
      containers:
      # Main worker container
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
              fieldPath: metadata.name
        volumeMounts:
        - name: shared-logs
          mountPath: /var/log
        - name: output
          mountPath: /data
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
      
      # Sidecar: Log tailer
      - name: log-tailer
        image: busybox:1.36
        command:
        - sh
        - -c
        - |
          echo "Log tailer started"
          touch /logs/worker.log
          tail -f /logs/worker.log
        volumeMounts:
        - name: shared-logs
          mountPath: /logs
        resources:
          requests:
            memory: "32Mi"
            cpu: "50m"
          limits:
            memory: "64Mi"
            cpu: "100m"
      
      volumes:
      - name: shared-logs
        emptyDir: {}
      - name: output
        emptyDir: {}
```

---

## Deploy and Test

```bash
cd ~/projects/homelab/ckad-project/day06-multicontainer/k8s

# Deploy pod with init container
k apply -f pod-with-init.yaml

# Watch init containers
k get pod worker-with-init -n dev -w

# View init container logs
k logs worker-with-init -n dev -c wait-for-redis
k logs worker-with-init -n dev -c setup-config

# View main container logs
k logs worker-with-init -n dev -c worker

# Check config file was created
k exec worker-with-init -n dev -c worker -- cat /config/worker.conf
```

### Test Sidecar

```bash
# Deploy pod with sidecar
k apply -f pod-with-sidecar.yaml

# View main container logs
k logs worker-with-sidecar -n dev -c worker

# View sidecar logs
k logs worker-with-sidecar -n dev -c log-processor -f

# See both containers running
k get pod worker-with-sidecar -n dev -o jsonpath='{.spec.containers[*].name}'
```

### Test Deployment

```bash
# Deploy multi-container deployment
k apply -f deployment-multicontainer.yaml

# Watch pod startup
k get pods -n dev -l app=worker-multi -w

# View init container logs
POD=$(k get pod -n dev -l app=worker-multi -o jsonpath='{.items[0].metadata.name}')
k logs $POD -n dev -c wait-redis

# View sidecar logs
k logs $POD -n dev -c log-tailer -f
```

---

## Common Exam Tasks

### Task 1: Add Init Container to Existing Deployment

```bash
# Get current deployment
k get deployment worker -n dev -o yaml > deployment.yaml

# Edit to add initContainers section (before containers:)
k edit deployment worker -n dev
```

```yaml
spec:
  template:
    spec:
      initContainers:
      - name: init-check
        image: busybox:1.36
        command: ['sh', '-c', 'echo Init complete!']
      containers:
      # ... existing containers
```

### Task 2: Debug Init Container Failure

```bash
k get pods -n dev
# STATUS: Init:Error or Init:CrashLoopBackOff

# View init container logs
k logs <POD_NAME> -n dev -c <INIT_CONTAINER_NAME>

# Describe to see events
k describe pod <POD_NAME> -n dev

# Common issues:
# - Init container command fails
# - Waiting for service that doesn't exist
# - Wrong image
```

### Task 3: View All Container Logs

```bash
# List all containers in pod
k get pod <POD_NAME> -n dev -o jsonpath='{.spec.containers[*].name}'

# View logs from all containers
k logs <POD_NAME> -n dev --all-containers=true

# Follow logs from specific container
k logs <POD_NAME> -n dev -c <CONTAINER_NAME> -f

# Previous container logs (after restart)
k logs <POD_NAME> -n dev -c <CONTAINER_NAME> --previous
```

### Task 4: Exec into Specific Container

```bash
# Exec into sidecar
k exec -it <POD_NAME> -n dev -c log-tailer -- sh

# Exec into main container
k exec -it <POD_NAME> -n dev -c worker -- sh
```

---

## Ambassador Pattern

Sidecar that proxies network traffic.

```yaml
containers:
- name: app
  image: myapp:v1
  env:
  - name: DB_HOST
    value: "localhost"  # Talk to ambassador
  - name: DB_PORT
    value: "5432"

- name: db-proxy
  image: haproxy:2.8
  # Proxies localhost:5432 -> real-db.prod.svc:5432
```

**Use case:** Decouple app from external service location

---

## Adapter Pattern

Sidecar that transforms data.

```yaml
containers:
- name: app
  image: myapp:v1
  volumeMounts:
  - name: logs
    mountPath: /var/log

- name: log-adapter
  image: fluentd:v1
  # Reads /logs/*.log
  # Transforms to JSON
  # Ships to Elasticsearch
  volumeMounts:
  - name: logs
    mountPath: /logs
```

**Use case:** Standardize log formats, metrics

---

## Speed Commands (Exam Practice)

```bash
# Create pod with init container
k run mypod --image=nginx --dry-run=client -o yaml > pod.yaml
# Edit to add initContainers section

# Quick init container check
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: init-demo
spec:
  initContainers:
  - name: init
    image: busybox
    command: ['sh', '-c', 'echo hello']
  containers:
  - name: main
    image: nginx
EOF

k logs init-demo -c init
k logs init-demo -c main

k delete pod init-demo
```

---

**If any init container fails:**
- Pod restarts from first init container (based on restartPolicy)

**Sidecar containers:**
- Start with main containers
- Run until pod deletion
- Should handle graceful shutdown

---


## Key Takeaways

1. **Init containers**: Run sequentially before main containers
2. **Sidecars**: Run alongside main container
3. **Shared volumes**: `emptyDir` for inter-container communication
4. **Container names**: Use `-c <name>` for logs, exec
5. **Patterns**: Init (setup), Sidecar (auxiliary), Ambassador (proxy), Adapter (transform)
6. **Debugging**: Check init container logs first if pod stuck in `Init:*` state
7. **Exam tip**: Know how to add init containers to existing deployments

