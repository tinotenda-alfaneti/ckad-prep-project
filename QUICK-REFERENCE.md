# CKAD Quick Reference Guide

## Essential kubectl Commands

### Resource Creation (Imperative)

```bash
# Pods
k run nginx --image=nginx
k run nginx --image=nginx --dry-run=client -o yaml > pod.yaml

# Deployments
k create deployment nginx --image=nginx --replicas=3
k create deployment nginx --image=nginx --dry-run=client -o yaml > deploy.yaml

# Services
k expose deployment nginx --port=80 --target-port=8080
k expose pod nginx --port=80 --type=NodePort
k create service clusterip myservice --tcp=80:8080

# ConfigMaps
k create cm myconfig --from-literal=key=value
k create cm myconfig --from-file=config.txt
k create cm myconfig --from-env-file=app.env

# Secrets
k create secret generic mysecret --from-literal=password=secret123
k create secret tls tls-secret --cert=tls.crt --key=tls.key

# Jobs
k create job myjob --image=busybox -- echo "Hello"

# CronJobs
k create cronjob mycron --image=busybox --schedule="*/5 * * * *" -- date

# ServiceAccounts
k create sa mysa

# Roles
k create role pod-reader --verb=get,list --resource=pods

# RoleBindings
k create rolebinding read-pods --role=pod-reader --serviceaccount=default:mysa
```

---

## Resource Management

```bash
# Get resources
k get pods
k get pods -o wide
k get pods -o yaml
k get pods --show-labels
k get pods -l app=nginx
k get all

# Describe (debugging)
k describe pod nginx

# Delete
k delete pod nginx
k delete -f file.yaml
k delete pod --all

# Edit
k edit deployment nginx

# Scale
k scale deployment nginx --replicas=5

# Labels
k label pod nginx env=prod
k label pod nginx env=prod --overwrite

# Annotations
k annotate pod nginx description="My pod"
```

---

## Logs & Debugging

```bash
# Logs
k logs nginx
k logs nginx -f                    # Follow
k logs nginx --previous            # Previous container
k logs nginx -c container-name     # Specific container
k logs -l app=nginx               # All pods with label

# Exec
k exec nginx -- ls /
k exec -it nginx -- /bin/bash

# Port forward
k port-forward pod/nginx 8080:80
k port-forward service/nginx 8080:80

# Copy files
k cp nginx:/path/to/file ./local-file
k cp ./local-file nginx:/path/to/file
```

---

## Updates & Rollouts

```bash
# Update image
k set image deployment/nginx nginx=nginx:1.24

# Update env
k set env deployment/nginx ENV=production

# Update resources
k set resources deployment/nginx --requests=cpu=100m,memory=64Mi --limits=cpu=200m,memory=128Mi

# Rollout status
k rollout status deployment/nginx

# Rollout history
k rollout history deployment/nginx

# Rollback
k rollout undo deployment/nginx
k rollout undo deployment/nginx --to-revision=2

# Restart
k rollout restart deployment/nginx
```

---

## Namespaces & Contexts

```bash
# Namespaces
k create namespace dev
k get pods -n dev
k get pods --all-namespaces
k delete namespace dev

# Context
k config current-context
k config get-contexts
k config set-context --current --namespace=dev
k config use-context my-context
```

---

## YAML Templates

### Pod with Everything

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp
  namespace: default
  labels:
    app: myapp
  annotations:
    description: "Full pod example"
spec:
  serviceAccountName: mysa
  securityContext:
    runAsUser: 1000
    runAsNonRoot: true
    fsGroup: 2000
  initContainers:
  - name: init
    image: busybox:1.36
    command: ['sh', '-c', 'echo "Init complete"']
  containers:
  - name: app
    image: nginx:1.24
    imagePullPolicy: IfNotPresent
    ports:
    - containerPort: 80
      name: http
    env:
    - name: ENV_VAR
      value: "value"
    - name: CONFIG_KEY
      valueFrom:
        configMapKeyRef:
          name: myconfig
          key: key
    - name: SECRET_KEY
      valueFrom:
        secretKeyRef:
          name: mysecret
          key: password
    envFrom:
    - configMapRef:
        name: myconfig
    - secretRef:
        name: mysecret
    volumeMounts:
    - name: config
      mountPath: /config
      readOnly: true
    - name: data
      mountPath: /data
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
    livenessProbe:
      httpGet:
        path: /health
        port: 80
      initialDelaySeconds: 10
      periodSeconds: 5
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /ready
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 3
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: false
      capabilities:
        drop:
        - ALL
  volumes:
  - name: config
    configMap:
      name: myconfig
  - name: data
    persistentVolumeClaim:
      claimName: mypvc
  - name: temp
    emptyDir: {}
  restartPolicy: Always
  nodeSelector:
    disktype: ssd
  tolerations:
  - key: "key"
    operator: "Equal"
    value: "value"
    effect: "NoSchedule"
