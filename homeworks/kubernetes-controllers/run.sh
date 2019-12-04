#!/bin/bash
set -xe

# Download kubectl
curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl 
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Download kind
curl -Lo kind https://github.com/kubernetes-sigs/kind/releases/download/v0.6.0/kind-linux-amd64
chmod +x kind
sudo mv kind /usr/local/bin/

# Create kind cluster
kind create cluster --wait 300s

# Wait while all components in kube-system namespace will start
kubectl wait --for=condition=Ready pod --all -n kube-system --timeout=300s

# Apply all manifests from kubernetes-controllers folder
kubectl apply -f kubernetes-controllers/

exit 1
