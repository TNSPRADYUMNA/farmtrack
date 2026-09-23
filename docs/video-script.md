# Video plan: approximately 8 minutes

Record your actual running Kubernetes deployment. A local SQLite preview or Docker Compose run alone does not meet this requirement.

## 0:00–1:00 — Purpose

“FarmTrack manages fields and farm tasks. I can record a planted crop, schedule watering, fertilizing or harvesting, and track completion. It is a teaching application; a small farm would normally use a simpler architecture.”

## 1:00–2:00 — Architecture

Show the diagram in architecture.md. Explain the two service responsibilities, the Field service's browser proxy, synchronous REST validation, separate schemas and shared PostgreSQL instance. Explain independent scaling and its assumed business scenario.

## 2:00–3:00 — Kubernetes resources

Run `kubectl -n farmtrack get deployments,pods,services,pvc`. Show two application Deployments, database StatefulSet, external NodePort and bound volume claim. Explain your cluster and storage provisioner. Show the actual Docker Hub image repositories.

## 3:00–4:30 — Browser demonstration

Open the Kubernetes URL, not the SQLite preview. Add North Meadow, 2.5 hectares, Rice. Schedule a watering task with a date and notes. Show the totals and filters. Complete the task and show history. Explain that the Activity service validated the field through REST.

## 4:30–5:15 — Logs

Run `kubectl -n farmtrack logs -l app=activity-service --tail=30 --prefix=true`. Identify `event=field_validation` and POST/PATCH status codes. Show a field-service log as well. Avoid showing credentials.

## 5:15–6:15 — YAML

Show image names, replicas, selectors, ports, readiness/liveness probes, Secret references, resource limits, PostgreSQL volumeClaimTemplates and the NodePort. Explain stable Kubernetes DNS names.

## 6:15–7:15 — Scaling and persistence

Scale only the Activity deployment to three replicas. Show that the Field deployment replica count does not change. Delete the database pod (not the PVC), wait for readiness, and refresh the page to show saved data. Explain your separate infrastructure restart test and its storage limitations. Pause the recording during long waits if necessary.

## 7:15–8:00 — Tradeoffs and security

Explain network dependency, shared database bottleneck and operating costs. Mention validation, parameterized SQL, non-root app containers and Secrets. Acknowledge missing login/HTTPS and required production improvements. Show the repository URL and conclude.

## Questions to rehearse

- Why two services? Business responsibilities and independent scaling.
- Why does a small farm not need this? Operational cost exceeds likely benefit.
- What if Field service is down? New task validation fails with 503; no invalid task is saved.
- What persists? PostgreSQL data on the PVC, subject to backend durability.
- What does Kubernetes Service do? Stable name/routing to matching ready pods.
- Is a Secret encrypted? Not necessarily; cluster encryption and access policy matter.
- Can I scale the database? Not by simply adding PostgreSQL replicas; replication coordination is outside scope.
- Why separate schemas? Simple data ownership, with limited isolation and shared infrastructure.
