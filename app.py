from flask import Flask, request
import utility

app = Flask(__name__)
app.debug = True

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    return utility.search(data)

if __name__ == '__main__':
    app.run()