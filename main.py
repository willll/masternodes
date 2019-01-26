from rest import app
from config import config


from klein import Klein


from twisted.internet import endpoints, reactor
from twisted.web.server import Site

if __name__ == '__main__':
    app.run(host=config["Listen"]["host"], port=config["Listen"]["port"])
    # Create desired endpoint
    endpoint_description = "tcp:port=9000:interface=127.0.0.1"
    endpoint = endpoints.serverFromString(reactor, endpoint_description)

    endpoint.listen(Site(app.resource()))


    reactor.suggestThreadPoolSize(8)
    reactor.run()