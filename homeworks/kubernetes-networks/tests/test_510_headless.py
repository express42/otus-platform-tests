import subprocess
import pytest
import kubetest.objects
from kubernetes import config, client, utils
from ipaddress import ip_address, ip_network
from time import sleep
import logging

LOG = logging.getLogger(__name__)
"""
Fixture definitions. Common fixtures, such as toolbox pod are in conftest.py
"""
@pytest.fixture(scope="module")
def web_service_headless(kube_module, web_deploy) -> kubetest.objects.Service:
    svc = kube_module.load_service(
        "./kubernetes-networks/web-svc-headless.yaml")
    svc.create()
    kube_module.wait_until_created(svc, timeout=10)
    yield svc
    svc.delete(options=None)
    svc.wait_until_deleted()


@pytest.fixture(scope="module")
def web_ingress_rules(request, kube_module):
    manifest = "web-ingress"
    path = "./kubernetes-networks"
    manifest_string = "{path}/{fn}.yaml".format(fn=manifest, path=path)
    ns = kube_module.namespace

    log_pattern = "reason: 'CREATE' Ingress {}/web".format(ns)

    config.load_kube_config()
    k8s_client = client.ApiClient()

    utils.create_from_yaml(k8s_client, manifest_string, namespace=ns)
    # OMG. It's a kludge. We explicity wait until ingress-controller
    # catches the ingress rules. This bug is mostly Travis specific,
    # and I still haven't figured out programmatical way of getting
    # current backend state in ingress-nginx.
    sleep(3)

    def fin():  # Someday i'll do it better ))
        LOG.info('Calling Kubectl to delete objects from "%s" manifest',
                 manifest)
        subprocess.check_call(
            ["kubectl", "--namespace", ns, "delete", "-f", manifest_string])

    request.addfinalizer(fin)

    # Below goes an unsuccessful try on getting backend state. But it doesn't work
    # unfortunately.
    nginx_pods = kube_module.get_pods(namespace="ingress-nginx",
                                      labels={
                                          "app.kubernetes.io/name":
                                          "ingress-nginx",
                                          "app.kubernetes.io/component":
                                          "controller"
                                      })

    for pod in nginx_pods.values():
        container = pod.get_container(name="controller")
        count: int = 0
        while count < 3 and not container.search_logs(log_pattern):
            LOG.error(container.get_logs())
            sleep(3)
            count = count + 1


"""
Actual tests code below. Fixtures are called and created as needed
"""
@pytest.mark.usefixtures("ingress_nginx")
@pytest.mark.it("TEST: Check ingress-nginx installation")
def test_nginx_namespace_exists(kube):
    # This is kinda hack. Because we create Nginx directly via K8S APIClient, we have
    # to wait until namespace is available.
    # .new() creates object representation without calling K8s API
    ns = kubetest.objects.Namespace.new(name="ingress-nginx")
    kube.wait_until_created(ns, timeout=30)
    assert ns.is_ready() is True, 'Namespace "{}" doesn\'t exist'.format(
        ns.name)


@pytest.mark.it("Check Nginx LoadBalancer-service config and ready state")
def test_nginx_service_lb(nginx_svc_lb):
    nginx_svc_lb
    sleep(120)
    assert (nginx_svc_lb.is_ready() is
            True), "Nginx LB Service is not ready (endpoints failing)"

    spec = nginx_svc_lb.obj.spec
    assert (spec.type == "LoadBalancer"
            ), "Service type is not LoadBalancer - detected type is {}".format(
                spec.type)
    assert (spec.ports[0].port == 80
            ), "Service port is not 80 (detected port is {})".format(
                spec.ports[0].port)


@pytest.mark.it("Check Nginx LoadBalancer ingress IP address")
def test_nginx_lb_service_ingress(nginx_svc_lb):
    sleep(3)
    nginx_svc_lb.refresh()
    lb_ingress = nginx_svc_lb.obj.status.load_balancer.ingress
    assert lb_ingress is not None, "LoadBalancer ingress endpoint is not set"
    assert lb_ingress[
        0].ip is not None, "LoadBalancer ingress IP is not defined"
    assert (
        ip_address(lb_ingress[0].ip) in ip_network("172.17.255.0/24").hosts()
    ), "Assigned LB ingress IP ({})is not from 172.17.255.0/24 range".format(
        lb_ingress[0].ip)


@pytest.mark.it("TEST: Check headless service and Ingress configurations")
def test_svc_headless_resource_existance(web_service_headless):
    assert web_service_headless is not None, "Headless Service for Web does not exist"


@pytest.mark.it("Verify Headless service configuration")
def test_service_headless(web_service_headless):
    TYPE = "ClusterIP"

    assert (web_service_headless.is_ready() is
            True), "Service is not ready (endpoints failing)"

    spec = web_service_headless.obj.spec

    assert spec.type == TYPE, "Service type is not {} - detected type is {}".format(
        TYPE, spec.type)
    assert (spec.cluster_ip == "None"
            ), "clusterIP is set in service specification, should be 'None'"
    assert (spec.ports[0].port == 80
            ), "Service port is not 80 (detected port is {})".format(
                spec.ports[0].port)


@pytest.mark.it("wev-svc-headless Service should have 3 healthy endpoints")
def test_headless_service_endpoints(web_service_headless):
    ep = web_service_headless.get_endpoints()
    assert len(ep[0].subsets[0].addresses) == 3


@pytest.mark.it("Connect to headless service via Ingress-Nginx")
@pytest.mark.usefixtures("web_ingress_rules")
def test_ingress_external_connection(nginx_svc_lb, test_container):
    svc: kubetest.objects.Service = nginx_svc_lb
    results: Set[str] = set()
    pattern = "HOSTNAME"

    ip: str = svc.obj.status.load_balancer.ingress[0].ip
    assert ip is not None, "No IP address assigned for LoadBalancer service"

    url: str = "http://{}:{}/web/index.html".format(ip, "80")

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
