# Dashboard K3s Deployment

This dashboard now uses a registry-backed image flow instead of a node-local K3s image.

The Deployment pulls:

```text
ghcr.io/m-ryan-nugent/cluster-dashboard:v1.0.3
```

The metric sync CronJob uses:

```text
ghcr.io/m-ryan-nugent/cluster-dashboard-temperature-sync:v1.0.3
```

That removes the old rollout constraint where the pod had to stay on `pi-worker-1` because the image only existed in that node's local containerd store.

## Deployment Flow

1. Push changes under `infra/apps/cluster-dashboard/` to `main`.
2. Create and push a release tag such as `<version>`.
3. GitHub Actions builds and publishes the tagged dashboard image to GHCR.
4. Update the Kubernetes manifest to that explicit tag.
5. Apply the Kubernetes manifests.
6. K3s schedules the pod on any eligible node.

The image workflow lives at:

```text
.github/workflows/build-cluster-dashboard.yml
```

For day-to-day development, `main` still publishes `latest` and a short SHA tag. The Kubernetes manifest should use a version tag for normal releases so the deployed version is explicit in git.

Use the release helper to update the pinned image references across the repo before you tag a release:

```bash
uv run python scripts/src/release_dashboard.py <version>
```

To verify the tracked dashboard docs and manifest are still aligned, run:

```bash
uv run python scripts/src/release_dashboard.py --check
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

## Update Dashboard Metrics

The dashboard can now be refreshed from the repo by collecting Raspberry Pi temperatures, load averages, and uptime over SSH and syncing them into the ConfigMap source file:

```bash
cd ~/personal-homelab
uv run python scripts/src/sync_dashboard_temperatures.py
kubectl apply -f infra/apps/cluster-dashboard/k8s/configmap-config.yaml
```

Run the collector from a machine that already has key-based SSH access to the Pi nodes. It uses non-interactive `ssh` and will fail fast if it would need a password prompt.

Useful variants:

```bash
uv run python scripts/src/sync_dashboard_temperatures.py --dry-run
uv run python scripts/src/sync_dashboard_temperatures.py --node pi-worker-1
```

The Deployment now mounts the dashboard config directory directly instead of using `subPath`, so ConfigMap updates can propagate into the running pod without restarting the Deployment.

## Automate Node Metrics With a CronJob

The repo now includes a Kubernetes-owned sync path so the cluster can refresh dashboard node metrics without relying on a laptop:

- `infra/apps/cluster-dashboard/k8s/temperature-sync-rbac.yaml`
- `infra/apps/cluster-dashboard/k8s/cronjob-temperature-sync.yaml`

The `CronJob` runs every 5 minutes, SSHes to the Pi nodes using a mounted private key, collects temperature, 1-minute load average, and uptime, and patches the `cluster-dashboard-config` ConfigMap directly.

Before you apply the updated `CronJob` manifest, push the repo changes and cut the next release tag so the versioned `cluster-dashboard-temperature-sync` image exists in GHCR.

### 1. Create a dedicated SSH key for the CronJob

Generate a separate key for the in-cluster job rather than reusing your laptop key:

```bash
ssh-keygen -t ed25519 \
  -f ~/.ssh/id_ed25519_homelab_temperature_sync \
  -C "cluster-dashboard-temperature-sync"
```

Install the public key on each node:

```bash
for host in 10.0.0.100 10.0.0.101 10.0.0.102 10.0.0.103; do
  cat ~/.ssh/id_ed25519_homelab_temperature_sync.pub | ssh pi@"$host" \
    'umask 077; mkdir -p ~/.ssh; touch ~/.ssh/authorized_keys; cat >> ~/.ssh/authorized_keys'
done
```

### 2. Create the Kubernetes secret with the private key

```bash
kubectl create secret generic cluster-dashboard-ssh \
  -n homelab \
  --from-file=id_ed25519=$HOME/.ssh/id_ed25519_homelab_temperature_sync
```

### 3. Apply the automation manifests

```bash
kubectl apply -f infra/apps/cluster-dashboard/k8s/temperature-sync-rbac.yaml
kubectl apply -f infra/apps/cluster-dashboard/k8s/cronjob-temperature-sync.yaml
```

### 4. Trigger one manual run before waiting for the schedule

```bash
kubectl create job \
  --from=cronjob/cluster-dashboard-temperature-sync \
  cluster-dashboard-temperature-sync-manual \
  -n homelab

kubectl logs -n homelab job/cluster-dashboard-temperature-sync-manual
kubectl get configmap cluster-dashboard-config -n homelab -o yaml
```

If the manual job succeeds, the scheduled `CronJob` will keep updating node metrics in the live dashboard ConfigMap.

## Release Checklist

Use this flow for each dashboard release:

```bash
git checkout main
git pull
uv run python scripts/src/release_dashboard.py <version>
git diff
git commit -am "Release cluster dashboard <version>"
git push origin main
git tag <version>
git push origin <version>
```

Wait for the `Build Cluster Dashboard` workflow to publish the tag, then make sure [infra/apps/cluster-dashboard/k8s/deployment.yaml](infra/apps/cluster-dashboard/k8s/deployment.yaml) points at the same version:

```text
ghcr.io/m-ryan-nugent/cluster-dashboard:<version>
```

Apply the manifest after the image exists in GHCR:

```bash
kubectl apply -f infra/apps/cluster-dashboard/k8s/deployment.yaml
kubectl rollout status deployment/cluster-dashboard -n homelab
```

The helper updates the deployment manifest and the versioned GHCR references in the release docs together.

## Pull a Fresh Image After a New GitHub Build

Because the Deployment uses `imagePullPolicy: IfNotPresent`, a pod that is already running will keep its current image until it is recreated.

After you update the manifest to a new version tag and apply it, verify the rollout:

```bash
kubectl apply -f infra/apps/cluster-dashboard/k8s/deployment.yaml
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