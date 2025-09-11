from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from .usuario import Usuario

class Transacao(Base):
    __tablename__ = 'transacoes'

    id = Column(Integer, primary_key=True)
    data = Column(Date)
    descricao = Column(String)
    valor = Column(Float)
    categoria = Column(String)
    user_id = Column(Integer, ForeignKey('usuarios.id'))
    usuario = relationship("Usuario", backref="transacoes")
