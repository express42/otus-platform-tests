import pytest
import kubetest.objects
import yaml

import logging

LOG = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def metallb_configmap(kube_module, metallb):
    cm = kube_module.load_configmap(
        "./kubernetes-networks/metallb-config.yaml", set_namespace=False
    )
    kube_module.wait_until_created(cm, timeout=5)
    yield cm


@pytest.mark.it("TEST: Check MetalLB installation")
@pytest.mark.usefixtures("metallb")
def test_metallb_namespace_exists(kube_module):
    # This is kinda hack. Because we create MetalLB directly via K8S APIClient, we have
    # to wait until namespace is available.
    # .new() creates object representation without calling K8s API
    ns = kubetest.objects.Namespace.new(name="metallb-system")
    kube_module.wait_until_created(ns, timeout=5)
    assert ns.is_ready() is True, 'Namespace "{}" doesn\'t exist'.format(ns.name)


@pytest.mark.it("Verify ConfigMap parameters")
def test_metallb_configmap(metallb_configmap):
    assert metallb_configmap.is_ready() is True, "ConfigMap for MetalLB doesn't exist"

    config_data = yaml.load(
        metallb_configmap.obj.data.get("config"), Loader=yaml.BaseLoader
    )

    pool = config_data["address-pools"][0]
    assert (
        pool["protocol"] == "layer2"
    ), "MetalLB should use Layer-2 mode, but {} configured".format(pool["protocol"])

    POOL = "172.17.255.1-172.17.255.254"

    assert (
        pool["addresses"][0] == POOL
    ), "First address pool MUST be '{}', got {} instead".format(
        POOL, pool["addresses"][0]
    )


@pytest.mark.it("Verify state of MetalLB speaker pods")
def test_metallb_speaker_pods(kube):
    speaker_list = dict()
    speaker_list = kube.get_pods(
        labels={"app": "metallb", "component": "speaker"}, namespace="metallb-system"
    )
    assert len(speaker_list) > 0, "MetalLB Speakers are not running"
    for pn, o_pod in speaker_list.items():
        o_pod.wait_until_ready(timeout=10)
        assert o_pod.is_ready() is True, "{} pod is not ready".format(pn)


@pytest.mark.it("Verify state of MetalLB controller pods")
@pytest.mark.usefixtures("metallb")
def test_metallb_controller_pods(kube):

    controller_list = dict()
    controller_list = kube.get_pods(
        labels={"app": "metallb", "component": "controller"}, namespace="metallb-system"
    )
    assert len(controller_list) > 0, "MetalLB Controllers are not running"
    for pn, o_pod in controller_list.items():
        o_pod.wait_until_ready(timeout=10)
        assert o_pod.is_ready() is True, "{} pod is not ready".format(pn)
