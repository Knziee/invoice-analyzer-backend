from flask import Flask
from flask_cors import CORS
from routes.transacoes import transacoes_bp
from routes.auth import auth_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(transacoes_bp)
app.register_blueprint(auth_bp)

if __name__ == '__main__':
    app.run(debug=True)
