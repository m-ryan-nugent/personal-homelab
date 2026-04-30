# Dashboard K3s Deployment

This dashboard now uses a registry-backed image flow instead of a node-local K3s image.

The Deployment pulls:

```text
ghcr.io/m-ryan-nugent/cluster-dashboard:latest
```

That removes the old rollout constraint where the pod had to stay on `pi-worker-1` because the image only existed in that node's local containerd store.

## Deployment Flow

1. Push changes under `infra/apps/cluster-dashboard/` to `main`.
2. GitHub Actions builds and publishes the dashboard image to GHCR.
3. Apply the Kubernetes manifests.
4. Restart the Deployment when you want the cluster to pull the newest `latest` tag.
5. K3s schedules the pod on any eligible node.

The image workflow lives at:

```text
.github/workflows/build-cluster-dashboard.yml
```

## One-Time GitHub Setup

Before the first cluster rollout, confirm these GitHub settings:

1. Actions are enabled for the repository.
2. The workflow has permission to write packages.
3. The `cluster-dashboard` GHCR package is public.

If you keep the package private, create an image pull secret and add `imagePullSecrets` to the Deployment before rolling out.

## Apply the Dashboard Manifests

Run these commands from the machine that already has `kubectl` access to the cluster. Based on the current setup, that is `pi-worker-1`.

```bash
cd ~/personal-homelab

kubectl apply -f infra/apps/cluster-dashboard/k8s/namespace.yaml
kubectl apply -f infra/apps/cluster-dashboard/k8s/configmap-config.yaml
kubectl apply -f infra/apps/cluster-dashboard/k8s/deployment.yaml
kubectl apply -f infra/apps/cluster-dashboard/k8s/service.yaml

kubectl rollout status deployment/cluster-dashboard -n homelab
kubectl get pods -n homelab -o wide
kubectl get svc -n homelab cluster-dashboard
```

The dashboard remains exposed through the NodePort service on `30080`.

Known-good URL:

```text
http://10.0.0.101:30080/frontend/
```

The nginx config also redirects `/` to `/frontend/`, but keeping the kiosk on the explicit path avoids ambiguity.

## Pull a Fresh Image After a New GitHub Build

Because the Deployment uses `imagePullPolicy: IfNotPresent`, a pod that is already running will keep its current image until it is recreated.

After a successful GitHub Actions build, pull the new image with a rollout restart:

```bash
kubectl rollout restart deployment/cluster-dashboard -n homelab
kubectl rollout status deployment/cluster-dashboard -n homelab
kubectl get pods -n homelab -o wide
```

## Verify the Pod Is No Longer Node-Pinned

Check where the pod is currently running:

```bash
kubectl get pods -n homelab -o wide
```

If you want to prove the workload can move off its current node, cordon that node, delete the pod, and watch Kubernetes reschedule it:

```bash
kubectl cordon <current-node>
kubectl delete pod -n homelab -l app=cluster-dashboard
kubectl get pods -n homelab -o wide -w
kubectl uncordon <current-node>
```

If the replacement pod comes up on a different node and still serves the dashboard, the GHCR-based deployment flow is working.

## Optional: Private GHCR Package

If you decide to keep the image private, create a pull secret in the `homelab` namespace:

```bash
kubectl create secret docker-registry ghcr-creds \
  -n homelab \
  --docker-server=ghcr.io \
  --docker-username=<github-username> \
  --docker-password=<classic-personal-access-token>
```

Then add this to the Deployment spec:

```yaml
imagePullSecrets:
  - name: ghcr-creds
```