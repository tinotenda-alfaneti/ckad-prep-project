# Day 10 - Ingress & Networking

## Objectives
- Configure Ingress for HTTP routing
- Path-based routing
- Host-based routing

## CKAD Skills Covered
- Services & Networking (20%)

---

## Install Ingress Controller

```bash
# Install NGINX Ingress Controller (if not already installed)
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Verify ingress controller
kubectl get pods -n ingress-nginx
```

---

## Simple Ingress

**File: `ingress.yaml`**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: dev
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: event-api
            port:
              number: 80
```

**Deploy:**
```bash
k apply -f ingress.yaml
k get ingress -n dev
k describe ingress api-ingress -n dev

# Test
curl http://<NODE_IP>/
```

---

## Path-Based Routing

**File: `path-ingress.yaml`**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-path-ingress
  namespace: dev
spec:
  rules:
  - http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: event-api
            port:
              number: 80
      - path: /health
        pathType: Prefix
        backend:
          service:
            name: event-api-probes
            port:
              number: 80
```

---

## Host-Based Routing

**File: `host-ingress.yaml`**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: host-ingress
  namespace: dev
spec:
  rules:
  - host: api.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: event-api
            port:
              number: 80
  - host: admin.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: event-api-probes
            port:
              number: 80
```

**Test:**
```bash
# Add to /etc/hosts
echo "192.168.1.100 api.local admin.local" | sudo tee -a /etc/hosts

curl http://api.local/
curl http://admin.local/
```

---

## Service Types

### ClusterIP (Default)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: internal-service
  namespace: dev
spec:
  type: ClusterIP
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
```

### NodePort

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nodeport-service
  namespace: dev
spec:
  type: NodePort
  selector:
    app: event-api
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080  # Optional, auto-assigned if omitted
```

**Access:** `http://<NODE_IP>:30080`

### LoadBalancer (Cloud only)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: lb-service
spec:
  type: LoadBalancer
  selector:
    app: myapp
  ports:
  - port: 80
    targetPort: 8080
```

---

## Speed Commands

```bash
# Create ingress
k create ingress myingress --rule="host/path=service:port" -n dev

# Example
k create ingress api --rule="api.local/=event-api:80" -n dev --dry-run=client -o yaml > ingress.yaml

# Expose as NodePort
k expose deployment event-api --type=NodePort --port=80 --target-port=8080 -n dev
```

---

## Key Takeaways

1. **Ingress**: Layer 7 (HTTP/HTTPS) load balancing
2. **IngressClass**: Specifies which ingress controller to use
3. **Path types**: Prefix, Exact, ImplementationSpecific
4. **Services**: ClusterIP (internal), NodePort (external via node), LoadBalancer (cloud)
5. **Exam tip**: Know how to create ingress with path and host rules