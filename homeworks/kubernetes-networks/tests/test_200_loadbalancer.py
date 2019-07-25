import pytest


"""
Fixture definitions. Common fixtures, such as toolbox pod are in conftest.py
"""


@pytest.fixture(scope="module")
def web_service_lb(request, kube_module):
    # Wait for Service to be ready on the cluster
    sm = kube_module.load_service("./kubernetes-networks/web-svc-lb.yaml")
    sm.create()
    kube_module.wait_for_registered(timeout=30)
    services = kube_module.get_services()
    s = services.get("web-svc-lb")
    s.wait_until_ready(timeout=30)
    yield s


"""
Actual tests code below. Fixtures are called and created as needed
"""


@pytest.mark.it("TEST: Check LoadBalancer and MetalLB configurations")
def test_resource_existance(web_deploy, web_service_lb):
    assert web_deploy is not None, "Deployment does not exist"
    assert web_service_lb is not None, "LoadBalancer Service for Web does not exist"


@pytest.mark.it("Verify Web LoadBalancer service configuration")
def test_service_lb(web_service_lb):
    assert web_service_lb.is_ready() is True, "Service is not ready (endpoints failing)"

    assert web_service_lb.obj.spec.type == "LoadBalancer"
    assert web_service_lb.obj.spec.ports[0].port == 80


@pytest.mark.it("wev-svc-lb Service should have 3 healthy endpoints")
def test_lb_service_endpoints(web_service_lb):
    ep = web_service_lb.get_endpoints()
    assert len(ep[0].subsets[0].addresses) == 3
