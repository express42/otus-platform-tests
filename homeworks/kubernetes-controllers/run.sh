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

go_bootstrap() {
    # Install latest Go version
    wget https://dl.google.com/go/go1.13.4.linux-amd64.tar.gz
    sudo tar -xf go1.13.4.linux-amd64.tar.gz
    sudo mv go /usr/local
    export GOROOT=/usr/local/go
    export GOPATH=$HOME/
    export PATH=$GOPATH/bin:$GOROOT/bin:$PATH
    go version
    
    cp -fr ./otus-platform-tests/homeworks/${HOMEWORK}/* ./
}

prepare() {
    # Create kind cluster
    kind create cluster -q --wait 300s
    # Wait while all components in kube-system namespace will start
    kubectl wait --for=condition=Ready pod --all -n kube-system --timeout=300s
}

run_mandatory_tests() {
    cd ./mandatory-tests
    go mod tidy
    go test
}

run_additional_tests() {
    pytest --color=yes --kube-config=~/.kube/config additional-tests/
}

echo "Downloading and bootstrapping dependencies..."
download
go_bootstrap
echo "Preparing test cluster..."
prepare
echo "Running mandatory tests..."
run_mandatory_tests
