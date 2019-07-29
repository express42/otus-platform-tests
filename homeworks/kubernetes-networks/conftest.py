import kubetest.objects
import kubetest.plugin
from kubernetes import client, config, utils
import pytest
import subprocess
import testinfra
import yaml


"""
Reusable fixtures are defined there, plus everything you'd like to do with pytest
"""


@pytest.fixture(scope="session")
def metallb(request):
    config.load_kube_config()
    k8s_client = client.ApiClient()
    utils.create_from_yaml(k8s_client, "./manifests/metallb.yaml")
    utils.create_from_yaml(k8s_client, "./kubernetes-networks/metallb-config.yaml")

    def fin():
        # Someday i'll do it better ))
        print("Calling Kubectl to delete objects from MetalLB manifest")
        subprocess.check_call(["kubectl", "delete", "-f", "./manifests/metallb.yaml"])

    request.addfinalizer(fin)


@pytest.fixture(scope="function")
def test_container(request) -> testinfra.host.Host:
    # run a container
    docker_id = (
        subprocess.check_output(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "alpine:latest",
                "nmeter",
                "-d5000",
                "%0t | MEM: %[mt] FREE:%[mf] | PROC:%[pn] | CPU: %[c]",
            ]
        )
        .decode()
        .strip()
    )

    yield testinfra.get_host("docker://" + docker_id)
    # return a testinfra connection to the container
    subprocess.check_call(["docker", "rm", "-f", docker_id])


@pytest.fixture(scope="function")
def test_pod(kube_module) -> testinfra.host.Host:
    p = kube_module.load_pod("./manifests/test-pod.yaml")
    p.create()
    kube_module.wait_until_created(p, timeout=10)
    p.wait_until_ready(timeout=30)

    yield testinfra.get_host(
        "kubectl://{pod}?namespace={ns}".format(ns=p.namespace, pod=p.name)
    )
    p.delete(options=None)


@pytest.fixture(scope="module")
def web_deploy(kube_module) -> kubetest.objects.Deployment:
    # wait for the manifests loaded by the 'applymanifests' marker
    # to be ready on the cluster
    dm = kube_module.load_deployment("./kubernetes-networks/web-deploy.yaml")
    dm.create()
    kube_module.wait_until_created(dm, timeout=10)
    deployments = kube_module.get_deployments()
    d = deployments.get("web")
    d.wait_until_ready(timeout=60)
    yield d
    d.delete(options=None)
    d.wait_until_deleted()
