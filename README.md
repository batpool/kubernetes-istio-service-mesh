<p align="center">
  <img src="./assets/kubernetes-istio-service-mesh-dark.png#gh-dark-mode-only" alt="kubernetes-istio-service-mesh-Logo" width="100%" />
  <img src="./assets/kubernetes-istio-service-mesh-light.png#gh-light-mode-only" alt="kubernetes-istio-service-mesh-Logo" width="100%" />
</p>

<h1 align="center">Kubernetes Istio Service Mesh With Kiali Console</h1>

<p align="center">
  <a href="https://github.com/batpool/kubernetes-istio-service-mesh/actions?query=workflow%3ACI+branch%3Amain">
    <img src="https://github.com/batpool/kubernetes-istio-service-mesh/actions/workflows/pipeline.yml/badge.svg?branch=master" />
  </a>
  <a href="https://github.com/batpool?tab=packages&repo_name=kubernetes-istio-service-mesh">
    <img src="https://img.shields.io/badge/GHCR-packages-0A0A0A?logo=github&logoColor=white" />
  </a>
  <a href="https://github.com/batpool/kubernetes-istio-service-mesh/blob/master/LICENSE">
    <img src="https://img.shields.io/github/license/batpool/kubernetes-istio-service-mesh" />
  </a>
  <a href="https://github.com/batpool/kubernetes-istio-service-mesh/blob/master/CODE_OF_CONDUCT.md">
    <img src="https://img.shields.io/badge/code%20of%20conduct-active-blueviolet" />
  </a>
  <a href="https://github.com/batpool/kubernetes-istio-service-mesh/blob/master/SECURITY.md">
    <img src="https://img.shields.io/badge/security-policy-important?color=red&logo=github" />
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/kubernetes-1.33-blue?logo=kubernetes&logoColor=white" />
  <img src="https://img.shields.io/badge/helm-3.18.3-0F1689?logo=helm&logoColor=white" />
  <img src="https://img.shields.io/badge/envoy-proxy-FF3366?logo=envoyproxy&logoColor=white" />
  <img src="https://img.shields.io/badge/kind-cluster-orange?logo=kubernetes&logoColor=white" />
  <img src="https://img.shields.io/badge/go-1.24.3-00ADD8?logo=go&logoColor=white" />
  <img src="https://img.shields.io/badge/gin-framework-black?logo=go&logoColor=white" />
  <img src="https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/pip-installed-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/fastapi-0.115.14-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/yaml-configured-C9B035?logo=yaml&logoColor=black" />
  <img src="https://img.shields.io/badge/istio-1.22.0-466BB0?logo=istio&logoColor=white" />
  <img src="https://img.shields.io/badge/kiali-enabled-3A6DA8?logo=kiali&logoColor=white" />
  <img src="https://img.shields.io/badge/prometheus-observability-E6522C?logo=prometheus&logoColor=white" />
  <img src="https://img.shields.io/badge/grafana-dashboards-F46800?logo=grafana&logoColor=white" />
  <img src="https://img.shields.io/badge/docker-multistage-2496ED?logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/ghcr-supported-0A0A0A?logo=github&logoColor=white" />
</p>

<details>
<summary><strong>📁 Table of Contents</strong></summary>

- [Screenshot Kiali](#-screenshot-kiali)
- [Step-by-Step Installation](#%EF%B8%8F-step-by-step-installation-guide)
  - [Clone the Repository](#-clone-the-repository)
  - [Create Kind Cluster](#-create-kind-cluster)
  - [Add Istio and Install Components](#-add-istio-helm-repo-and-install-components)
  - [Enable Istio Injection](#-enable-istio-injection)
  - [Install Istio Gateway](#-install-istio-gateway)
  - [Monitoring Setup](#-monitoring-setup)
  - [Kiali Dashboard](#-kiali-dashboard)
  - [Install Microservices](#%EF%B8%8F-install-microservices)
- [Security](SECURITY.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [License](LICENSE)
- [GitHub Packages](https://github.com/batpool?tab=packages&repo_name=kubernetes-istio-service-mesh)

</details>

---

## 📊 Screenshot Kiali
<img src="./assets/1.png" />
<img src="./assets/2.png" />
<img src="./assets/3.png" />

## 🛠️ Step-by-Step Installation Guide

### 🧬 Clone the Repository

Start by cloning the project to your local machine:

```bash
git clone https://github.com/batpool/kubernetes-istio-service-mesh.git
cd kubernetes-istio-service-mesh
```

### 🧱 Create Kind Cluster

```bash
kind create cluster --config kind/config.yaml --name dev
```

### 📦 Add Istio Helm Repo and Install Components

```bash
helm repo add istio https://istio-release.storage.googleapis.com/charts

helm install istio-base istio/base -n istio-system --create-namespace --wait
helm install istiod istio/istiod -n istio-system --wait
```

### 🔧 Enable Istio Injection

```bash
kubectl label ns default istio-injection=enabled --overwrite
kubectl wait pods --for=condition=Ready -l app=istiod -n istio-system
```

### 🌐 Install Istio Gateway

```bash
helm install istio-gateway istio/gateway -n istio-system \
  --set "service.type=NodePort" \
  --set "service.ports[0].name=http2" \
  --set "service.ports[0].port=80" \
  --set "service.ports[0].nodePort=30000" \
  --set "service.ports[1].name=https" \
  --set "service.ports[1].port=443" \
  --set "service.ports[1].nodePort=31000" \
  --set "service.ports[2].name=status-port" \
  --set "service.ports[2].port=15021" \
  --set "service.ports[2].targetPort=15021" \
  --set "service.ports[2].nodePort=32000"

kubectl apply -f istio/servicemesh/gateway.yaml
```

### 📈 Monitoring Setup

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

helm install prometheus prometheus-community/prometheus -n monitoring --create-namespace

```

### 📊 Kiali Dashboard

```bash
helm install kiali-server kiali-server \
  --repo https://kiali.org/helm-charts \
  --namespace istio-system \
  --create-namespace \
  --set auth.strategy="anonymous" \
  --set external_services.prometheus.url="http://prometheus-server.monitoring" \
  --set external_services.grafana.enabled=false
```

### ⚙️ Install Microservices

```bash
helm install fastapi-auth-service ./helm-charts/fastapi-auth-service

helm install golang-profile-service ./helm-charts/golang-profile-service
```

---

✅ Now you’re ready to visualize your Istio Service Mesh with **Kiali**, **Prometheus** – all running on a local **Kind** cluster!

> 🌟 *Don’t forget to give a ⭐ on GitHub if you find this project helpful!*