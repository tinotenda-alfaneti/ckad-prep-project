# Day 11 - NetworkPolicies

## Objectives
- Implement pod isolation
- Control ingress/egress traffic
- Default deny policies

## CKAD Skills Covered
- Services & Networking (20%)

---

## Default Deny All

**File: `deny-all.yaml`**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: dev
spec:
  podSelector: {}  # Applies to all pods
  policyTypes:
  - Ingress
  - Egress
```

**Apply:**
```bash
k apply -f deny-all.yaml

# All pods now isolated - cannot receive or send traffic
```

---

## Allow Worker → Redis

**File: `allow-worker-redis.yaml`**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-worker-to-redis
  namespace: dev
spec:
  podSelector:
    matchLabels:
      app: redis  # Apply to Redis pods
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: worker  # Allow from worker pods
    ports:
    - protocol: TCP
      port: 6379
```

---

## Allow API Ingress

**File: `allow-api-ingress.yaml`**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-ingress
  namespace: dev
spec:
  podSelector:
    matchLabels:
      app: event-api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress  # From ingress namespace
    ports:
    - protocol: TCP
      port: 8080
```

---

## Allow DNS (Egress)

**File: `allow-dns.yaml`**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: dev
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - protocol: UDP
      port: 53
```

---

## Complete Example

**File: `complete-policy.yaml`**

```yaml
# Allow worker to access Redis and DNS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: worker-policy
  namespace: dev
spec:
  podSelector:
    matchLabels:
      app: worker
  policyTypes:
  - Egress
  egress:
  # Allow Redis
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  # Allow DNS
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: UDP
      port: 53
```

---

## Test

```bash
# Apply policies
k apply -f deny-all.yaml
k apply -f allow-worker-redis.yaml
k apply -f allow-dns.yaml

# Test connectivity
k exec -it deployment/worker -n dev -- nc -zv redis 6379
# Should work

k exec -it deployment/worker -n dev -- nc -zv event-api 80
# Should fail (not allowed)
```

---

## Key Takeaways

1. **Default deny**: Best practice for security
2. **podSelector**: Which pods the policy applies to
3. **ingress**: Incoming traffic rules
4. **egress**: Outgoing traffic rules
5. **Selectors**: podSelector, namespaceSelector, ipBlock
6. **Exam tip**: NetworkPolicies are namespace-scoped

---

## Next: Day 12

Tomorrow: **Security Contexts**

**Estimated time:** 30 minutes
