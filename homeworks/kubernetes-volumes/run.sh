#!/bin/bash
set -xe

# Download kubectl
curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl 
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Download kind
curl -Lo kind https://github.com/kubernetes-sigs/kind/releases/download/v0.11.1/kind-linux-amd64
chmod +x kind 
sudo mv kind /usr/local/bin/

# Create kind cluster
kind create cluster --wait 300s
export KUBECONFIG="$(kind get kubeconfig-path)"

# Wait while all components in kube-system namespace will start
kubectl wait --for=condition=Ready pod --all -n kube-system --timeout=300s

# Create pod from students with probes added
kubectl apply -f kubernetes-volumes/

# Wait while pod will ready
kubectl wait --for=condition=Ready pod/minio-0 --timeout=300s

# Wait while MinIO will ready
sleep 10

# Connect to Minio and upload file
kubectl run -i --tty --rm debug --image=otusplatform/test-minio --restart=Never

# Manual approval
# echo "All tests passed. Proceed with manual approval" 
# exit 1
