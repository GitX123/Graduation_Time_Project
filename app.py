from flask import Flask, request, render_template
import utility

app = Flask(__name__)
app.debug = True
# [TODO] set up private key

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    return utility.search(data)

if __name__ == '__main__':
    app.run()