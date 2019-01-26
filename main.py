from rest import app
from config import config


from klein import Klein


from twisted.internet import endpoints, reactor
from twisted.web.server import Site

if __name__ == '__main__':
    app.run(host=config["Listen"]["host"], port=config["Listen"]["port"])
