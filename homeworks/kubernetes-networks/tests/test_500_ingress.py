import pytest

"""
Fixture definitions. Common fixtures, such as toolbox pod are in conftest.py
"""


@pytest.fixture(scope="module")
def web_service_headless(request, kube_module):
    # Wait for Service to be ready on the cluster
    sm = kube_module.load_service("./kubernetes-networks/web-svc-headless.yaml")
    sm.create()
    kube_module.wait_for_registered(timeout=30)
    services = kube_module.get_services()
    s = services.get("web-svc")
    s.wait_until_ready(timeout=60)
    yield s


"""
Actual tests code below. Fixtures are called and created as needed
"""


@pytest.mark.it("TEST: Check ingress-nginx configurations")
def test_resource_existance(web_deploy, web_service_headless):
    assert web_deploy is not None, "Deployment does not exist"
    assert (
        web_service_headless is not None
    ), "LoadBalancer Service for Web does not exist"


@pytest.mark.it("Verify Headless service configuration")
def test_service_headless(web_service_headless):
    assert (
        web_service_headless.is_ready() is True
    ), "Service is not ready (endpoints failing)"

    assert web_service_headless.obj.spec.type == "ClusterIP"
    assert web_service_headless.obj.spec.cluster_ip == "None"
    assert web_service_headless.obj.spec.ports[0].port == 80


@pytest.mark.it("wev-svc-headless Service should have 3 healthy endpoints")
def test_headless_service_endpoints(web_service_headless):
    ep = web_service_headless.get_endpoints()
    assert len(ep[0].subsets[0].addresses) == 3