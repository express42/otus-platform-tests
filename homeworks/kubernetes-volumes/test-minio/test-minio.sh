#!/bin/sh
mc config host add minio http://minio-0.minio.default.svc.cluster.local:9000 minio minio123
if [ "$?" = "0" ]; then
	mc mb minio/bucket
    echo "Hello, Minio!" > hello.txt
    mc cp hello.txt minio/bucket
    echo "File uploaded"
    echo "Test passed!"
else
	echo "Cannot connecting to S3 storage" 1>&2
	exit 1
fi
