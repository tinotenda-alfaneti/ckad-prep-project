# Day 14 - Chaos & Debugging

## Objectives
- Debug common Kubernetes issues
- Practice troubleshooting workflow
- Build exam-day confidence

---

## Broken Scenarios

### Scenario 1: ImagePullBackOff

**File: `broken-image.yaml`**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: broken-image
  namespace: dev
spec:
  containers:
  - name: app
    image: nginx:nonexistent-tag
```

**Debug:**
```bash
k apply -f broken-image.yaml
k get pods -n dev
# STATUS: ImagePullBackOff

k describe pod broken-image -n dev
# Events: Failed to pull image

# Fix: Use correct image tag
k delete pod broken-image -n dev
# Edit YAML with nginx:latest
```

---

### Scenario 2: CrashLoopBackOff

**File: `crash-loop.yaml`**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: crash-loop
  namespace: dev
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ['sh', '-c', 'exit 1']
```

**Debug:**
```bash
k apply -f crash-loop.yaml
k get pods -n dev -w
# STATUS: CrashLoopBackOff

k logs crash-loop -n dev
# Shows exit 1

k logs crash-loop -n dev --previous
# Shows previous attempt

# Fix: Change command to 'sleep 3600'
```

---

### Scenario 3: Wrong Port

**File: `wrong-port.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wrong-port-app
  namespace: dev
spec:
  replicas: 1
  selector:
    matchLabels:
      app: wrong-port
  template:
    metadata:
      labels:
        app: wrong-port
    spec:
      containers:
      - name: app
        image: nginx
        ports:
        - containerPort: 8080  # WRONG! Nginx uses 80
---
apiVersion: v1
kind: Service
metadata:
  name: wrong-port-svc
  namespace: dev
spec:
  selector:
    app: wrong-port
  ports:
  - port: 80
    targetPort: 8080  # WRONG!
```

**Debug:**
```bash
k apply -f wrong-port.yaml
k port-forward svc/wrong-port-svc 8080:80 -n dev
curl localhost:8080
# Connection refused

k get endpoints wrong-port-svc -n dev
# Shows IP but wrong port

# Fix: Change targetPort to 80
```

---

### Scenario 4: Missing ConfigMap

**File: `missing-cm.yaml`**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: missing-cm
  namespace: dev
spec:
  containers:
  - name: app
    image: nginx
    envFrom:
    - configMapRef:
        name: does-not-exist
```

**Debug:**
```bash
k apply -f missing-cm.yaml
k get pods -n dev
# STATUS: CreateContainerConfigError

k describe pod missing-cm -n dev
# Events: configmap "does-not-exist" not found

# Fix: Create the ConfigMap
k create cm does-not-exist --from-literal=key=value -n dev
# Pod auto-recovers
```

---

### Scenario 5: Selector Mismatch

**File: `selector-mismatch.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mismatch-deploy
  namespace: dev
spec:
  replicas: 2
  selector:
    matchLabels:
      app: myapp  # OK
  template:
    metadata:
      labels:
        app: wrong-label  # WRONG!
    spec:
      containers:
      - name: nginx
        image: nginx
```

**Debug:**
```bash
k apply -f selector-mismatch.yaml
# Error: selector does not match template labels

# Fix: Ensure selector.matchLabels == template.metadata.labels
```

---

### Scenario 6: Resource Limits

**File: `oom.yaml`**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: oom-pod
  namespace: dev
spec:
  containers:
  - name: app
    image: polinux/stress
    command: ['stress', '--vm', '1', '--vm-bytes', '256M']
    resources:
      limits:
        memory: "128Mi"  # Too low!
```

**Debug:**
```bash
k apply -f oom.yaml
k get pods -n dev -w
# STATUS: OOMKilled

k describe pod oom-pod -n dev
# Last State: Terminated (OOMKilled)

# Fix: Increase memory limit
```

---

## Debugging Workflow (Exam Pattern)

```bash
# 1. Check pod status
k get pods -n dev

# 2. Describe pod (most important!)
k describe pod POD_NAME -n dev

# 3. Check logs
k logs POD_NAME -n dev
k logs POD_NAME -n dev --previous

# 4. Check events
k get events -n dev --sort-by='.lastTimestamp'

# 5. Exec into pod (if running)
k exec -it POD_NAME -n dev -- sh

# 6. Check service endpoints
k get endpoints SERVICE_NAME -n dev

# 7. Check resource definitions
k get deploy/pod/svc NAME -n dev -o yaml
```

---

## Common Error Patterns

| Status | Likely Cause | First Check |
|--------|--------------|-------------|
| ImagePullBackOff | Wrong image name/tag | describe pod |
| CrashLoopBackOff | App exits immediately | logs |
| CreateContainerConfigError | Missing ConfigMap/Secret | describe pod |
| Pending | No resources/PVC | describe pod |
| OOMKilled | Memory limit too low | describe pod |
| Error | Command failed | logs |
| Running (not Ready) | Readiness probe failing | describe pod |

---

## Quick Fixes

```bash
# Restart deployment
k rollout restart deployment NAME -n dev

# Scale to 0 and back
k scale deployment NAME --replicas=0 -n dev
k scale deployment NAME --replicas=2 -n dev

# Delete and recreate pod
k delete pod POD_NAME -n dev
# Deployment will recreate

# Force delete stuck pod
k delete pod POD_NAME -n dev --force --grace-period=0

# Edit live resource
k edit deployment NAME -n dev

# Replace from file
k replace --force -f file.yaml
```

---

## Practice Drills

1. **Deploy all broken scenarios**
2. **Debug each within 5 minutes**
3. **Fix without looking at solutions**
4. **Time yourself**

---

## Key Takeaways

1. **describe** is your best friend
2. **Check events first** (at bottom of describe output)
3. **Know common error patterns**
4. **Logs show application errors, describe shows Kubernetes errors**
5. **Service issues = check endpoints**
6. **Always verify labels and selectors match**

---

## Next: Day 15

Final CKAD simulation - timed challenges!

**Estimated time:** Variable (practice!)
