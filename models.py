from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

engine = create_engine('sqlite:///database.db')
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# ----------------------
# Modelo de transação
# ----------------------
class Transacao(Base):
    __tablename__ = 'database'
    id = Column(Integer, primary_key=True)
    data = Column(Date)
    descricao = Column(String)
    valor = Column(Float)
    categoria = Column(String)
    user_id = Column(Integer, ForeignKey('usuarios.id')) 
    usuario = relationship("Usuario", backref="database")

# ----------------------
# Modelo de usuários
# ----------------------
class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

Base.metadata.create_all(engine)
