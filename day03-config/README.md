# Day 3 - Configuration & Secrets

## Objectives
- Decouple configuration from container images
- Create and use ConfigMaps
- Create and use Secrets
- Inject config via environment variables
- Mount config as files

## CKAD Skills Covered
- Configuration (18%)

---

## Why Configuration Management?

**Anti-pattern:** Hardcoding values in images
```python
MESSAGE = "Hello from prod!"  # ❌ Requires rebuild for different envs
```

**Best practice:** External configuration
```python
MESSAGE = os.getenv('MESSAGE')  # ✅ Configure at runtime
```

---

## ConfigMaps

### Create ConfigMap (Imperative)

```bash
# From literal values
k create configmap api-config \
  --from-literal=MESSAGE="Hello from ConfigMap!" \
  --from-literal=LOG_LEVEL="debug" \
  -n dev

# From file
echo "Hello from file!" > message.txt
k create configmap api-config-file \
  --from-file=message.txt \
  -n dev

# From env file
cat <<EOF > app.env
MESSAGE=Hello from env file!
LOG_LEVEL=info
EOF

k create configmap api-config-env \
  --from-env-file=app.env \
  -n dev

# View ConfigMaps
k get configmaps -n dev
k describe configmap api-config -n dev
k get configmap api-config -n dev -o yaml
```

### Create ConfigMap (Declarative)

**File: `configmap.yaml`**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: dev
data:
  MESSAGE: "Hello from CKAD ConfigMap!"
  LOG_LEVEL: "info"
  MAX_WORKERS: "4"
  # Can also store file content
  app.properties: |
    server.port=8080
    server.host=0.0.0.0
    cache.enabled=true
```

```bash
k apply -f configmap.yaml
```

---

## Secrets

### Create Secret (Imperative)

```bash
# From literal values
k create secret generic api-secret \
  --from-literal=API_TOKEN="super-secret-token-123" \
  --from-literal=DB_PASSWORD="postgres123" \
  -n dev

# From file
echo -n "my-secret-token" > api-token.txt
k create secret generic api-secret-file \
  --from-file=token=api-token.txt \
  -n dev

# View secrets (values are base64 encoded)
k get secrets -n dev
k describe secret api-secret -n dev
k get secret api-secret -n dev -o yaml

# Decode secret
k get secret api-secret -n dev -o jsonpath='{.data.API_TOKEN}' | base64 -d
```

### Create Secret (Declarative)

**File: `secret.yaml`**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secret
  namespace: dev
type: Opaque
data:
  # Values must be base64 encoded
  API_TOKEN: c3VwZXItc2VjcmV0LXRva2VuLTEyMw==  # super-secret-token-123
  DB_PASSWORD: cG9zdGdyZXMxMjM=  # postgres123
```

**Encoding values:**
```bash
echo -n "super-secret-token-123" | base64
# Output: c3VwZXItc2VjcmV0LXRva2VuLTEyMw==
```

**Alternative (using stringData - no encoding needed):**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secret
  namespace: dev
type: Opaque
stringData:  # Note: stringData, not data
  API_TOKEN: "super-secret-token-123"
  DB_PASSWORD: "postgres123"
```

```bash
k apply -f secret.yaml
```

---

## Using ConfigMaps & Secrets

### Method 1: Environment Variables (All Keys)

**File: `deployment-envfrom.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-api
  namespace: dev
spec:
  replicas: 2
  selector:
    matchLabels:
      app: event-api
  template:
    metadata:
      labels:
        app: event-api
    spec:
      containers:
      - name: api
        image: event-api:v1
        imagePullPolicy: Never
        ports:
        - containerPort: 8080
        # Inject ALL keys from ConfigMap
        envFrom:
        - configMapRef:
            name: api-config
        # Inject ALL keys from Secret
        - secretRef:
            name: api-secret
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

### Method 2: Environment Variables (Specific Keys)

**File: `deployment-env.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-api
  namespace: dev
spec:
  replicas: 2
  selector:
    matchLabels:
      app: event-api
  template:
    metadata:
      labels:
        app: event-api
    spec:
      containers:
      - name: api
        image: event-api:v1
        imagePullPolicy: Never
        ports:
        - containerPort: 8080
        env:
        # From ConfigMap
        - name: MESSAGE
          valueFrom:
            configMapKeyRef:
              name: api-config
              key: MESSAGE
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: api-config
              key: LOG_LEVEL
        # From Secret
        - name: API_TOKEN
          valueFrom:
            secretKeyRef:
              name: api-secret
              key: API_TOKEN
        # Literal value (still works)
        - name: APP_NAME
          value: "event-api"
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

### Method 3: Volume Mounts (Files)

**File: `deployment-volume.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: event-api
  namespace: dev
spec:
  replicas: 2
  selector:
    matchLabels:
      app: event-api
  template:
    metadata:
      labels:
        app: event-api
    spec:
      containers:
      - name: api
        image: event-api:v1
        imagePullPolicy: Never
        ports:
        - containerPort: 8080
        volumeMounts:
        # Mount ConfigMap as files
        - name: config-volume
          mountPath: /config
          readOnly: true
        # Mount Secret as files
        - name: secret-volume
          mountPath: /secrets
          readOnly: true
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
      volumes:
      # ConfigMap volume
      - name: config-volume
        configMap:
          name: api-config
      # Secret volume
      - name: secret-volume
        secret:
          secretName: api-secret
