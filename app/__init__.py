from flask import Flask, render_template
from .views import bp

# Flask 앱 팩토리 패턴

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        return render_template('index.html')

    app.register_blueprint(bp)

    return app 