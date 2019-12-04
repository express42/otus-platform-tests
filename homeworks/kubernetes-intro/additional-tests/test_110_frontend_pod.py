
import pytest
import kubetest.objects
import time

@pytest.fixture(scope="module")
def frontend_pod(kube_module) -> kubetest.objects.Pod:
    # Wait while token controller generates tokens and adds them to the service account
    time.sleep(10)
    pod = kube_module.load_pod("./kubernetes-intro/frontend-pod.yaml")
    pod.create()
    kube_module.wait_until_created(pod, timeout=10)

    pods = kube_module.get_pods()
    p = pods.get("frontend")
    p.wait_until_containers_start(timeout=60)
    yield p
    p.delete(options=None)
    p.wait_until_deleted()

@pytest.mark.it("TEST: Check pod configuration")
def test_resource_existence(frontend_pod):
    assert frontend_pod is not None, "Pod does not exist"

@pytest.mark.it("TEST: Check pod status")
def test_resource_status(frontend_pod):
    assert frontend_pod.is_ready(), "Pod is not ready"