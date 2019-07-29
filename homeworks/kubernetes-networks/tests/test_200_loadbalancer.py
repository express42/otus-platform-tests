import pytest
import kubetest.objects
import ipaddress
from time import sleep

"""
Fixture definitions. Common fixtures, such as toolbox pod are in conftest.py
"""


@pytest.fixture(scope="module")
def web_service_lb(kube_module, web_deploy) -> kubetest.objects.Service:
    # Wait for Service to be ready on the cluster
    sm = kube_module.load_service("./kubernetes-networks/web-svc-lb.yaml")
    sm.create()
    kube_module.wait_until_created(sm, timeout=10)
    services = kube_module.get_services()
    s = services.get("web-svc-lb")
    yield s
    s.delete(options=None)
    s.wait_until_deleted()


"""
Actual tests code below. Fixtures are called and created as needed
"""


@pytest.mark.it("TEST: Check LoadBalancer and MetalLB configurations")
def test_svc_lb_resource_existance(web_service_lb):
    assert web_service_lb is not None, "LoadBalancer Service for Web does not exist"


@pytest.mark.it("Verify Web LoadBalancer service configuration")
def test_service_lb(web_service_lb):
    web_service_lb.wait_until_ready(timeout=30)

    assert web_service_lb.is_ready() is True, "Service is not ready (endpoints failing)"
    assert (
        web_service_lb.obj.spec.type == "LoadBalancer"
    ), "Service type is not LoadBalancer"
    assert web_service_lb.obj.spec.ports[0].port == 80, "Service port is not 80"


@pytest.mark.it("wev-svc-lb Service should have 3 healthy endpoints")
def test_lb_service_endpoints(web_service_lb):
    ep = web_service_lb.get_endpoints()
    assert len(ep[0].subsets[0].addresses) == 3


@pytest.mark.it("Check LoadBalancer ingress IP address")
def test_lb_service_ingress(web_service_lb):
    sleep(3)
    web_service_lb.refresh()
    lb_ingress = web_service_lb.obj.status.load_balancer.ingress
    assert lb_ingress is not None, "LoadBalancer ingress endpoint is not set"
    assert lb_ingress[0].ip is not None, "LoadBalancer ingress IP is not defined"
    assert (
        ipaddress.ip_address(lb_ingress[0].ip)
        in ipaddress.ip_network("172.17.255.0/24").hosts()
    ), "Assigned LB ingress IP is not from 172.17.255.0/24 range"


@pytest.mark.it("Verify external connectivity for web-svc-lb service")
def test_lb_external_connection(web_service_lb, test_container):
    ip = web_service_lb.obj.status.load_balancer.ingress[0].ip
    assert ip is not None
    res = list()
    for test in range(0, 4):
        res.append(
            test_container.check_output(
                "wget -T 10 -O- http://{}:{}/index.html | grep HOSTNAME".format(
                    ip, "80"
                )
            )
        )
    assert len(set(res)) > 1, "Requests are not balanced between pods"
