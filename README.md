# CKAD Integrated Practice Project - Complete Solutions

## Quick Start

This repository contains **complete, working solutions** for a CKAD preparation journey.

### Prerequisites
- Kubernetes cluster (local or cloud) with kubectl configured
- Basic Docker knowledge

### How to Use This Repository

1. **Try each day yourself first** (recommended)
2. **Compare with the solution** in the corresponding day folder
3. **Understand the concepts** before moving forward

---

## Daily Progress Tracker

- [ ] Day 1 - Cluster Setup & Workflow
- [ ] Day 2 - Event API Service
- [ ] Day 3 - Configuration & Secrets
- [ ] Day 4 - Redis (Stateful)
- [ ] Day 5 - Worker Service
- [ ] Day 6 - Multi-Container Pods
- [ ] Day 7 - Health Probes
- [ ] Day 8 - Batch Jobs
- [ ] Day 9 - CronJobs
- [ ] Day 10 - Networking
- [ ] Day 11 - NetworkPolicies
- [ ] Day 12 - Security Contexts
- [ ] Day 13 - ServiceAccounts & RBAC
- [ ] Day 14 - Chaos & Debugging
- [ ] Day 15 - Full CKAD Simulation

---

## Architecture

```
[ Ingress (day10) ]
        |
[ Event API (day2) ] ---> [ Redis (day4) ] ---> [ Worker (day5) ]
        |                      |                      |
[ ConfigMaps/Secrets ]   [ PVC Storage ]      [ Job Processing ]
    (day3)                  (day4)            (day8, day9)
        |
[ Probes (day7) ]
[ Multi-Container (day6) ]
[ NetworkPolicy (day11) ]
[ Security (day12, day13) ]
```

---

## Key Exam Skills Practiced

### Speed Commands
```bash
# Fast pod creation
k run nginx --image=nginx --dry-run=client -o yaml > pod.yaml

# Fast deployment
k create deploy api --image=myapi:v1 --dry-run=client -o yaml > deploy.yaml

# Fast service
k expose deploy api --port=8080 --dry-run=client -o yaml > svc.yaml

# Fast configmap
k create cm app-config --from-literal=KEY=VALUE --dry-run=client -o yaml > cm.yaml
```

### Debugging Workflow
```bash
# 1. Check pod status
k get pods -o wide

# 2. Describe for events
k describe pod POD_NAME

# 3. Check logs
k logs POD_NAME [-c CONTAINER]

# 4. Interactive debug
k exec -it POD_NAME -- sh

# 5. Check service endpoints
k get endpoints
```

---

## CKAD Domain Coverage Map

| Day | Domain | Topics |
|-----|--------|--------|
| 1 | Core Concepts | Namespaces, context switching |
| 2 | Core Concepts | Pods, Deployments, Services |
| 3 | Configuration | ConfigMaps, Secrets, env vars |
| 4 | State Persistence | PVCs, Volumes |
| 5 | Networking | Service discovery, DNS |
| 6 | Multi-Container | Init containers, sidecars |
| 7 | Observability | Liveness, Readiness, Startup probes |
| 8 | Pod Design | Jobs, restartPolicy |
| 9 | Pod Design | CronJobs, scheduling |
| 10 | Services & Networking | Ingress, routing |
| 11 | Services & Networking | NetworkPolicies |
| 12 | Security | SecurityContexts, non-root |
| 13 | Security | ServiceAccounts, RBAC |
| 14 | Troubleshooting | Debugging scenarios |
| 15 | Full Integration | Timed simulation |

---

## Build & Deploy Pattern (Used Throughout)

Each day follows this pattern:

```bash
# 1. Navigate to day folder
cd dayXX-topic/

# 2. Build image (if applicable)
docker build -t event-api:v1 .

# 3. Make the image available in your cluster
# (Push to container registry or load locally depending on your setup)
# Example: docker tag event-api:v1 your-registry/event-api:v1 && docker push your-registry/event-api:v1

# 4. Apply manifests
kubectl apply -f k8s/

# 5. Verify
kubectl get all -n dev

# 6. Test
kubectl logs -f deployment/api -n dev
```

---

## Tips for CKAD Exam Success

### 1. Muscle Memory
- Practice creating resources **without looking at docs**
- Use `--dry-run=client -o yaml` religiously
- Learn to pipe: `k create ... | k apply -f -`

### 2. Time Management
- Bookmark critical doc pages at exam start
- Skip hard questions, come back later
- 2 hours for ~15-20 questions = 6-8 min/question

### 3. Common Patterns

**Resource Limits**
```yaml
resources:
  requests:
    memory: "64Mi"
    cpu: "250m"
  limits:
    memory: "128Mi"
    cpu: "500m"
```

**Volume Mounts**
```yaml
volumeMounts:
  - name: config
    mountPath: /config
volumes:
  - name: config
    configMap:
      name: app-config
```

**Probes**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
```

---
