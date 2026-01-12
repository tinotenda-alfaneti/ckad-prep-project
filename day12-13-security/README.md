# Day 12-13 - Security (SecurityContexts & RBAC)

## Day 12: Security Contexts

### Objectives
- Run containers as non-root
- Set filesystem permissions
- Configure capabilities

---

### Pod-Level Security Context

**File: `pod-security.yaml`**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
  namespace: dev
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
  containers:
  - name: app
    image: busybox:1.36
    command: ['sh', '-c', 'sleep 3600']
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
```

---

### Non-Root User

**File: `deployment-nonroot.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-worker
  namespace: dev
spec:
  replicas: 1
  selector:
    matchLabels:
      app: secure-worker
  template:
    metadata:
      labels:
        app: secure-worker
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: worker
        image: worker:v1
        imagePullPolicy: Never
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
```

---

### Read-Only Filesystem

```yaml
containers:
- name: app
  image: nginx
  securityContext:
    readOnlyRootFilesystem: true
  volumeMounts:
  - name: cache
    mountPath: /var/cache/nginx
  - name: run
    mountPath: /var/run
volumes:
- name: cache
  emptyDir: {}
- name: run
  emptyDir: {}
```

---

## Day 13: ServiceAccounts & RBAC

### Create ServiceAccount

**File: `serviceaccount.yaml`**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: worker-sa
  namespace: dev
```

### Role (Namespace-scoped)

**File: `role.yaml`**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: dev
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
```

### RoleBinding

**File: `rolebinding.yaml`**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: dev
subjects:
- kind: ServiceAccount
  name: worker-sa
  namespace: dev
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### Use ServiceAccount in Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: worker-with-sa
  namespace: dev
spec:
  serviceAccountName: worker-sa
  containers:
  - name: worker
    image: worker:v1
```

---

### ClusterRole (Cluster-wide)

**File: `clusterrole.yaml`**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: secret-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
```

### ClusterRoleBinding

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-secrets-global
subjects:
- kind: ServiceAccount
  name: worker-sa
  namespace: dev
roleRef:
  kind: ClusterRole
  name: secret-reader
  apiGroup: rbac.authorization.k8s.io
```

---

### Speed Commands

```bash
# Create ServiceAccount
k create sa mysa -n dev

# Create Role
k create role pod-reader --verb=get,list --resource=pods -n dev

# Create RoleBinding
k create rolebinding read-pods --role=pod-reader --serviceaccount=dev:mysa -n dev

# Create ClusterRole
k create clusterrole secret-reader --verb=get,list --resource=secrets

# Create ClusterRoleBinding
k create clusterrolebinding read-secrets --clusterrole=secret-reader --serviceaccount=dev:mysa
```

---

### Test RBAC

```bash
# Create pod with ServiceAccount
k run test --image=nginx --serviceaccount=worker-sa -n dev

# Check permissions from inside pod
k exec test -n dev -- kubectl auth can-i get pods
# Should return: yes

k exec test -n dev -- kubectl auth can-i delete pods
# Should return: no
```

---

## Key Takeaways

### Security Contexts
1. **runAsUser**: UID to run container
2. **runAsNonRoot**: Enforce non-root
3. **readOnlyRootFilesystem**: Immutable filesystem
4. **allowPrivilegeEscalation**: Prevent privilege escalation
5. **capabilities**: Linux capabilities (add/drop)

### RBAC
1. **ServiceAccount**: Pod identity
2. **Role**: Namespace permissions
3. **ClusterRole**: Cluster-wide permissions
4. **RoleBinding**: Attach Role to ServiceAccount
5. **ClusterRoleBinding**: Attach ClusterRole to ServiceAccount
6. **Verbs**: get, list, watch, create, update, patch, delete
