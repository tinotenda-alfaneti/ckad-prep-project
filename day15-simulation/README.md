# Day 15 - Full CKAD Simulation

## Objectives
- Complete timed CKAD challenges
- Practice exam workflow
- Build speed and confidence

---

## Exam Simulation Rules

- **Time limit:** 120 minutes
- **Tasks:** 15 challenges (see below)
- **Passing score:** 11/15 correct (73%)
- **Resources allowed:** kubernetes.io docs
- **No copy-paste from external sources**

---

## Setup

```bash
# Create fresh namespace
k create namespace exam

# Set as default
k config set-context --current --namespace=exam

# Start timer
date
```

---

## Challenges (8 minutes each)

### Task 1: Core Concepts (8 min)

Create a deployment named `web` with:
- Image: `nginx:1.24`
- Replicas: 3
- Namespace: `exam`
- Label: `tier=frontend`
- Expose as ClusterIP service on port 80

<details>
<summary>Solution</summary>

```bash
k create deployment web --image=nginx:1.24 --replicas=3 -n exam
k label deployment web tier=frontend -n exam
k expose deployment web --port=80 -n exam
```
</details>

---

### Task 2: ConfigMap & Secret (8 min)

1. Create ConfigMap `app-config` with `DB_HOST=postgres`
2. Create Secret `app-secret` with `DB_PASSWORD=secret123`
3. Create pod `db-client` using `busybox:1.36`
4. Inject ConfigMap and Secret as environment variables
5. Command: `sleep 3600`

<details>
<summary>Solution</summary>

```bash
k create cm app-config --from-literal=DB_HOST=postgres -n exam
k create secret generic app-secret --from-literal=DB_PASSWORD=secret123 -n exam

k run db-client --image=busybox:1.36 -n exam --dry-run=client -o yaml -- sleep 3600 > pod.yaml
# Edit to add envFrom
k apply -f pod.yaml
```
</details>

---

### Task 3: Multi-Container Pod (8 min)

Create pod `logger` with:
- Container 1: `app` - image `nginx`, logs to `/var/log/nginx/access.log`
- Container 2: `sidecar` - image `busybox`, command `tail -f /logs/access.log`
- Shared emptyDir volume at `/var/log/nginx` (app) and `/logs` (sidecar)

<details>
<summary>Solution</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: logger
  namespace: exam
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: logs
      mountPath: /var/log/nginx
  - name: sidecar
    image: busybox:1.36
    command: ['sh', '-c', 'tail -f /logs/access.log']
    volumeMounts:
    - name: logs
      mountPath: /logs
  volumes:
  - name: logs
    emptyDir: {}
```
</details>

---

### Task 4: Init Container (6 min)

Add init container to deployment `web`:
- Name: `init-check`
- Image: `busybox:1.36`
- Command: wait for service `redis` on port 6379 to be available

<details>
<summary>Solution</summary>

```bash
k edit deployment web -n exam
```

```yaml
initContainers:
- name: init-check
  image: busybox:1.36
  command: ['sh', '-c', 'until nc -z redis 6379; do sleep 2; done']
```
</details>

---

### Task 5: Persistent Volume (10 min)

1. Create PVC `data-pvc` requesting 1Gi storage
2. Create pod `data-pod` using `nginx` image
3. Mount PVC at `/usr/share/nginx/html`
4. Verify by creating file `/usr/share/nginx/html/index.html`

<details>
<summary>Solution</summary>

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
  namespace: exam
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: data-pod
  namespace: exam
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /usr/share/nginx/html
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: data-pvc
```
</details>

---

### Task 6: Health Probes (8 min)

Update deployment `web`:
- Liveness probe: HTTP GET `/` on port 80, initial delay 10s
- Readiness probe: HTTP GET `/` on port 80, initial delay 5s

<details>
<summary>Solution</summary>

```bash
k edit deployment web -n exam
```

```yaml
livenessProbe:
  httpGet:
    path: /
    port: 80
  initialDelaySeconds: 10
readinessProbe:
  httpGet:
    path: /
    port: 80
  initialDelaySeconds: 5
```
</details>

---

### Task 7: Job (6 min)

Create job `backup-job`:
- Image: `busybox:1.36`
- Command: `echo "Backup complete"`
- Completions: 1
- TTL: 100 seconds after completion

<details>
<summary>Solution</summary>

```bash
k create job backup-job --image=busybox:1.36 -n exam -- echo "Backup complete"
k edit job backup-job -n exam
# Add: ttlSecondsAfterFinished: 100
```
</details>

---

### Task 8: CronJob (6 min)

