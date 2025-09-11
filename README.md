# Invoice Analyzer - Backend

Backend simples em **Flask** para análise de faturas em CSV e PDF, integrado ao frontend em **Next.js**. Permite login, upload de faturas e análise de transações.

## Tecnologias

- **Python 3.11+**  
- **Flask 3**  
- **Flask-CORS**  
- **SQLAlchemy**  
- **Pandas / NumPy**  
- **pdfplumber / pdfminer.six / pypdfium2**  
- **JWT para autenticação**  
- **Gunicorn** (deploy)

## Deploy

🔗 Frontend: [Invoice Analyzer](https://invoice-analyzer-frontend.vercel.app/)

(Backend rodando local ou via deploy próprio, link não fornecido)

## Login para testes

```json
{
  "username": "teste1",
  "password": "123456"
}
