
import pytest
import kubetest.objects
import time

@pytest.fixture(scope="module")
def web_pod(kube_module) -> kubetest.objects.Pod:
    # Wait while token controller generates tokens and adds them to the service account
    time.sleep(10)
    pod = kube_module.load_pod("./kubernetes-intro/web-pod.yaml")
    pod.create()
    kube_module.wait_until_created(pod, timeout=10)

    pods = kube_module.get_pods()
    p = pods.get("web")
    p.wait_until_ready(timeout=120)
    yield p
    p.delete(options=None)
    p.wait_until_deleted()

@pytest.mark.it("TEST: Check pod configuration")
def test_resource_existence(web_pod):
    assert web_pod is not None, "Pod does not exist"
    assert len(web_pod.get_containers()) == 1, "Pod should have one container"

@pytest.mark.it("TEST: Check web server responce")
def test_response(web_pod):
    resp = web_pod.http_proxy_get("/index.html", port=8000)
    assert 'TEST PHRASE' in resp.data


