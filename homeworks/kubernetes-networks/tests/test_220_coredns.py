import logging
from time import sleep
from typing import Dict, List, Optional
import os
import yaml
from kubernetes.client import models
from kubetest.manifest import get_type, new_object
import kubetest.objects
import pytest
import testinfra.host

LOG = logging.getLogger(__name__)
TEST_QUERY = "kubernetes.default.svc.cluster.local"
"""
these functions are copy-pasted shamelessly from kubetest.manifest.
The only difference - load_file **ignores** unknown manifest types
'Raises' is simply replaced with 'Print' call. That's all.
"""


def load_file(path: str) -> List[object]:
    """ Loads manifest from YAML file and returns kubetest ApiObjects"""
    with open(path, "r") as input_file:
        manifests = yaml.load_all(input_file, Loader=yaml.SafeLoader)
        objs: List[object] = list()
        for manifest in manifests:
            obj_type: Optional[object] = get_type(manifest)
            if obj_type is None:
                LOG.warning("Unable to determine object type for manifest:",
                            manifest)
            else:
                objs.append(new_object(obj_type, manifest))
    return objs


def load_path(path: str) -> List[object]:
    """ Calls load_file for all YAML files in the specified directory """
    if not os.path.isdir(path):
        raise ValueError("{} is not a directory".format(path))

    objs: List[object] = list()
    for file_name in os.listdir(path):
        if os.path.splitext(file_name)[1].lower() in [".yaml", ".yml"]:
            objs = objs + load_file(os.path.join(path, file_name))
    return objs


# Kubetest copy-paste END


def preload_manifests(path: str,
                      selector: Dict[str, str]) -> List[models.V1Service]:
    """
    Loads all manifest files from dir, and returns a list of all
    Service objects with matching selector in spec
    """
    try:
        objects = load_path(path)
    except ValueError:
        pass

    coredns_svc = [
        obj for obj in objects
        if isinstance(obj, models.V1Service) and obj.spec.selector == selector
    ]
    return coredns_svc


MANIFESTS = preload_manifests(path="./kubernetes-networks",
                              selector={"k8s-app": "kube-dns"})

if not MANIFESTS:
    pytest.skip("Skipping CoreDNS tests", allow_module_level=True)


def get_services_by_proto(proto_string: str) -> List[models.V1Service]:
    return [
        obj for obj in MANIFESTS if obj.spec.ports[0].protocol == proto_string
    ]


@pytest.fixture(scope="module")
def coredns_tcp(kube_module: kubetest.client.TestClient
                ) -> kubetest.objects.Service:
    """ Return instance of CoreDNS LoadBalancer service for TCP endpoint"""
    svc_list = get_services_by_proto("TCP")
    svc = kubetest.objects.Service(svc_list[0])
    svc.create()
    kube_module.wait_until_created(svc, timeout=10)
    svc.wait_until_ready(timeout=10)
    yield svc
    svc.delete(options=None)
    svc.wait_until_deleted()


@pytest.fixture(scope="module")
def coredns_udp(kube_module: kubetest.client.TestClient
                ) -> kubetest.objects.Service:
    """ Return instance of CoreDNS LoadBalancer service for UDP endpoint"""
    svc_list = get_services_by_proto("UDP")
    svc = kubetest.objects.Service(svc_list[0])
    svc.create()
    kube_module.wait_until_created(svc, timeout=10)
    svc.wait_until_ready(timeout=10)
    yield svc
    svc.delete(options=None)
    svc.wait_until_deleted()


def get_lb_ip(service: kubetest.objects.Service) -> Optional[str]:
    """ Returns IP address of LoadBalancer-assigned Ingress or None """
    ip: Optional[str] = None
    count: int = 0
    while ip is None:
        if count == 3:
            break
        try:
            service.refresh()
            ip = service.obj.status.load_balancer.ingress[0].ip
        except TypeError:
            LOG.info("Still have no IP for %s. Retrying...", service.name)
            sleep(3)
            count = count + 1
            continue
    return ip


@pytest.mark.xfail(
    len(MANIFESTS) < 2,
    run=False,
    reason="TCP or UDP service for CoreDNS is not defined",
)
@pytest.mark.it("CoreDNS services MUST have the same LB ingress IP")
def test_coredns_shared_ip(coredns_tcp: kubetest.objects.Service,
                           coredns_udp: kubetest.objects.Service) -> None:

    tcp_ip: Optional[str] = get_lb_ip(coredns_tcp)
    udp_ip: Optional[str] = get_lb_ip(coredns_udp)

    assert udp_ip == tcp_ip, "UDP ({}) and TCP({}) LB IPs don't match".format(
        udp_ip, tcp_ip)


@pytest.mark.xfail(
    get_services_by_proto("TCP") == list(),
    run=False,
    reason="TCP service for CoreDNS is not defined",
)
@pytest.mark.it("Verify CoreDNS via MetalLB. Using TCP")
def test_coredns_tcp(coredns_tcp: kubetest.objects.Service,
                     test_container: testinfra.host.Host) -> None:
    assert isinstance(coredns_tcp, kubetest.objects.Service
                      ), "CoreDNS Service for TCP Endpoint is not available"

    assert (coredns_tcp.obj.status.load_balancer != {}
            ), "LoadBalancer ingress status is not set. Is MetalLB available?"

    ip: Optional[str] = get_lb_ip(coredns_tcp)
    assert ip is not None, "No IP address assigned for TCP endpoint"

    test_container.run("apk --no-cache -q add drill")
    assert (test_container.package("drill").is_installed is
            True), "Can't bootstrap test container - curl is not installed"

    tcp: str = test_container.check_output("drill -t {rec} @{ip}".format(
        ip=ip, rec=TEST_QUERY))
    assert (tcp.find("NOERROR") !=
            -1), "CoreDNS is not accessible via TCP, output is {}".format(tcp)
    LOG.info(tcp)


@pytest.mark.xfail(
    get_services_by_proto("UDP") == list(),
    run=False,
    reason="UDP service for CoreDNS is not defined",
)
@pytest.mark.it("Verify CoreDNS via MetalLB. Using UDP")
def test_coredns_udp(coredns_udp: kubetest.objects.Service,
                     test_container: testinfra.host.Host) -> None:

    assert coredns_udp is not None and isinstance(
        coredns_udp, kubetest.objects.Service
    ), "CoreDNS Service for UDP Endpoint is not available"

    assert (coredns_udp.obj.status.load_balancer.ingress != {}
            ), "LoadBalancer ingress status is not set. Is MetalLB available?"

    ip: Optional[str] = get_lb_ip(coredns_udp)
    assert ip is not None, "No IP address assigned for UDP endpoint"

    test_container.run("apk --no-cache -q add drill")
    assert (test_container.package("drill").is_installed is
            True), "Can't bootstrap test container - curl is not installed"

    udp: str = test_container.check_output("drill -u {rec} @{ip}".format(
        ip=ip, rec=TEST_QUERY))

    assert (udp.find("NOERROR") !=
            -1), "CoreDNS is not accessible via UDP, output is {}".format(udp)
    LOG.info(udp)
