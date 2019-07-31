import pytest
import kubetest.objects
from kubernetes.client import models
from time import sleep
import yaml
import os
from kubetest.manifest import get_type, new_object

TEST_QUERY = "kubernetes.default.svc.cluster.local"

"""
these functions are copy-pasted shamelessly from kubetest.manifest.
The only difference - load_file **ignores** unknown manifest types
"""


def load_file(path):
    with open(path, "r") as f:
        manifests = yaml.load_all(f, Loader=yaml.SafeLoader)
        objs = []
        for manifest in manifests:
            obj_type = get_type(manifest)
            if obj_type is None:
                print(
                    "Unable to determine object type for manifest: {}".format(manifest)
                )
            else:
                objs.append(new_object(obj_type, manifest))
    return objs


def load_path(path):
    if not os.path.isdir(path):
        raise ValueError("{} is not a directory".format(path))

    objs = []
    for f in os.listdir(path):
        if os.path.splitext(f)[1].lower() in [".yaml", ".yml"]:
            objs = objs + load_file(os.path.join(path, f))
    return objs


"""
END
"""


def preload_manifests():
    try:
        objects = load_path("./kubernetes-networks")
    except ValueError:
        pass

    coredns_svc = [
        obj
        for obj in objects
        if isinstance(obj, models.V1Service)
        and obj.spec.selector == {"k8s-app": "kube-dns"}
    ]
    return coredns_svc


manifests = preload_manifests()

if len(manifests) == 0:
    pytest.skip("Skipping CoreDNS tests", allow_module_level=True)


def get_services_by_proto(proto_string=None) -> [models.V1Service]:
    svc_list = [obj for obj in manifests if obj.spec.ports[0].protocol == proto_string]
    return svc_list


@pytest.fixture(scope="module")
def coredns_tcp(kube_module) -> kubetest.objects.Service:
    svc_list = get_services_by_proto("TCP")
    svc = kubetest.objects.Service(svc_list[0])
    svc.create()
    kube_module.wait_until_created(svc, timeout=10)
    svc.wait_until_ready(timeout=10)
    yield svc
    svc.delete(options=None)
    svc.wait_until_deleted()


@pytest.fixture(scope="module")
def coredns_udp(kube_module) -> kubetest.objects.Service:
    svc_list = get_services_by_proto("UDP")
    svc = kubetest.objects.Service(svc_list[0])
    svc.create()
    kube_module.wait_until_created(svc, timeout=10)
    svc.wait_until_ready(timeout=10)
    yield svc
    svc.delete(options=None)
    svc.wait_until_deleted()


def get_lb_ip(service=None):
    ip = None
    count = 0
    while ip is None:
        if count == 3:
            break
        try:
            service.refresh()
            ip = service.obj.status.load_balancer.ingress[0].ip
        except TypeError:
            print("Still have no IP for {}. Retrying...".format(service.name))
            sleep(3)
            count = count + 1
            continue
    return ip


@pytest.mark.xfail(
    len(manifests) < 2,
    run=False,
    reason="TCP or UDP service for CoreDNS is not defined",
)
@pytest.mark.it("CoreDNS services MUST have the same LB ingress IP")
def test_coredns_shared_ip(coredns_tcp, coredns_udp):

    tcp_ip = get_lb_ip(coredns_tcp)
    udp_ip = get_lb_ip(coredns_udp)

    # tcp_ip, udp_ip = None, None
    # count = 0
    # while udp_ip is None or tcp_ip is None:
    #     if count == 3:
    #         break
    #     try:
    #         coredns_udp.refresh()
    #         coredns_tcp.refresh()

    #         udp_ip = coredns_udp.obj.status.load_balancer.ingress[0].ip
    #         tcp_ip = coredns_tcp.obj.status.load_balancer.ingress[0].ip
    #     except TypeError:
    #         print("Still have no IP. Retrying...")
    #         sleep(3)
    #         count = count + 1
    #         continue

    assert udp_ip == tcp_ip, "UDP ({}) and TCP({}) LB IPs don't match".format(
        udp_ip, tcp_ip
    )


@pytest.mark.xfail(
    get_services_by_proto("TCP") == list(),
    run=False,
    reason="TCP service for CoreDNS is not defined",
)
@pytest.mark.it("Verify CoreDNS via MetalLB. Using TCP")
def test_coredns_tcp(coredns_tcp, test_container):
    assert coredns_tcp is not None and isinstance(
        coredns_tcp, kubetest.objects.Service
    ), "CoreDNS Service for TCP Endpoint is not available"

    assert (
        coredns_tcp.obj.status.load_balancer is not dict()
    ), "LoadBalancer ingress status is not set. Is MetalLB available?"

    ip = get_lb_ip(coredns_tcp)

    assert ip is not None, "No IP address assigned for TCP endpoint"

    test_container.run("apk --no-cache -q add drill")
    assert (
        test_container.package("drill").is_installed is True
    ), "Can't bootstrap test container - curl is not installed"

    tcp = test_container.check_output(
        "drill -t {rec} @{ip}".format(ip=ip, rec=TEST_QUERY)
    )
    assert (
        tcp.find("NOERROR") != -1
    ), "CoreDNS is not accessible via TCP, output is {}".format(tcp)
    print(tcp)


@pytest.mark.xfail(
    get_services_by_proto("UDP") == list(),
    run=False,
    reason="UDP service for CoreDNS is not defined",
)
@pytest.mark.it("Verify CoreDNS via MetalLB. Using UDP")
def test_coredns_udp(coredns_udp, test_container):

    assert coredns_udp is not None and isinstance(
        coredns_udp, kubetest.objects.Service
    ), "CoreDNS Service for UDP Endpoint is not available"

    assert (
        coredns_udp.obj.status.load_balancer.ingress is not dict()
    ), "LoadBalancer ingress status is not set. Is MetalLB available?"

    ip = get_lb_ip(coredns_udp)
    assert ip is not None, "No IP address assigned for UDP endpoint"

    test_container.run("apk --no-cache -q add drill")
    assert (
        test_container.package("drill").is_installed is True
    ), "Can't bootstrap test container - curl is not installed"

    udp = test_container.check_output(
        "drill -u {rec} @{ip}".format(ip=ip, rec=TEST_QUERY)
    )

    assert (
        udp.find("NOERROR") != -1
    ), "CoreDNS is not accessible via UDP, output is {}".format(udp)
    print(udp)
