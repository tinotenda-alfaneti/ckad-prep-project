# Day 8 - Batch Jobs

## Objectives
- Create one-off Jobs
- Handle job completion and failures
- Configure parallelism and backoff

## CKAD Skills Covered
- Pod Design (20%)

---

## Simple Job

**File: `simple-job.yaml`**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-import
  namespace: dev
spec:
  template:
    spec:
      containers:
      - name: importer
        image: busybox:1.36
        command:
        - sh
        - -c
        - |
          echo "Starting data import..."
          sleep 10
          echo "Data imported successfully!"
          echo "Processed 1000 records"
      restartPolicy: Never  # OnFailure or Never for Jobs
  backoffLimit: 3  # Retry 3 times on failure
```

**Deploy:**
```bash
k apply -f simple-job.yaml
k get jobs -n dev
k get pods -n dev
k logs job/data-import -n dev
```

---

## Job with Failure

**File: `failing-job.yaml`**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: failing-task
  namespace: dev
spec:
  template:
    spec:
      containers:
      - name: task
        image: busybox:1.36
        command: ['sh', '-c', 'echo "Task failed!"; exit 1']
      restartPolicy: Never
  backoffLimit: 2  # Try 3 times total (initial + 2 retries)
```

**Test:**
```bash
k apply -f failing-job.yaml
k get jobs -n dev -w
# STATUS: 0/1 completions, then Failed after 3 attempts
k get pods -n dev -l job-name=failing-task
# Shows 3 failed pods
```

---

## Parallel Jobs

**File: `parallel-job.yaml`**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-processor
  namespace: dev
spec:
  completions: 6  # Total successful completions needed
  parallelism: 2  # Run 2 pods at a time
  template:
    spec:
      containers:
      - name: processor
        image: busybox:1.36
        command:
        - sh
        - -c
        - |
          echo "Processing batch $(hostname)..."
          sleep $(( RANDOM % 10 + 5 ))
          echo "Batch complete!"
      restartPolicy: OnFailure
  backoffLimit: 4
```

**Watch:**
```bash
k apply -f parallel-job.yaml
k get pods -n dev -l job-name=parallel-processor -w
# 2 pods run, complete, then 2 more start, etc. until 6 completions
```

---

## Job with Deadline

**File: `deadline-job.yaml`**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: timeout-job
  namespace: dev
spec:
  activeDeadlineSeconds: 30  # Kill job after 30 seconds
  template:
    spec:
      containers:
      - name: long-task
        image: busybox:1.36
        command: ['sh', '-c', 'echo "Starting..."; sleep 60; echo "Done"']
      restartPolicy: Never
```

---

## Job with TTL

**File: `ttl-job.yaml`**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: cleanup-job
  namespace: dev
spec:
  ttlSecondsAfterFinished: 60  # Delete job 60s after completion/failure
  template:
    spec:
      containers:
      - name: cleanup
        image: busybox:1.36
        command: ['sh', '-c', 'echo "Cleaning..."; sleep 5; echo "Done"']
      restartPolicy: Never
```

---

## Real-World Example: Data Processing

**File: `data-job.yaml`**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: redis-data-loader
  namespace: dev
spec:
  completions: 1
  template:
    spec:
      containers:
      - name: loader
        image: redis:7-alpine
        command:
        - sh
        - -c
        - |
          echo "Loading data into Redis..."
          for i in $(seq 1 100); do
            redis-cli -h redis SET "key_$i" "value_$i"
            echo "Loaded key_$i"
          done
          echo "Data load complete!"
      restartPolicy: OnFailure
  backoffLimit: 3
  ttlSecondsAfterFinished: 300
```

---

## Common Exam Tasks

### Task 1: Create Job from Command Line

```bash
k create job test-job --image=busybox -n dev -- echo "Hello CKAD"

# With dry-run for editing
k create job test-job --image=busybox -n dev --dry-run=client -o yaml -- echo "Hello" > job.yaml
```

### Task 2: Debug Failed Job

```bash
k get jobs -n dev
# COMPLETIONS: 0/1

k describe job failing-task -n dev
# Events: Pod failed, creating new pod

k get pods -n dev -l job-name=failing-task
# Shows failed pods

k logs <POD_NAME> -n dev
# Check error message
```

### Task 3: Delete Completed Jobs

```bash
# Manual deletion
k delete job data-import -n dev

# Or use TTL (automatic)
ttlSecondsAfterFinished: 100
```

---

## Job Patterns

| Pattern | completions | parallelism | Use Case |
|---------|-------------|-------------|----------|
| **One-shot** | 1 | 1 | Single task |
| **Parallel fixed** | N | M | Process N items with M workers |
| **Work queue** | (unset) | M | Process until queue empty |

---

## Speed Commands

```bash
# Create job
k create job myjob --image=busybox -- echo "test"

# View jobs
k get jobs -n dev

# Delete job and pods
k delete job myjob -n dev

# View job YAML
k get job myjob -n dev -o yaml
```

---

## Key Takeaways

1. **restartPolicy**: Must be `Never` or `OnFailure` (not `Always`)
2. **backoffLimit**: Number of retries before marking as failed
3. **completions**: Total successful completions needed
4. **parallelism**: Number of pods running simultaneously
5. **activeDeadlineSeconds**: Maximum job runtime
6. **ttlSecondsAfterFinished**: Auto-cleanup after completion
7. **Exam tip**: Jobs create pods with `job-name=<JOB_NAME>` label
