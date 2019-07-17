# Docker image otusplatform/test-minio
FROM minio/mc
WORKDIR /check
COPY test-minio.sh .
ENTRYPOINT [ "sh", "./test-minio.sh" ]