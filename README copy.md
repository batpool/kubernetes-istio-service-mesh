kind create cluster --config kind/config.yaml --name dev

helm repo add istio https://istio-release.storage.googleapis.com/charts

helm install istio-base istio/base -n istio-system --create-namespace --wait

helm install istiod istio/istiod -n istio-system --wait

kubectl label ns default istio-injection=enabled --overwrite

kubectl wait pods --for=condition=Ready -l app=istiod -n istio-system

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


monitoring
---
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts

helm install prometheus prometheus-community/prometheus -n monitoring --create-namespace

helm install grafana grafana/grafana -n monitoring -f 

helm upgrade --install grafana grafana \
  --repo https://grafana.github.io/helm-charts \
  --set adminPassword=admin \
  --set grafana.ini.auth.anonymous.enabled=true \
  --set grafana.ini.auth.anonymous.org_role=Admin \
  -n monitoring




kiali
----

helm install kiali-server kiali-server \
  --repo https://kiali.org/helm-charts \
  --namespace istio-system \
  --create-namespace \
  --set auth.strategy="anonymous" \
  --set external_services.prometheus.url="http://prometheus-server.monitoring" \
  --set external_services.grafana.enabled=false \
  --set external_services.grafana.external_url="http://grafana.monitoring:80" \
  --set external_services.grafana.internal_url="http://grafana.monitoring:80" \
  --set external_services.grafana.health_check_url="http://grafana.monitoring:80/api/health"
