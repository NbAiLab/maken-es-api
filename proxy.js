// npm install http-proxy
var http = require('http');
var httpProxy = require('http-proxy');
var proxy = httpProxy.createProxyServer({secure: false});
var TARGET = process.env.TARGET || "http://localhost:9200";
var PORT = process.env.PORT || 3000;

http.createServer(function(req, res) {
    console.info(`http://localhost:${PORT} -> ${TARGET}${req.url}`)
    proxy.web(req, res, { target: TARGET });
}).listen(PORT);
