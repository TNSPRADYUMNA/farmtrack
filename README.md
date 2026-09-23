# FarmTrack

A teaching project for managing farm fields, crops, and watering, fertilizing, and harvesting tasks. Two Python REST microservices and PostgreSQL, with a responsive browser interface.

## Start here

- `docs/architecture.md`: design, security, business implications, and requirement mapping.
- `docs/video-script.md`: an approximately eight-minute Kubernetes demonstration.
- `docs/submission-checklist.md`: remaining evidence and submission requirements.
- `docs/verification.md`: exactly what was tested and what was not.

## Quick local preview (Python 3.11+)

Run from this project directory in PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/run-local.py
```

Open http://127.0.0.1:8001. Stop with Ctrl+C. This development mode uses two separate SQLite files in `.local-data`; it is NOT the Kubernetes assignment deployment. The fields API docs are at http://127.0.0.1:8001/docs and activities API docs at http://127.0.0.1:8002/docs. Add fields before scheduling tasks. The UI starts empty and all dashboard totals come from saved data.

## PostgreSQL / Docker Compose

Install Docker with Linux containers. Create an ignored `.env` file containing `DB_PASSWORD=` followed by a strong local password. Do not commit it. Then:

```powershell
docker compose up --build -d
```

Open http://localhost:8080. `docker compose logs -f` shows application logs. `docker compose down` stops the services while retaining the named database volume. Do not use `down -v` if you need the data.

## Publish images to Docker Hub

Create two public Docker Hub repositories, `farmtrack-fields` and `farmtrack-activities`, under your account. Sign in with `docker login`, then:

```powershell
./scripts/publish-images.ps1 -DockerHubUser YOUR_DOCKERHUB_USERNAME
```

Replace `YOUR_DOCKERHUB_USERNAME` in both `k8s/field-service.yaml` and `k8s/activity-service.yaml` with your real username. Images must be pushed before deploying; placeholders are not runnable image references. If your cluster uses another CPU architecture, build for that architecture or publish multi-platform images. Private repositories require an image pull Secret, so public repositories are simplest for examination.

## Deploy on Kubernetes

Use a local teaching cluster such as Minikube or Docker Desktop Kubernetes, or an existing cluster. You need Docker, kubectl, a running cluster, and a default StorageClass. Check:

```powershell
kubectl config current-context
kubectl get nodes
kubectl get storageclass
kubectl apply -f k8s/namespace.yaml
```

Generate a database password locally, without committing it:

```powershell
$dbPassword = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
kubectl -n farmtrack create secret generic database-credentials --from-literal="password=$dbPassword"
Remove-Variable dbPassword
kubectl apply -f k8s/postgres.yaml
kubectl -n farmtrack rollout status statefulset/postgres --timeout=180s
kubectl apply -f k8s/field-service.yaml
kubectl apply -f k8s/activity-service.yaml
kubectl apply -f k8s/web.yaml
kubectl -n farmtrack rollout status deployment/field-service --timeout=180s
kubectl -n farmtrack rollout status deployment/activity-service --timeout=180s
kubectl -n farmtrack get pods,services,pvc
```

Create the Secret once. Changing it does not change the password inside an existing PostgreSQL data volume. A Pending PVC usually means that a storage provisioner/default StorageClass is missing. Configure storage for your cluster rather than deleting data.

### Browser access

The NodePort service exposes port 30080 on a reachable cluster node. On Docker Desktop, try http://localhost:30080. With Minikube, use `minikube service farmtrack-web -n farmtrack --url` and keep any required tunnel process running. Alternatively:

```powershell
kubectl -n farmtrack port-forward service/farmtrack-web 8080:80
```

Open http://localhost:8080 while that command runs. Port-forwarding is a local demonstration access method, not permanent hosting. A production deployment should use an authenticated HTTPS ingress. This demo has no user login; use a controlled teaching environment.

### Independent horizontal scaling

```powershell
kubectl -n farmtrack scale deployment/field-service --replicas=3
kubectl -n farmtrack scale deployment/activity-service --replicas=4
kubectl -n farmtrack get deployments,pods
```

Each service starts with two replicas and stores no application state in pod memory. There is no automatic HPA; manual horizontal scaling meets the independent scaling requirement. CPU limits and readiness probes are included. Applying the manifests again restores their specified replica counts.

### Logs and persistence demonstration

Create a field and an activity through the UI, then:

```powershell
kubectl -n farmtrack logs -l app=activity-service --tail=50 --prefix=true
kubectl -n farmtrack logs -l app=field-service --tail=50 --prefix=true
kubectl -n farmtrack delete pod postgres-0
kubectl -n farmtrack wait --for=condition=Ready pod/postgres-0 --timeout=180s
kubectl -n farmtrack get pvc
```

Refresh the browser and verify your records remain. Brief errors during the database restart are expected because there is one database instance. For infrastructure restart evidence, restart the same local cluster WITHOUT deleting it, then verify the records again. Minikube supports `minikube stop` followed by `minikube start`. A PVC survives pod replacement, but infrastructure durability depends on its actual storage backend. Node-local storage does not survive loss of its disk or deletion of the cluster. For stronger durability, use an external persistent disk, an appropriate retention policy, and tested backups. Do not delete the namespace or PVC as part of the persistence demonstration.

## Tests

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
node --check services/fields/static/app.js
```

The integration test starts two real HTTP servers against temporary SQLite storage. It checks creation, REST validation, completion, invalid requests, service outage behavior, and restart persistence. It does not substitute for PostgreSQL/Kubernetes testing.

## Publish the configuration repository

Create a GitHub/GitLab repository you can share with the examiner, then run from this directory:

```powershell
git init
git add .
git commit -m "Build FarmTrack microservices application"
git branch -M main
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

Review staged files before committing. Never upload `.env`, credentials, or private data. Add the real repository URL, Docker Hub URLs, and recording URL to your submission. No remote repository or Docker Hub images have been published by the project generator.
