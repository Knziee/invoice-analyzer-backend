import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import json
from flask import Flask
from routes.graficos_routes import charts_bp  # importe o blueprint correto

@pytest.fixture
def client():
    """Cria um client de teste do Flask"""
    app = Flask(__name__)
    app.register_blueprint(charts_bp)  
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_charts_geral_endpoint(client):
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3NjAyMDI1OTF9.zXrrXvhP6_h0UT8nOWrDFdtY5mV0T3wv50mhJWBWwpU"

    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/charts/geral", headers=headers)

    assert response.status_code == 200

    data = json.loads(response.data)
    assert isinstance(data, dict)

    assert "soma_total" in data
    assert "meses" in data

