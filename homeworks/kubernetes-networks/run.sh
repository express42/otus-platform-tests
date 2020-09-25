#!/bin/bash
set -xe

export TERM=xterm

download() {
    export KUBECTL_VER="$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)"
    export KIND_VER="v0.7.0"

    # Download kubectl
    curl -L -o /tmp/kubectl https://storage.googleapis.com/kubernetes-release/release/${KUBECTL_VER}/bin/linux/amd64/kubectl
    sudo install /tmp/kubectl /usr/local/bin/

    # Download kind
    curl -L -o /tmp/kind https://github.com/kubernetes-sigs/kind/releases/download/${KIND_VER}/kind-linux-amd64
    sudo install /tmp/kind /usr/local/bin/
}

pytest_bootstrap() {
    # Install Py3 Venv module
    sudo apt-get -q -y install software-properties-common
    sudo apt-add-repository universe
    sudo apt-get -qq update
    sudo apt-get -q -y install python3-venv

    # Create and activate venv for PyTest
    python3 -m venv /tmp/pytest &&
        source /tmp/pytest/bin/activate

    pip3 install -q -U pip setuptools

    # Setup Pytest environment
    cp -fr ./otus-platform-tests/homeworks/kubernetes-networks/* ./
    pip3 install -q --disable-pip-version-check -r requirements.txt
}

prepare() {
    export KUBECONFIG="${HOME}/.kube/kind-config-pytest"
    # Create kind cluster
    kind create cluster --name=pytest --wait 300s -q
    # Wait while all components in kube-system namespace will start
    kubectl wait --for=condition=Ready pod --all -n kube-system --timeout=300s
    kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.9.3/manifests/namespace.yaml
    kubectl create secret generic -n metallb-system memberlist --from-literal=secretkey="$(openssl rand -base64 128)"
    curl -L -o ./manifests/metallb.yaml https://raw.githubusercontent.com/metallb/metallb/v0.9.3/manifests/metallb.yaml
    curl -L -o ./manifests/ingress-nginx.yaml https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-0.32.0/deploy/static/provider/cloud/deploy.yaml
}

run_tests() {
    pytest --color=yes --kube-config="${KUBECONFIG}" tests/
    kubectl get all -A
}

finalize() {
    # Manual approval
    echo "All tests passed. Proceed with manual approval"
    exit 1
}

echo "Downloading and bootstrapping dependencies..."
download
pytest_bootstrap
echo "Preparing test cluster..."
prepare
echo "Running tests..."
run_tests
echo "Running post-test tasks..."
finalize
