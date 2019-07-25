import kubetest.plugin as kbp
import pytest
import subprocess
import testinfra


"""
Reusable fixtures are defined there, plus everything you'd like to do with pytest
"""


@pytest.fixture(scope="function")
def test_container(request):
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
    # return a testinfra connection to the container
    yield testinfra.get_host("docker://" + docker_id)
    subprocess.check_call(["docker", "rm", "-f", docker_id])


@pytest.fixture(scope="function")
def test_pod(request, kube_module):
    p = kube_module.load_pod("./manifests/test-pod.yaml")
    p.create()
    kube_module.wait_for_registered(timeout=30)
    p.wait_until_ready(timeout=30)
    yield testinfra.get_host(
        "kubectl://{pod}?namespace={ns}".format(ns=p.namespace, pod=p.name)
    )
    p.delete(options=None)


@pytest.fixture(scope="module")
def web_deploy(request, kube_module):
    # wait for the manifests loaded by the 'applymanifests' marker
    # to be ready on the cluster
    dm = kube_module.load_deployment("./kubernetes-networks/web-deploy.yaml")
    dm.create()
    kube_module.wait_for_registered(timeout=30)
    deployments = kube_module.get_deployments()
    d = deployments.get("web")
    d.wait_until_ready(timeout=60)
    yield d
    """
    This really hacky and weird way of cleaning up test namespaces
    It should be fixed with patching kubetest code, but I still haven't
    found, where things gone wrong.
    """
    kbp.pytest_keyboard_interrupt()