```

### Deployment Template

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: default
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
        version: v1
    spec:
      containers:
      - name: app
        image: nginx:1.24
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

### Service Templates

```yaml
# ClusterIP
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
---
# NodePort
apiVersion: v1
kind: Service
metadata:
  name: myapp-nodeport
spec:
  type: NodePort
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080
---
# Headless
apiVersion: v1
kind: Service
metadata:
  name: myapp-headless
spec:
  clusterIP: None
  selector:
    app: myapp
  ports:
  - port: 80
```

---

## Common Patterns

### Multi-Container Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi
spec:
  initContainers:
  - name: init
    image: busybox
    command: ['sh', '-c', 'until nc -z service 80; do sleep 2; done']
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: shared
      mountPath: /app/logs
  - name: sidecar
    image: busybox
    command: ['sh', '-c', 'tail -f /logs/app.log']
    volumeMounts:
    - name: shared
      mountPath: /logs
  volumes:
  - name: shared
    emptyDir: {}
```

### Job with Parallelism

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-job
spec:
  completions: 10
  parallelism: 3
  backoffLimit: 3
  ttlSecondsAfterFinished: 100
  template:
    spec:
      containers:
      - name: worker
        image: busybox
        command: ['sh', '-c', 'echo "Processing"; sleep 10']
      restartPolicy: OnFailure
```

### CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup
spec:
  schedule: "0 2 * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: busybox
            command: ['sh', '-c', 'echo "Backup"']
          restartPolicy: OnFailure
```

### NetworkPolicy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-backend
spec:
  podSelector:
    matchLabels:
      tier: frontend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: backend
    ports:
    - protocol: TCP
      port: 80
  egress:
  - to:
    - podSelector:
        matchLabels:
          tier: database
    ports:
    - protocol: TCP
      port: 5432
```

### RBAC

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: mysa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
subjects:
- kind: ServiceAccount
  name: mysa
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

---

## Troubleshooting Checklist

1. ✅ `k get pods` - Check status
2. ✅ `k describe pod <name>` - Check events (bottom)
3. ✅ `k logs <name>` - Check application logs
4. ✅ `k get endpoints` - Service routing issues
5. ✅ Verify labels match selectors
6. ✅ Check resource requests/limits
7. ✅ Verify ConfigMaps/Secrets exist
8. ✅ Check image name and tag

---

## Exam Strategy

1. **Read question completely** before starting
2. **Use imperative commands** when possible
3. **Use --dry-run=client -o yaml** for complex resources
4. **Verify immediately:**
   ```bash
   k get pods
   k describe pod <name>
   k logs <name>
   ```
5. **Flag and skip** if stuck >5 minutes
6. **Time per question:** ~8 minutes
7. **Leave 15 minutes** for review

---

## Cron Schedule Reference

```
┌─── minute (0-59)
│ ┌─── hour (0-23)
│ │ ┌─── day of month (1-31)
│ │ │ ┌─── month (1-12)
│ │ │ │ ┌─── day of week (0-6) (Sun=0)
│ │ │ │ │
* * * * *
```

**Examples:**
- `*/5 * * * *` - Every 5 minutes
- `0 * * * *` - Hourly
- `0 0 * * *` - Daily at midnight
- `0 2 * * 0` - Weekly on Sunday at 2 AM
- `0 0 1 * *` - Monthly on 1st at midnight

---

## Resource Shortcuts

```bash
po  = pods
deploy = deployments
svc = services
cm = configmaps
sa = serviceaccounts
cj = cronjobs
pvc = persistentvolumeclaims
pv = persistentvolumes
ns = namespaces
netpol = networkpolicies
```

Good luck! 🎯
