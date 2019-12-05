package tests

import (
	"fmt"
	"path/filepath"
	"strings"
	"testing"
	"time"

	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"github.com/stretchr/testify/require"

	"github.com/gruntwork-io/terratest/modules/k8s"
	"github.com/gruntwork-io/terratest/modules/random"
)

func TestKubernetesFrontendReplicaSet(t *testing.T) {
	t.Parallel()

	kubeResourcePath, err := filepath.Abs("../frontend-replicaset.yaml")
	require.NoError(t, err)

	namespaceName := fmt.Sprintf("kubernetes-controllers-%s", strings.ToLower(random.UniqueId()))

	options := k8s.NewKubectlOptions("", "", namespaceName)
	filters := metav1.ListOptions{
		LabelSelector: "app=frontend",
	}

	k8s.CreateNamespace(t, options, namespaceName)
	defer k8s.DeleteNamespace(t, options, namespaceName)
	defer k8s.KubectlDelete(t, options, kubeResourcePath)

	k8s.KubectlApply(t, options, kubeResourcePath)

	k8s.WaitUntilNumPodsCreated(t, options, filters, 3, 10, 5*time.Second)

	for _, pod := range k8s.ListPods(t, options, filters) {
		k8s.WaitUntilPodAvailable(t, options, pod.Name, 10, 5*time.Second)
	}

	for _, pod := range k8s.ListPods(t, options, filters) {
		require.True(t, pod.Status.ContainerStatuses[0].Ready, "All pods should be Ready")
	}
}
