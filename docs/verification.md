# Verification record

## Passed locally

- Python compilation for service, shared, launcher and test modules.
- JavaScript syntax check with Node.
- Integration test using two real Uvicorn processes and isolated SQLite files: field creation, invalid area rejection, task creation through the browser-facing proxy, missing-field rejection, invalid activity kind rejection, field filtering, completion, idempotent completion timestamp, missing-task rejection, upstream outage returning 503, and records surviving Field service restart.
- Browser interaction: add North Meadow (2.5 ha, Rice), create watering task, mark complete, and observe live totals.
- Browser screenshot inspected for readable field cards, activity row, navigation and task controls at the current browser size. Mobile CSS exists but no separate mobile browser test was performed.
- YAML parsing: namespace, PostgreSQL Service and StatefulSet, both application Deployments and Services, external NodePort Service, and Compose configuration.

## Not verified here

Docker and kubectl are unavailable on the build machine. Consequently, Docker image builds, PostgreSQL runtime behavior, image pushes, Kubernetes schema/server validation, live scaling and persistent-volume durability have not been executed. YAML parsing is not Kubernetes deployment validation. SQLite restart behavior is not evidence of PostgreSQL or infrastructure restart persistence.

No repository has been published, no Docker Hub images have been pushed, and no video has been recorded. Follow README and submission-checklist.md to complete those assignment deliverables.

The live local preview contains one example field and a completed watering task created during browser testing. The ZIP excludes local databases, caches and credentials and therefore starts empty.
