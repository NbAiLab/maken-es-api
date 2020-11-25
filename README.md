# Maken Elasticsearch Configs

This repo contains a few instructions on setting up Open Distro for Elasticsearch (ES) for the National Library of Norway AI-Lab similarity (maken) service.

1. Create a new VM. Make sure you have allowed access to its IP on ports 9200, 5600 and 5602.
2. Follow the instructions in OpenDistro to install Open Distro for Elasticsearch: https://opendistro.github.io/for-elasticsearch-docs/docs/install/deb/ Additionally, the Kibana dashboard can also be installed: https://opendistro.github.io/for-elasticsearch-docs/docs/kibana/#run-kibana-using-the-rpm-or-debian-package
3. Since in most cases ES will be secured by internal IT, disable SSL and HTTPS by editing the file:...
