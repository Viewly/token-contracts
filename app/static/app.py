import os

from flask import (
    Flask,
    render_template,
)

app = Flask(__name__, template_folder='../templates', static_folder='../static')


@app.route('/')
def app_index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host=os.getenv('FLASK_HOST', '127.0.0.1'),
            debug=not os.getenv('PRODUCTION', False))
