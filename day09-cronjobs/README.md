# Day 9 - CronJobs

## Objectives
- Schedule recurring jobs
- Understand cron syntax
- Manage job history

## CKAD Skills Covered
- Pod Design (20%)

---

## CronJob Basics

**File: `simple-cronjob.yaml`**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: redis-backup
  namespace: dev
spec:
  schedule: "*/5 * * * *"  # Every 5 minutes
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: redis:7-alpine
            command:
            - sh
            - -c
            - |
              echo "$(date): Starting Redis backup..."
              redis-cli -h redis SAVE
              echo "$(date): Backup complete!"
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
```

---

## Cron Schedule Syntax

```
 ┌───────────── minute (0 - 59)
 │ ┌───────────── hour (0 - 23)
 │ │ ┌───────────── day of month (1 - 31)
 │ │ │ ┌───────────── month (1 - 12)
 │ │ │ │ ┌───────────── day of week (0 - 6) (Sunday=0)
 │ │ │ │ │
 * * * * *
```

**Examples:**
```yaml
"0 * * * *"       # Every hour at minute 0
"*/15 * * * *"    # Every 15 minutes
"0 2 * * *"       # Every day at 2:00 AM
"0 0 * * 0"       # Every Sunday at midnight
"30 3 * * 1"      # Every Monday at 3:30 AM
"0 */6 * * *"     # Every 6 hours
"0 9 1 * *"       # First day of month at 9:00 AM
```

---

## Cleanup CronJob

**File: `cleanup-cronjob.yaml`**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: redis-cleanup
  namespace: dev
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: redis:7-alpine
            command:
            - sh
            - -c
            - |
              echo "Starting cleanup at $(date)..."
              # Delete keys older than 7 days (example)
              redis-cli -h redis --scan --pattern "temp:*" | xargs redis-cli -h redis DEL
              echo "Cleanup completed at $(date)"
          restartPolicy: OnFailure
      backoffLimit: 2
      ttlSecondsAfterFinished: 86400  # Clean up job after 24h
  successfulJobsHistoryLimit: 5
  failedJobsHistoryLimit: 3
  concurrencyPolicy: Forbid  # Don't start if previous job still running
```

---

## ConcurrencyPolicy

| Policy | Behavior |
|--------|----------|
| **Allow** | Multiple jobs can run concurrently (default) |
| **Forbid** | Skip new job if previous still running |
| **Replace** | Kill previous job and start new one |

**File: `concurrent-cronjob.yaml`**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: report-generator
  namespace: dev
spec:
  schedule: "*/2 * * * *"  # Every 2 minutes
  concurrencyPolicy: Forbid  # Don't overlap
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: generator
            image: busybox:1.36
            command:
            - sh
            - -c
            - |
              echo "Generating report at $(date)..."
              sleep 180  # Takes 3 minutes (longer than schedule)
              echo "Report complete"
          restartPolicy: Never
```

---

## Deploy and Test

```bash
cd ~/projects/homelab/ckad-project/day09-cronjobs/k8s

# Deploy CronJob
k apply -f simple-cronjob.yaml

# View CronJobs
k get cronjobs -n dev

# View created Jobs
k get jobs -n dev

# View pods from jobs
k get pods -n dev

# Check logs
k logs -n dev -l job-name=redis-backup-<TIMESTAMP>

# Manual trigger (don't wait for schedule)
k create job --from=cronjob/redis-backup manual-backup -n dev
```

---

## Suspend CronJob

```bash
# Suspend (stop creating new jobs)
k patch cronjob redis-backup -n dev -p '{"spec":{"suspend":true}}'

# Resume
k patch cronjob redis-backup -n dev -p '{"spec":{"suspend":false}}'

# Or edit
k edit cronjob redis-backup -n dev
# Change: suspend: true
```

---

## Common Exam Tasks

### Task 1: Create CronJob from Command Line

```bash
k create cronjob test-cron \
  --image=busybox \
  --schedule="*/1 * * * *" \
  -n dev \
  -- echo "Hello CKAD"

# With dry-run
k create cronjob test-cron \
  --image=busybox \
  --schedule="0 * * * *" \
  -n dev \
  --dry-run=client -o yaml \
  -- date > cronjob.yaml
```

### Task 2: Debug CronJob Not Running

```bash
# Check CronJob status
k get cronjob redis-backup -n dev
# SUSPEND column should be False

k describe cronjob redis-backup -n dev
# Check schedule syntax, last schedule time

# Check if Jobs are being created
k get jobs -n dev

# If no jobs, check Events
k get events -n dev --sort-by='.lastTimestamp'
```

### Task 3: Change Schedule

```bash
k edit cronjob redis-backup -n dev
# Modify schedule: "*/10 * * * *"

# Or patch
k patch cronjob redis-backup -n dev -p '{"spec":{"schedule":"0 */2 * * *"}}'
```

---

## Real-World Examples

### Database Backup

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
  namespace: prod
spec:
  schedule: "0 1 * * *"  # Daily at 1 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:15-alpine
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-creds
                  key: password
            command:
            - sh
            - -c
            - |
              pg_dump -h postgres -U admin mydb > /backup/db-$(date +%Y%m%d).sql
              echo "Backup saved"
            volumeMounts:
            - name: backup
              mountPath: /backup
          restartPolicy: OnFailure
          volumes:
          - name: backup
            persistentVolumeClaim:
              claimName: backup-pvc
```

### Log Rotation

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: log-rotate
  namespace: ops
spec:
  schedule: "0 0 * * 0"  # Weekly on Sunday
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: rotate
            image: busybox:1.36
            command:
            - sh
            - -c
            - |
              find /logs -name "*.log" -mtime +30 -delete
              echo "Old logs deleted"
            volumeMounts:
            - name: logs
              mountPath: /logs
          restartPolicy: OnFailure
          volumes:
          - name: logs
            hostPath:
              path: /var/log/apps
```

---

## Speed Commands

```bash
# Create CronJob
k create cronjob mycron --image=busybox --schedule="*/5 * * * *" -n dev -- echo "test"

# List CronJobs
k get cj -n dev

# Describe
k describe cj mycron -n dev

# Delete
k delete cj mycron -n dev

# Create job from CronJob (manual trigger)
k create job --from=cronjob/mycron manual-job -n dev
```

---

## Verification Checklist

- [ ] CronJob created with valid schedule
- [ ] Jobs created automatically per schedule
- [ ] Pods run and complete
- [ ] History limits work (old jobs deleted)
- [ ] Can suspend/resume CronJob
- [ ] Can manually trigger job from CronJob
- [ ] Understand concurrencyPolicy
- [ ] Know cron syntax patterns

---

## Key Takeaways

1. **Schedule**: Cron syntax (minute hour day month dayofweek)
2. **jobTemplate**: Contains Job spec (just like standalone Job)
3. **concurrencyPolicy**: Allow, Forbid, or Replace
4. **History limits**: successfulJobsHistoryLimit, failedJobsHistoryLimit
5. **Manual trigger**: `k create job --from=cronjob/<name>`
6. **Suspend**: Temporarily stop scheduling
7. **Exam tip**: Common schedules - hourly: `0 * * * *`, daily: `0 0 * * *`

