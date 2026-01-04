# Day 4 - Redis (Stateful Component)

## Objectives
- Deploy a stateful application (Redis)
- Create and use PersistentVolumeClaims (PVCs)
- Understand volume lifecycle
- Test data persistence across pod restarts

## CKAD Skills Covered
- State Persistence (8%)
- Volumes

---

## Why Redis?

Redis serves as our message queue and cache:
- **Stateful**: Data must survive pod restarts
- **Requires Storage**: PersistentVolume for data directory
- **Service Discovery**: Other services connect via DNS

---

## PersistentVolumeClaim

**File: `pvc.yaml`**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: dev
spec:
  accessModes:
    - ReadWriteOnce  # RWO = single node read/write
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard  # Default storage class
```

**Key Concepts:**
- **ReadWriteOnce (RWO)**: Volume can be mounted read-write by a single node
- **ReadWriteMany (RWX)**: Volume can be mounted read-write by many nodes
- **ReadOnlyMany (ROX)**: Volume can be mounted read-only by many nodes
- **storageClassName**: Defines how storage is provisioned

```bash
# Apply PVC
k apply -f pvc.yaml

# Check PVC status
k get pvc -n dev
# STATUS: Bound (storage provisioned)

# Check underlying PV
k get pv
# Shows auto-created PersistentVolume
```

---

## Redis Deployment

**File: `deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: dev
  labels:
    app: redis
spec:
  replicas: 1  # Redis typically runs as single instance
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
          name: redis
        volumeMounts:
        - name: redis-storage
          mountPath: /data  # Redis data directory
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc  # References the PVC
```

**Alternative: StatefulSet** (more common for stateful apps)

**File: `statefulset.yaml`**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: dev
spec:
  serviceName: redis  # Headless service name
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
          name: redis
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
  volumeClaimTemplates:  # StatefulSet creates PVCs automatically
  - metadata:
      name: redis-storage
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 1Gi
      storageClassName: standard
```

**Deployment vs StatefulSet:**
- **Deployment**: For stateless apps (or single-replica stateful)
- **StatefulSet**: For stateful apps needing stable network identity, ordered deployment

---

## Redis Service

**File: `service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: dev
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
    protocol: TCP
  type: ClusterIP
```

**For StatefulSet, also create Headless Service:**

**File: `headless-service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: dev
spec:
  clusterIP: None  # Headless service
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

---

## Deploy

```bash
cd ~/projects/homelab/ckad-project/day04-redis/k8s

# Option 1: Deployment with PVC
k apply -f pvc.yaml
k apply -f deployment.yaml
k apply -f service.yaml

# Option 2: StatefulSet (manages PVC automatically)
k apply -f statefulset.yaml
k apply -f headless-service.yaml

# Verify
k get pvc -n dev
k get pods -n dev
k get svc -n dev
```

---

## Test Persistence

### Write Data to Redis

```bash
# Connect to Redis
k exec -it deployment/redis -n dev -- redis-cli

# Inside redis-cli:
SET mykey "Hello CKAD!"
SET counter 42
GET mykey
# Output: "Hello CKAD!"

KEYS *
# Output: 1) "mykey" 2) "counter"

exit
```

### Delete Pod (Simulate Failure)

```bash
# Delete the pod
k delete pod -l app=redis -n dev

# Wait for new pod to start
k get pods -n dev -w

# Reconnect to new pod
k exec -it deployment/redis -n dev -- redis-cli

# Data should still exist!
GET mykey
# Output: "Hello CKAD!"

GET counter
# Output: "42"

exit
```

**Why?** The PVC persists across pod restarts. New pod mounts the same volume.

### Delete Deployment (Keep PVC)

```bash
# Delete deployment
k delete deployment redis -n dev

# PVC still exists
k get pvc -n dev
# STATUS: Bound

# Recreate deployment
k apply -f deployment.yaml

# Reconnect
k exec -it deployment/redis -n dev -- redis-cli
GET mykey
# Still there!
```

### Delete PVC (Data Loss)

```bash
# Delete PVC
k delete pvc redis-pvc -n dev

# This deletes the underlying PV and data!
k get pv
# PV is also deleted (for dynamic provisioning)

# Recreate
k apply -f pvc.yaml
k apply -f deployment.yaml

# Data is gone
k exec -it deployment/redis -n dev -- redis-cli
KEYS *
# Empty
```

---

## Common Exam Tasks

### Task 1: Check Storage Class

```bash
# List storage classes
k get storageclass

# Describe storage class
k describe storageclass standard

# Set default storage class
k patch storageclass standard -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

### Task 2: Resize PVC

```bash
# Edit PVC (if storage class allows expansion)
k edit pvc redis-pvc -n dev
# Change: storage: 1Gi → storage: 2Gi

# Check status
k get pvc redis-pvc -n dev
# May need to restart pod for some storage providers
```

### Task 3: Debug Pending PVC

```bash
k get pvc -n dev
# STATUS: Pending

k describe pvc redis-pvc -n dev
# Look for: no persistent volumes available, storage class not found

# Check PVs
k get pv

# Check storage class exists
k get storageclass
```

### Task 4: Use EmptyDir Volume (Non-Persistent)

```yaml
# For temporary storage (lost on pod deletion)
volumes:
- name: temp-storage
  emptyDir: {}
```

**Use cases:**
- Cache
- Temporary processing
- Shared volume between containers in same pod

---

## Volume Types Summary

| Type | Persistence | Use Case | Exam Frequency |
|------|-------------|----------|----------------|
| emptyDir | Pod lifetime | Temporary, cache | High |
| hostPath | Node lifetime | Node-specific data | Medium |
| PVC | Cluster lifetime | Stateful apps | High |
| ConfigMap | N/A | Config files | High |
| Secret | N/A | Credentials | High |

---

## Test from Another Service

```bash
# Create test pod with redis-cli
k run redis-test --image=redis:7-alpine -n dev -- sleep 3600

# Connect to Redis service
k exec -it redis-test -n dev -- redis-cli -h redis

# Inside redis-cli:
PING
# Output: PONG

SET testkey "Service discovery works!"
GET testkey

exit

# Cleanup
k delete pod redis-test -n dev
```

**Key:** Service discovery via DNS name `redis` (or `redis.dev.svc.cluster.local`)

---

## Speed Commands (Exam Practice)

```bash
# Create PVC
k create -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
EOF

# Create pod with PVC
k run mypod --image=nginx --dry-run=client -o yaml > pod.yaml
# Edit pod.yaml to add volume and volumeMount

# Quick pod with emptyDir
k run tmp-pod --image=busybox --dry-run=client -o yaml -- sleep 3600 > pod.yaml
# Add emptyDir volume to pod.yaml
```

---

## Verification Checklist

- [ ] PVC created and bound
- [ ] PV auto-created by storage class
- [ ] Redis deployment running
- [ ] Can write data to Redis
- [ ] Data persists after pod deletion
- [ ] Data persists after deployment deletion
- [ ] Service discovery works (redis-cli -h redis)
- [ ] Understand PVC lifecycle

---

## Key Takeaways

1. **PVCs** abstract storage from pods
2. **Storage Classes** provision storage dynamically
3. **accessModes**: RWO (most common), RWX, ROX
4. **volumeMounts**: Connect PVC to container filesystem
5. **Data persistence**: Survives pod/deployment deletion, not PVC deletion
6. **StatefulSets**: Use `volumeClaimTemplates` for automatic PVC creation
7. **Exam tip**: Know how to debug Pending PVCs (check PV availability, storage class)

---
