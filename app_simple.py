# We like to start out Flask apps with a simple app so
# that we feel comfortable we can connect to the app
# from other machines on our network

from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8080,debug=True)