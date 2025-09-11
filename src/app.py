from flask import Flask
from flask_cors import CORS
from routes.transacoes_routes import transacoes_bp
from routes.auth_routes import auth_bp
from routes.graficos_routes import charts_bp


app = Flask(__name__)
CORS(app)

app.register_blueprint(transacoes_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(charts_bp)

if __name__ == '__main__':
    app.run(debug=True)
