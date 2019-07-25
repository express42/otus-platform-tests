import pytest
import testinfra
import subprocess


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
