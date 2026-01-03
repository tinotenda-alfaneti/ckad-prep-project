# Day 1 - Cluster, Workflow & Exam Muscle Memory

## Objectives
- Verify Kubernetes cluster is ready
- Ensure required components are enabled
- Create namespace structure
- Setup kubectl shortcuts
- Build exam-day muscle memory

## Prerequisites
- Kubernetes cluster (local or cloud)
- kubectl configured and available

---

## Tasks

### 1. Verify Cluster

```bash
# Check cluster status
kubectl cluster-info

# Check nodes
kubectl get nodes

# Get cluster info
kubectl cluster-info
```

### 2. Verify Required Components

```bash
# Verify DNS (required for service discovery)
kubectl get svc -n kube-system | grep dns

# Verify storage classes (for PVCs)
kubectl get storageclass

# Verify ingress controller (for Day 10) - may need separate installation
kubectl get svc -n ingress-nginx  # or your ingress namespace

# Verify cluster components
kubectl get componentstatuses
```

### 3. Setup kubectl Alias

```bash
# Add to ~/.bashrc or ~/.zshrc
echo "alias k='kubectl'" >> ~/.bashrc
echo "alias kgp='kubectl get pods'" >> ~/.bashrc
echo "alias kgd='kubectl get deployments'" >> ~/.bashrc
echo "alias kgs='kubectl get services'" >> ~/.bashrc
echo "alias kd='kubectl describe'" >> ~/.bashrc
echo "alias kdel='kubectl delete'" >> ~/.bashrc

# Apply changes
source ~/.bashrc

# Test
k version --short
```

**Exam tip:** The exam provides `kubectl` directly. Practice both ways.

### 4. Create Namespace Structure

```bash
# Create namespaces
k create namespace dev
k create namespace prod
k create namespace ops

# Verify
k get namespaces

# Label namespaces (useful for policies later)
k label namespace dev env=development
k label namespace prod env=production
k label namespace ops env=operations

# Verify labels
k get ns --show-labels
```

### 5. Set Default Namespace (Optional)

```bash
# Set dev as default for current context
k config set-context --current --namespace=dev

# Verify
k config view --minify | grep namespace:
```

### 6. Create Repository Structure

```bash
cd ~/projects/homelab
mkdir -p ckad-project/{namespaces,api,worker,redis,jobs,ingress,config,security,network-policy,chaos}

# Verify structure
tree ckad-project -L 1
```

### 7. Practice Speed Commands

**These are CRITICAL for exam success.**

```bash
# Create pod (imperative)
k run test-pod --image=nginx

# Create pod (declarative)
k run test-pod --image=nginx --dry-run=client -o yaml > test-pod.yaml

# Create deployment
k create deployment test-deploy --image=nginx --replicas=3

# Expose deployment
k expose deployment test-deploy --port=80 --target-port=80

# Scale deployment
k scale deployment test-deploy --replicas=5

# Create configmap
k create configmap test-cm --from-literal=key1=value1

# Create secret
k create secret generic test-secret --from-literal=password=secret123

# Get resources with custom columns
k get pods -o wide
k get pods -o yaml
k get pods -o json | jq .

# Cleanup
k delete pod test-pod
k delete deployment test-deploy
k delete service test-deploy
k delete configmap test-cm
k delete secret test-secret
```

### 8. Practice Context Switching

```bash
# View contexts
k config get-contexts

# Switch namespace quickly
k config set-context --current --namespace=dev
k get pods

k config set-context --current --namespace=prod
k get pods

k config set-context --current --namespace=ops
k get pods

# Or use -n flag (exam preferred for speed)
k get pods -n dev
k get pods -n prod
k get pods -n ops

# Get all resources across all namespaces
k get pods --all-namespaces
k get all --all-namespaces
```

### 9. Practice Describing & Debugging

```bash
# Create a test pod
k run debug-test --image=nginx -n dev

# Describe (most common debugging step)
k describe pod debug-test -n dev

# Get logs
k logs debug-test -n dev

# Execute into pod
k exec -it debug-test -n dev -- /bin/bash
# (inside pod) cat /etc/nginx/nginx.conf
# (inside pod) exit

# Port forward (test connectivity)
k port-forward pod/debug-test 8080:80 -n dev
# Open browser to localhost:8080
# Ctrl+C to stop

# Cleanup
k delete pod debug-test -n dev
```

### 10. Save Namespace Manifests

Apply the namespace manifests for future reference:

```bash
cd ~/projects/homelab/ckad-project/namespaces
k apply -f namespaces.yaml
```

---

## Verification Checklist

- [ ] Kubernetes cluster is accessible
- [ ] DNS service is running
- [ ] Storage classes are available
- [ ] Ingress controller is available
- [ ] Namespaces created: dev, prod, ops
- [ ] kubectl alias works
- [ ] Can create pods imperatively
- [ ] Can create resources declaratively with `--dry-run`
- [ ] Can switch namespaces
- [ ] Can describe, log, exec into pods

---

## Key Exam Skills Learned

1. **Speed**: Using `--dry-run=client -o yaml`
2. **Context switching**: `-n namespace` flag
3. **Imperative vs Declarative**: When to use each
4. **Debugging workflow**: describe → logs → exec
5. **Muscle memory**: Common commands without thinking

---

## Common Mistakes to Avoid

❌ Forgetting `-n namespace` (defaults to current context)
❌ Not using `--dry-run` (editing YAML manually is slow)
❌ Not checking `k describe` first when debugging
❌ Using full commands instead of aliases/shortcuts

✅ Always specify namespace explicitly
✅ Use `--dry-run` for fast YAML generation
✅ `describe` before `logs` before `exec`
✅ Practice shortcuts until they're automatic

---

## Next: Day 2

Tomorrow you'll build the **Event API** service - a simple HTTP server that demonstrates:
- Deployments
- Services
- Labels & Selectors
- Environment variable injection

**Estimated time:** 30-45 minutes
