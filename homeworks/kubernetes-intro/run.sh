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
kind create cluster
export KUBECONFIG="$(kind get kubeconfig-path)"

# Wait while kind cluster is up and running
kubectl wait --for=condition=Ready pod/kube-controller-manager-kind-control-plane --timeout=300s -n kube-system
kubectl wait --for=condition=Ready pod/kube-apiserver-kind-control-plane --timeout=300s -n kube-system
kubectl wait --for=condition=Ready pod/kube-scheduler-kind-control-plane --timeout=300s -n kube-system

# Create pod from students with probes added
kubectl patch --local -f kubernetes-intro/web-pod.yaml -p '{"spec":{"containers":[{"name":"web","readinessProbe":{"httpGet":{"path":"/index.html", "port":8000}}}]}}' -o yaml | kubectl apply -f -

# Wait while pod will ready
kubectl wait --for=condition=Ready pod/web --timeout=120s
