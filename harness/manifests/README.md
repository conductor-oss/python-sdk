# Kubernetes Manifests

This directory contains Kubernetes manifests for deploying the Python SDK harness worker to the certification clusters.

## Prerequisites

**Set your namespace environment variable:**
```bash
export NS=your-namespace-here
```

All kubectl commands below use `-n $NS` to specify the namespace. The manifests intentionally do not include hardcoded namespaces.

**Note:** The harness worker images are published as public packages on GHCR and do not require authentication to pull. No image pull secrets are needed.

## Files

| File | Description |
|---|---|
| `deployment.yaml` | Deployment (single file, works on all clusters) |
| `configmap-aws.yaml` | Conductor URL + auth key for certification-aws |
| `configmap-azure.yaml` | Conductor URL + auth key for certification-az |
| `configmap-gcp.yaml` | Conductor URL + auth key for certification-gcp |
| `secret-conductor.yaml` | Conductor auth secret (placeholder template) |

## Quick Start

### 1. Create the Conductor Auth Secret

The `CONDUCTOR_AUTH_SECRET` must be created as a Kubernetes secret before deploying.

```bash
kubectl create secret generic conductor-credentials \
  --from-literal=auth-secret=YOUR_AUTH_SECRET \
  -n $NS
```

If the `conductor-credentials` secret already exists in the namespace (e.g. from the e2e-testrunner-worker), it can be reused as-is.

See `secret-conductor.yaml` for more details.

### 2. Apply the ConfigMap for Your Cluster

```bash
# AWS
kubectl apply -f manifests/configmap-aws.yaml -n $NS

# Azure
kubectl apply -f manifests/configmap-azure.yaml -n $NS

# GCP
kubectl apply -f manifests/configmap-gcp.yaml -n $NS
```

### 3. Deploy

```bash
kubectl apply -f manifests/deployment.yaml -n $NS
```

### 4. Verify

```bash
# Check pod status
kubectl get pods -n $NS -l app=python-sdk-harness-worker

# Watch logs
kubectl logs -n $NS -l app=python-sdk-harness-worker -f
```

## Building and Pushing the Image

From the repository root:

```bash
# Build the harness target and push to GHCR
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --target harness \
  -t ghcr.io/conductor-oss/python-sdk/harness-worker:latest \
  --push .
```

After pushing a new image with the same tag, restart the deployment to pull it:

```bash
kubectl rollout restart deployment/python-sdk-harness-worker -n $NS
kubectl rollout status deployment/python-sdk-harness-worker -n $NS
```

## Tuning

The harness worker accepts these optional environment variables (set in `deployment.yaml`):

| Variable | Default | Description |
|---|---|---|
| `HARNESS_WORKFLOWS_PER_SEC` | 2 | Workflows to start per second |
| `HARNESS_BATCH_SIZE` | 20 | Tasks each worker polls per batch |
| `HARNESS_POLL_INTERVAL_MS` | 100 | Milliseconds between poll cycles |

Edit `deployment.yaml` to change these, then re-apply:

```bash
kubectl apply -f manifests/deployment.yaml -n $NS
```

## Troubleshooting

### Pod not starting

```bash
kubectl describe pod -n $NS -l app=python-sdk-harness-worker
kubectl logs -n $NS -l app=python-sdk-harness-worker --tail=100
```

### Secret not found

```bash
kubectl get secret conductor-credentials -n $NS
```

## Resource Limits

Default resource allocation:
- **Memory**: 256Mi (request) / 512Mi (limit)
- **CPU**: 100m (request) / 500m (limit)

Adjust in `deployment.yaml` based on workload. Higher `HARNESS_WORKFLOWS_PER_SEC` values may need more CPU/memory.

## Service

The harness worker does **not** need a Service or Ingress. It connects to Conductor via outbound HTTP polling. All communication is outbound.
