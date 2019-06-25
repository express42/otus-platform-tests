
#!/bin/bash
set -e

# Download kubectl
curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl 
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Download kind
curl -Lo kind https://github.com/kubernetes-sigs/kind/releases/download/v0.3.0/kind-linux-amd64
chmod +x kind 
sudo mv kind /usr/local/bin/

kind create cluster
export KUBECONFIG="$(kind get kubeconfig-path)"

kubectl version
