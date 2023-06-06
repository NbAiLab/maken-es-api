# Maken Elasticsearch Configs

This repo contains a few instructions on setting up Open Distro for Elasticsearch (ES) for the National Library of Norway AI-Lab similarity (maken) service.

1. Create a new VM. Make sure you have allowed access to its IP on ports 9200, 5600 and 5602.
2. Follow the instructions in OpenDistro to install Open Distro for Elasticsearch: https://opendistro.github.io/for-elasticsearch-docs/docs/install/deb/ Additionally, the Kibana dashboard can also be installed: https://opendistro.github.io/for-elasticsearch-docs/docs/kibana/#run-kibana-using-the-rpm-or-debian-package
3. Since in most cases ES will be secured by internal IT, disable SSL and HTTPS. If self-signed, you'll need to run a local proxy for connecting GUIs like [Elasticvue](https://github.com/cars10/elasticvue), as in `PORT=3000 TARGET=https://user:pass@192.168.34.21:9200 node proxy.js`, and then connect to `http://localhost:3000` instead.

Data could be ingested using [maken-es-data](https://github.com/nbailab/maken-es-data). Once Elasticsearch is running with some data, the API can be deployed using Docker as follows:

```bash
$ docker build -t maken-es-api .
$ docker run -d -p 80:80 -e ES_HOST=192.166.0.10 --name maken-es-api maken-es-api
```

There are a few optional parameters to connect to Elasticsearch that can be set using environment variables:

- `ES_HOST`, to set host IP or name. Defaults to `localhost`
- `ES_PORT`, to set port. Defaults to `9200`
- `ES_USER`, to set user. Defaults to `admin`
- `ES_PASS`, to set password. Defaults to `admin`
- `ES_TIMEOUT`, to set a request timeout. Defaults to `60`
- `ES_MAX_RETRIES`, to set the max number of retries. Defaults to `300`

Once up, OpenAPI documentation can be accessed at `/docs`. A test site can be found at [api.nb.no/maken](https://api.nb.no/maken/docs).

For development, it can be useful to run it using uvicorn:

```bash
$ uvicorn app.main:app
```
