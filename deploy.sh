#!/bin/bash

set -e

echo "🚀 Starting microservices deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed. Please install kubectl and try again."
    exit 1
fi

# Check if Istio is installed
if ! kubectl get namespace istio-system &> /dev/null; then
    print_warning "Istio namespace not found. Please ensure Istio is installed."
    print_warning "You can install Istio using: istioctl install --set profile=demo"
fi

print_status "Building Docker images..."

# Build profile service
print_status "Building profile service..."
cd src/golang-profile-service
docker build -t profile-service:latest .
cd ../..

# Build auth service
print_status "Building auth service..."
cd src/fastapi-auth-service
docker build -t auth-service:latest .
cd ../..

print_status "Deploying to Kubernetes..."

# Create namespace
print_status "Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Deploy services
print_status "Deploying profile service..."
kubectl apply -f k8s/profile-service-deployment.yaml

print_status "Deploying auth service..."
kubectl apply -f k8s/auth-service-deployment.yaml

# Deploy Istio resources
print_status "Deploying Istio resources..."
kubectl apply -f k8s/destination-rules.yaml
kubectl apply -f k8s/istio-gateway.yaml

print_status "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=profile-service -n microservices-demo --timeout=300s
kubectl wait --for=condition=ready pod -l app=auth-service -n microservices-demo --timeout=300s

print_status "Deployment completed successfully! 🎉"

# Show deployment status
echo ""
print_status "Deployment Status:"
kubectl get pods -n microservices-demo
echo ""
kubectl get svc -n microservices-demo
echo ""

# Get Istio ingress gateway IP
print_status "Getting Istio ingress gateway IP..."
INGRESS_IP=$(kubectl get svc -n istio-system istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$INGRESS_IP" ]; then
    INGRESS_IP=$(kubectl get svc -n istio-system istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
fi

if [ -n "$INGRESS_IP" ]; then
    print_status "Istio Ingress Gateway IP: $INGRESS_IP"
    echo ""
    print_status "You can now access the services:"
    echo "  Health check: curl http://$INGRESS_IP/auth/health"
    echo "  Get token: curl -X POST \"http://$INGRESS_IP/auth/token\" -H \"Content-Type: application/x-www-form-urlencoded\" -d \"username=johndoe&password=secret\""
else
    print_warning "Could not determine Istio ingress gateway IP."
    print_warning "You may need to use port-forwarding or check your cluster configuration."
fi

echo ""
print_status "To view logs:"
echo "  kubectl logs -f deployment/auth-service -n microservices-demo"
echo "  kubectl logs -f deployment/profile-service -n microservices-demo"

echo ""
print_status "To access Kiali dashboard:"
echo "  istioctl dashboard kiali"

echo ""
print_status "To clean up:"
echo "  kubectl delete namespace microservices-demo" 