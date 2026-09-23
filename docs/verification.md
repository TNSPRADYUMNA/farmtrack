# Verification record

## Initial local checks

- Python compilation and JavaScript syntax checks passed.
- Integration tests using two Uvicorn processes and SQLite passed, covering validation, field and activity creation, filtering, completion, upstream failure handling, and persistence after a service restart.
- Browser testing covered field creation, activity creation, completion, and dashboard totals.
- Compose and Kubernetes YAML files parsed successfully.
- Mobile layout was not separately tested.

## Docker and registry verification

- Docker Compose built and ran both application services and PostgreSQL.
- Saved records survived Docker Compose shutdown and startup without deleting volumes.
- Application images were pushed to Docker Hub:
  - pradyummm/farmtrack-fields:1.0.0
  - pradyummm/farmtrack-activities:1.0.0
- Kubernetes successfully pulled both images.

## Kubernetes verification

- Deployed to the local kind-farmtrack cluster.
- The node became Ready, and system pods were Running.
- PostgreSQL became ready with a Bound 1 GiB persistent volume claim.
- Both application Deployments reached two ready replicas.
- Browser access worked through kubectl port-forward on port 8080.
- The fields and activities API routes returned HTTP 200.
- A field and activity were saved through the browser.
- Saved records remained after deleting and recreating the PostgreSQL pod.
- The field service scaled independently to three ready replicas while the activity service remained at two.
- The activity service then scaled to three ready replicas while the field service remained at three.

## Issues and limitations

- Cluster creation required a locally modified kind executable with a longer node startup log timeout.
- Earlier application startup failures included temporary database hostname resolution errors.
- Health-check timeouts caused container restarts and interrupted port-forward connections.
- Later API and browser checks succeeded, but the underlying intermittent failures were not conclusively resolved.
- The persistence test covered PostgreSQL pod replacement, not cluster deletion, volume deletion, or disaster recovery.
- Scaling checks verified replica readiness, not load performance or automatic scaling.
- Browser access was demonstrated on the local machine, not through a public internet endpoint.

## Submission status

- Source repository published:
  https://github.com/TNSPRADYUMNA/farmtrack
- Written documentation and Kubernetes manifests are present in the repository.
- Demonstration video remains to be recorded.