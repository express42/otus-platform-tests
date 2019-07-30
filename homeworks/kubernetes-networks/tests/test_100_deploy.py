import pytest
import kubetest.objects

"""
Fixture definitions. Common fixtures, such as toolbox pod are in conftest.py
"""


@pytest.fixture(scope="module")
def web_service_cip(kube_module) -> kubetest.objects.Service:
    svc = kube_module.load_service("./kubernetes-networks/web-svc-cip.yaml")
    svc.create()
    kube_module.wait_for_registered(timeout=30)
    yield svc
    svc.delete(options=None)
    svc.wait_until_deleted()


@pytest.fixture
def pod_list_by_selector(kube_module):
    pod_list = kube_module.get_pods(labels={"app": "web"})
    return pod_list


"""
Actual tests code below. Fixtures are called and created as needed
"""


@pytest.mark.it("TEST: Check Deployment and Service configurations")
def test_resource_existance(web_deploy, web_service_cip):
    assert web_deploy is not None, "Deployment does not exist"
    assert web_service_cip is not None, "ClusterIP Service for Web does not exist"


@pytest.mark.it("Check that Deployment is ready")
def test_deployment_state_is_ready(web_deploy):
    # Wait until the deployment is in the ready state and then
    # refresh its underlying object data
    web_deploy.wait_until_ready(timeout=60)
    assert web_deploy.is_ready() is True, "Deployment state is not READY"


@pytest.mark.it("Deployment should have 3 replicas available")
def test_deployment_replicas_count(web_deploy):
    web_deploy.refresh()
    ds = web_deploy.status()
    assert ds.replicas == 3, "Deployment MUST have 3 replicas"
    assert ds.ready_replicas == ds.replicas, "All replicas in Deployment MUST be ready"


@pytest.mark.it("Selector should return three pods")
def test_pods_count(pod_list_by_selector):
    assert (
        len(pod_list_by_selector) == 3
    ), "Selected less than 3 pods. WTF?"  # Redundant check there


@pytest.mark.it("HTTP response from Pod should contain its name")
def test_pods_http_reply(pod_list_by_selector):
    # Get the pod, ensure that it is ready,
    # check that index.html contains pod name
    for pn, pod in pod_list_by_selector.items():
        pod.wait_until_ready(timeout=30)
        http_check = pod.http_proxy_get("/index.html", port=8000)
        assert http_check.data.find(pn) != -1


@pytest.mark.it("Pod should have HTTP readiness probe defined")
def test_pods_readiness_probe(pod_list_by_selector):
    for pn, pod in pod_list_by_selector.items():
        assert pod.obj.spec.containers[0].readiness_probe.http_get is not None


@pytest.mark.it("Pod should have TCP liveness probe defined")
def test_pods_liveness_probe(pod_list_by_selector):
    for pn, pod in pod_list_by_selector.items():
        assert pod.obj.spec.containers[0].liveness_probe.tcp_socket is not None


@pytest.mark.it("Verify ClusterIP service configuration")
def test_service_cip(web_service_cip):
    assert (
        web_service_cip.is_ready() is True
    ), "Service is not ready (endpoints failing)"

    assert web_service_cip.obj.spec.type == "ClusterIP"
    assert web_service_cip.obj.spec.cluster_ip != "None"
    assert web_service_cip.obj.spec.ports[0].port == 80


@pytest.mark.it("wev-svc-cip Service should have 3 healthy endpoints")
def test_service_endpoints(web_service_cip):
    ep = web_service_cip.get_endpoints()
    assert len(ep[0].subsets[0].addresses) == 3


@pytest.mark.it("Connection to ClusterIP and port should return HTTP code 200 ")
def test_service_cip_connection(web_service_cip, test_pod):
    spec = web_service_cip.obj.spec
    test_pod.run_test(
        "wget -T 10 --spider http://{}:{}/index.html".format(
            spec.cluster_ip, spec.ports[0].port
        )
    )
