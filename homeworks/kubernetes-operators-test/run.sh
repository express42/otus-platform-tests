#!/bin/bash
set -xe

# Download kubectl
curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl 
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Download kind
curl -Lo kind https://github.com/kubernetes-sigs/kind/releases/download/v0.4.0/kind-linux-amd64
chmod +x kind 
sudo mv kind /usr/local/bin/

# Create kind cluster
kind create cluster --wait 300s
export KUBECONFIG="$(kind get kubeconfig-path)"

# Wait while all components in kube-system namespace will start
kubectl wait --for=condition=Ready pod --all -n kube-system --timeout=300s

# Deploy operator

kubectl apply -f kubernetes-operators/deploy/crd.yml
kubectl apply -f kubernetes-operators/deploy/service-account.yml
kubectl apply -f kubernetes-operators/deploy/role.yml
kubectl apply -f kubernetes-operators/deploy/role-binding.yml
kubectl apply -f kubernetes-operators/deploy/deploy-operator.yml
kubectl apply -f kubernetes-operators/deploy/cr.yml


kubectl wait --for=condition=Available deployment/mysql-operator --timeout=300s
sleep 10
export MYSQLPOD="$(kubectl get pods -l app=mysql-instance -o jsonpath="{.items[*].metadata.name}")"
kubectl wait --for=condition=Ready pod/$MYSQLPOD --timeout=300s

# Fill DB:

kubectl exec -it $MYSQLPOD -- mysql -u root -potuspassword -e "CREATE TABLE test ( id smallint unsigned not null auto_increment, name varchar(20) not null, constraint pk_example primary key (id) );" otus-database
kubectl exec -it $MYSQLPOD -- mysql -potuspassword -e "INSERT INTO test ( id, name ) VALUES ( null, 'some data' );" otus-database
kubectl exec -it $MYSQLPOD -- mysql -potuspassword -e "INSERT INTO test ( id, name ) VALUES ( null, 'some data-2' );" otus-database

# Redeploy mysql
kubectl delete -f kubernetes-operators/deploy/cr.yml
sleep 10
kubectl wait --for=condition=complete jobs/backup-mysql-instance-job
kubectl apply -f kubernetes-operators/deploy/cr.yml
sleep 10
kubectl wait --for=condition=complete jobs/restore-mysql-instance-job  --timeout=600s


# 
# content=$(kubectl exec -it $MYSQLPOD -- mysql -potuspassword -e "select * from test;" otus-database)
# if [ `echo $content | egrep 'some data' | wc -l` -eq 2 ]; then echo passed && exit 0; else echo error; fi 

#check content
export MYSQLPOD="$(kubectl get pods -l app=mysql-instance -o jsonpath="{.items[*].metadata.name}")"
content="$(kubectl exec -it $MYSQLPOD -- bash -c 'MYSQL_PWD=otuspassword  mysql -ss -e "select count(*) from test where name LIKE \"some data%\";" otus-database')"

if [[$content == "2"]];
then 
    exit 0 
else 
    exit 1
