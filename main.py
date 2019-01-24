from rest import app,config

if __name__ == '__main__':
    app.run(host=config["Listen"]["host"], port=config["Listen"]["port"])