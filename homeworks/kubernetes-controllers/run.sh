#!/bin/bash
set -xe

export TERM=xterm
export HOMEWORK="kubernetes-controllers"
export KUBECONFIG=~/.kube/config

download(){
    export KUBECTL_VER="$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)"
    export KIND_VER="v0.6.0"

    # Download kubectl
    curl -L -o /tmp/kubectl https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VER}/bin/linux/amd64/kubectl
    sudo install /tmp/kubectl /usr/local/bin/

    # Download kind
    curl -L -o /tmp/kind https://github.com/kubernetes-sigs/kind/releases/download/${KIND_VER}/kind-linux-amd64
    sudo install /tmp/kind /usr/local/bin/
}

prepare() {
    # Create kind cluster
    kind create cluster -q --wait 300s
    # Wait while all components in kube-system namespace will start
    kubectl wait --for=condition=Ready pod --all -n kube-system --timeout=300s
}

run_mandatory_tests() {
    cd mandatory-tests
    go test
}

run_additional_tests() {
    pytest --color=yes --kube-config=~/.kube/config additional-tests/
}

echo "Downloading and bootstrapping dependencies..."
download
echo "Preparing test cluster..."
prepare
echo "Running mandatory tests..."
run_mandatory_tests