```

**Result inside container:**
```bash
k exec -it <POD_NAME> -n dev -- sh

ls /config
# MESSAGE  LOG_LEVEL  MAX_WORKERS  app.properties

cat /config/MESSAGE
# Hello from CKAD ConfigMap!

cat /config/app.properties
# server.port=8080
# server.host=0.0.0.0
# cache.enabled=true

ls /secrets
# API_TOKEN  DB_PASSWORD

cat /secrets/API_TOKEN
# super-secret-token-123
```

### Method 4: Volume Mounts (Specific Keys)

```yaml
volumes:
- name: config-volume
  configMap:
    name: api-config
    items:  # Only mount specific keys
    - key: MESSAGE
      path: message.txt  # Custom filename
    - key: app.properties
      path: config/app.properties  # Subdirectory
```

---

## Deploy and Test

```bash
cd ~/projects/homelab/ckad-project/day03-config/k8s

# Create ConfigMap and Secret
k apply -f configmap.yaml
k apply -f secret.yaml

# Deploy (choose one method)
k apply -f deployment-envfrom.yaml

# Verify
k get pods -n dev
k describe pod <POD_NAME> -n dev

# Test environment variables
k exec -it <POD_NAME> -n dev -- printenv | grep -E 'MESSAGE|API_TOKEN|LOG_LEVEL'

# Test via API
k port-forward svc/event-api 8080:80 -n dev
curl localhost:8080
# Should see MESSAGE from ConfigMap
```

---

## Update ConfigMap/Secret

### ConfigMaps

```bash
# Edit ConfigMap
k edit configmap api-config -n dev
# Change MESSAGE value

# ConfigMap updates DON'T automatically restart pods
# You must force a rollout:
k rollout restart deployment event-api -n dev

# Verify new value
k exec -it <POD_NAME> -n dev -- printenv MESSAGE
```

**Exam tip:** Mounted ConfigMaps/Secrets update automatically (after ~60s), but env vars require pod restart.

### Secrets

```bash
# Update secret
k create secret generic api-secret \
  --from-literal=API_TOKEN="new-token-456" \
  --dry-run=client -o yaml | k apply -f - -n dev

# Restart pods
k rollout restart deployment event-api -n dev
```

---

## Common Exam Tasks

### Task 1: Create ConfigMap from Directory

```bash
mkdir config-files
echo "value1" > config-files/key1.txt
echo "value2" > config-files/key2.txt

k create configmap dir-config --from-file=config-files/ -n dev

# Verify
k describe configmap dir-config -n dev
```

### Task 2: Create Secret from TLS Cert

```bash
# Generate self-signed cert (for practice)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt -subj "/CN=example.com"

# Create TLS secret
k create secret tls tls-secret \
  --cert=tls.crt \
  --key=tls.key \
  -n dev

# Verify
k describe secret tls-secret -n dev
```

### Task 3: Debug Missing ConfigMap

```bash
k get pods -n dev
# STATUS: CreateContainerConfigError

k describe pod <POD_NAME> -n dev
# Error: configmap "api-config" not found

# Fix: Create the ConfigMap
k apply -f configmap.yaml
# Pod will auto-recover
```

### Task 4: Update Running Deployment with New Config

```bash
# Scenario: Add new env var from ConfigMap

# 1. Update ConfigMap
k create configmap api-config \
  --from-literal=MESSAGE="Updated!" \
  --from-literal=NEW_VAR="new-value" \
  --dry-run=client -o yaml | k apply -f - -n dev

# 2. Patch deployment to add new env var
k set env deployment/event-api --from=configmap/api-config -n dev

# Or edit directly
k edit deployment event-api -n dev
```

---

## Speed Commands (Exam Practice)

```bash
# Create ConfigMap
k create cm myconfig --from-literal=key=value -n dev --dry-run=client -o yaml > cm.yaml

# Create Secret
k create secret generic mysecret --from-literal=password=secret -n dev --dry-run=client -o yaml > secret.yaml

# Add ConfigMap to existing deployment
k set env deployment/myapp --from=configmap/myconfig -n dev

# Add Secret to existing deployment
k set env deployment/myapp --from=secret/mysecret -n dev

# Delete ConfigMap (pods will fail if they depend on it)
k delete cm api-config -n dev
```

---

## Verification Checklist

- [ ] ConfigMap created with multiple keys
- [ ] Secret created with base64-encoded values
- [ ] Deployment uses envFrom for all keys
- [ ] Deployment uses env for specific keys
- [ ] ConfigMap mounted as volume
- [ ] Secret mounted as volume
- [ ] Can read config files inside pod
- [ ] Can update ConfigMap and restart pods
- [ ] Understand env vars vs mounted files

---

## Key Takeaways

1. **ConfigMaps**: Non-sensitive configuration
2. **Secrets**: Sensitive data (base64 encoded, NOT encrypted by default)
3. **envFrom**: All keys → environment variables
4. **env + valueFrom**: Specific keys → environment variables
5. **volumeMounts**: Keys → files
6. **Updates**: env vars need pod restart, mounted files auto-update
7. **Exam tip**: Use `--dry-run=client -o yaml` to generate YAML fast

---

## Next: Day 4

Tomorrow you'll add **Redis** with persistent storage:
- StatefulSets
- PersistentVolumeClaims (PVCs)
- Data persistence

**Estimated time:** 45-60 minutes
