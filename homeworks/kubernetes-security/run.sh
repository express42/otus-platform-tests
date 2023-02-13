#!/bin/bash
set -xe

# Download kubectl
curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Download kind
curl -Lo kind https://github.com/kubernetes-sigs/kind/releases/download/v0.17.0/kind-linux-amd64
chmod +x kind
sudo mv kind /usr/local/bin/

# Create kind cluster
kind create cluster --wait 300s
export KUBECONFIG="$(kind get kubeconfig-path)"

# We have three tasks, each one in its own directory

# task01
kubectl apply -f kubernetes-security/task01/ && sleep 10

# bob should have access to deployments in current(default) namespace
kubectl auth can-i get deployments --as system:serviceaccount:default:bob || exit 1

# bob should have access to deployments in kube-system namespace
kubectl auth can-i get deployments --as system:serviceaccount:default:bob --all-namespaces=true || exit 1

# dave should not have access to cluster
kubectl auth can-i get pods --as system:serviceaccount:default:dave && exit 1

# task02
kubectl apply -f kubernetes-security/task02/ && sleep 10

# carol should not have deployments permissions in default namespace
kubectl auth can-i get deployments --as system:serviceaccount:prometheus:carol && exit 2

# but should be able to list pods in prometheus namespace
kubectl auth can-i list pods --as system:serviceaccount:prometheus:carol -n prometheus || exit 2

# and should be able to list pods in default namespace
kubectl auth can-i list pods --as system:serviceaccount:prometheus:carol || exit 2

# now we create cindy
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cindy
  namespace: prometheus
EOF

# but should be able to list pods in prometheus namespace
kubectl auth can-i list pods --as system:serviceaccount:prometheus:cindy -n prometheus || exit 2

# and should be able to list pods in default namespace
kubectl auth can-i list pods --as system:serviceaccount:prometheus:cindy || exit 2

# now we create dan
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dan
EOF

# but should not be able to list pods in prometheus namespace
kubectl auth can-i list pods --as system:serviceaccount:default:dan -n prometheus && exit 2

# and should not be able to list pods in default namespace
kubectl auth can-i list pods --as system:serviceaccount:default:dan && exit 2


# task03
kubectl apply -f kubernetes-security/task03/ && sleep 10

# jane should not have deployments permissions in default namespace
kubectl auth can-i get deployments --as system:serviceaccount:dev:jane && exit 3

# but should be able to create deployments in dev namespace
kubectl auth can-i create deployments --as system:serviceaccount:dev:jane -n dev || exit 3

# ken should not have get deployments permissions in default namespace
kubectl auth can-i get deployments --as system:serviceaccount:dev:ken && exit 3

# but should be able to get deployments in dev namespace
kubectl auth can-i get deployments --as system:serviceaccount:dev:ken -n dev || exit 3

# and should not be able to create deployments in dev namespace
kubectl auth can-i create deployments --as system:serviceaccount:dev:ken -n dev && exit 3

exit 0

# Manual approval
# echo "All tests passed. Proceed with manual approval"
# exit 1

