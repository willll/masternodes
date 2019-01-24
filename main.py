from rest import app
from config import config

if __name__ == '__main__':
    app.run(host=config["Listen"]["host"], port=config["Listen"]["port"])