from ipaddress import ip_address, ip_network
from time import sleep
from typing import List, Set
import pytest
import kubetest.objects
"""
Fixture definitions. Common fixtures, such as toolbox pod are in conftest.py
"""
@pytest.fixture(scope="module")
def web_service_lb(kube_module, web_deploy) -> kubetest.objects.Service:
    svc = kube_module.load_service("./kubernetes-networks/web-svc-lb.yaml")
    svc.create()
    kube_module.wait_until_created(svc, timeout=30)
    yield svc
    svc.delete(options=None)
    svc.wait_until_deleted()


"""
Actual tests code below. Fixtures are called and created as needed
"""
@pytest.mark.it("TEST: Check LoadBalancer service configurations")
def test_svc_lb_resource_existance(web_service_lb):
    assert web_service_lb is not None, "LoadBalancer Service for Web does not exist"


@pytest.mark.it("Verify Web LoadBalancer service configuration")
def test_service_lb(web_service_lb):
    web_service_lb.wait_until_ready(timeout=30)

    assert web_service_lb.is_ready(
    ) is True, "Service is not ready (endpoints failing)"

    spec = web_service_lb.obj.spec
    assert (spec.type == "LoadBalancer"
            ), "Service type is not LoadBalancer - detected type is {}".format(
                spec.type)
    assert (spec.ports[0].port == 80
            ), "Service port is not 80 (detected port is {})".format(
                spec.ports[0].port)


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
    assert lb_ingress[
        0].ip is not None, "LoadBalancer ingress IP is not defined"
    assert (
        ip_address(lb_ingress[0].ip) in ip_network("172.18.255.0/24").hosts()
    ), "Assigned LB ingress IP ({})is not from 172.18.255.0/24 range".format(
        lb_ingress[0].ip)


@pytest.mark.it("Verify external connectivity for web-svc-lb service")
def test_lb_external_connection(web_service_lb, test_container) -> None:
    svc: kubetest.objects.Service = web_service_lb
    results: Set[str] = set()
    pattern = "HOSTNAME"

    ip: str = svc.obj.status.load_balancer.ingress[0].ip
    assert ip is not None, "No IP address assigned for LoadBalancer service"

    url: str = "http://{}:{}/index.html".format(ip, "80")

    test_container.run("apk --no-cache -q add curl")
    assert (test_container.package("curl").is_installed is
            True), "Curl installation failed"

    for test in range(5):
        out: str = test_container.check_output(
            "curl --connect-timeout 10 -kL -sS {}".format(url))
        # Splits output by lines, then adds matching lines to resulting set
        results.update([l for l in out.splitlines() if pattern in l])
        assert (
            results
        ), "Pattern '{}' was not found in Pod's response\nOutput was:\n{}".format(
            pattern, out)
    assert (
        len(results) > 1
    ), "Got the same value for {} in 5 responses. Check balancing or page contents:\n{}".format(
        pattern, results)
