#!/bin/bash
set -xe

export TERM=xterm
export HOMEWORK="kubernetes-intro"
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

pytest_bootstrap() {
    # Install Py3 Venv module
    sudo apt-get -q -y install software-properties-common
    sudo apt-add-repository universe
    sudo apt-get -qq update
    sudo apt-get -q -y install python3-venv

    # Create and activate venv for PyTest
    python3 -m venv /tmp/pytest && \
    source /tmp/pytest/bin/activate

    pip3 install -q -U pip setuptools

    # Setup Pytest environment
    cp -fr ./otus-platform-tests/homeworks/${HOMEWORK}/* ./
    pip3 install -q --disable-pip-version-check -r requirements.txt
}

prepare() {
    # Create kind cluster
    kind create cluster -q --wait 300s
    # Wait while all components in kube-system namespace will start
    kubectl wait --for=condition=Ready pod --all -n kube-system --timeout=300s
}

run_mandatory_tests() {
    pytest --color=yes --kube-config=~/.kube/config mandatory-tests/
}

run_additional_tests() {
    pytest --color=yes --kube-config=~/.kube/config additional-tests/
}

echo "Downloading and bootstrapping dependencies..."
download
pytest_bootstrap
echo "Preparing test cluster..."
prepare
echo "Running mandatory tests..."
run_mandatory_tests
echo "Running additional tests..."
run_additional_tests | exit 0