Create cronjob `cleanup`:
- Schedule: Every day at 2 AM
- Image: `busybox:1.36`
- Command: `date`
- Keep last 3 successful jobs

<details>
<summary>Solution</summary>

```bash
k create cronjob cleanup --image=busybox:1.36 --schedule="0 2 * * *" -n exam -- date
k edit cronjob cleanup -n exam
# Add: successfulJobsHistoryLimit: 3
```
</details>

---

### Task 9: Resource Limits (6 min)

Update deployment `web`:
- Requests: memory 64Mi, cpu 100m
- Limits: memory 128Mi, cpu 200m

<details>
<summary>Solution</summary>

```bash
k set resources deployment web -n exam \
  --requests=memory=64Mi,cpu=100m \
  --limits=memory=128Mi,cpu=200m
```
</details>

---

### Task 10: Labels & Selectors (6 min)

1. Add label `env=prod` to all pods in deployment `web`
2. Get all pods with label `env=prod`
3. Delete pods with label `tier=frontend` (but not deployment)

<details>
<summary>Solution</summary>

```bash
k label pods -l app=web env=prod -n exam
k get pods -l env=prod -n exam
k delete pods -l tier=frontend -n exam
```
</details>

---

### Task 11: NetworkPolicy (10 min)

Create NetworkPolicy `allow-web`:
- Apply to pods with label `tier=frontend`
- Allow ingress from pods with label `tier=backend` on port 80

<details>
<summary>Solution</summary>

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web
  namespace: exam
spec:
  podSelector:
    matchLabels:
      tier: frontend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: backend
    ports:
    - protocol: TCP
      port: 80
```
</details>

---

### Task 12: ServiceAccount & RBAC (10 min)

1. Create ServiceAccount `app-sa`
2. Create Role `pod-reader` with permissions to get, list pods
3. Bind role to ServiceAccount
4. Create pod `rbac-test` using this ServiceAccount

<details>
<summary>Solution</summary>

```bash
k create sa app-sa -n exam
k create role pod-reader --verb=get,list --resource=pods -n exam
k create rolebinding read-pods --role=pod-reader --serviceaccount=exam:app-sa -n exam
k run rbac-test --image=nginx --serviceaccount=app-sa -n exam
```
</details>

---

### Task 13: Security Context (8 min)

Create pod `secure`:
- Image: `nginx`
- Run as user 1000
- Non-root only
- Read-only root filesystem

<details>
<summary>Solution</summary>

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure
  namespace: exam
spec:
  securityContext:
    runAsUser: 1000
    runAsNonRoot: true
  containers:
  - name: nginx
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
</details>

---

### Task 14: Debugging (10 min)

Debug the broken deployment `broken-app` in namespace `exam`:
- Find why pods are not starting
- Fix the issue
- Verify pods are running

<details>
<summary>Solution</summary>

```bash
k get pods -n exam
k describe pod <POD_NAME> -n exam
# Check events for errors
k logs <POD_NAME> -n exam
# Fix based on error (wrong image, missing config, etc.)
```
</details>

---

### Task 15: Full Stack (12 min)

Create complete application:
1. Deployment `api` with nginx image, 2 replicas
2. Service `api-svc` exposing port 80
3. ConfigMap `api-config` with `ENV=production`
4. Mount ConfigMap as file at `/etc/config`
5. Add liveness probe HTTP GET `/` port 80

<details>
<summary>Solution</summary>

```bash
k create deployment api --image=nginx --replicas=2 -n exam
k expose deployment api --name=api-svc --port=80 -n exam
k create cm api-config --from-literal=ENV=production -n exam

k edit deployment api -n exam
# Add volume, volumeMount, and liveness probe
```
</details>

---

## Scoring

- **15/15:** 100% - Ready for exam!
- **13-14/15:** 87-93% - Strong, review weak areas
- **11-12/15:** 73-80% - Passing, practice more
- **<11/15:** <73% - More practice needed

---

## Post-Simulation

```bash
# Cleanup
k delete namespace exam

# Review mistakes
# Redo failed tasks
# Time yourself again
```

---

## Exam Day Tips

1. **Read question twice** before starting
2. **Use imperative commands** when possible
3. **Use --dry-run=client -o yaml** for templates
4. **Bookmark these docs:**
   - kubectl cheat sheet
   - Pod spec
   - Deployment spec
   - Service spec
5. **Don't get stuck** - flag and move on
6. **Verify your work:**
   ```bash
   k get pods
   k describe pod
   k logs pod
   ```
7. **Time management:** 8 min/question average