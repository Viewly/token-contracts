import os

from .sale import ViewlySale

from flask import Flask, render_template

app = Flask(__name__, template_folder='../templates', static_folder='../static')


@app.route('/')
def hello_world():
    sale = ViewlySale()
    return render_template(
        'index.html',
        sale_info=sale.sale_info(),
        current_round=sale.current_round(),
        is_running=sale.is_running(),
    )


if __name__ == '__main__':
    app.run(host=os.getenv('FLASK_HOST', '127.0.0.1'),
            debug=not os.getenv('PRODUCTION', False))
