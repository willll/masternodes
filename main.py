from rest import config
from rest import app

if __name__ == '__main__':
    app.run(host=config["Listen"]["host"], port=config["Listen"]["port"])