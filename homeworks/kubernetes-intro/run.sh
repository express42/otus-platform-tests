#!/bin/bash
set -xe

# Download kubectl
curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl 
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Download kind
curl -Lo kind https://github.com/kubernetes-sigs/kind/releases/download/v0.4.0/kind-linux-amd64
chmod +x kind 
sudo mv kind /usr/local/bin/

# Create kind cluster
kind create cluster --wait 300s
export KUBECONFIG="$(kind get kubeconfig-path)"

# Wait while all components in kube-system namespace will start
kubectl wait --for=condition=Ready pod --all -n kube-system --timeout=300s

# Create pod from students with probes added
kubectl patch --local -f kubernetes-intro/web-pod.yaml -p '{"spec":{"containers":[{"name":"web","readinessProbe":{"httpGet":{"path":"/index.html", "port":8000}}}]}}' -o yaml | kubectl apply -f -

# Wait while pod will ready
kubectl wait --for=condition=Ready pod/web --timeout=300s

# Manual approve
# echo "All tests passed. Proceed with manual approve" 
# exit 1

