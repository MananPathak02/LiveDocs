from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = 'documents'
    room_name = Column(String, primary_key=True)
    content = Column(Text)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class Version(Base):
    __tablename__ = 'versions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_name = Column(String)
    content = Column(Text)
    saved_at = Column(DateTime, default=datetime.datetime.utcnow)

# DB Setup
engine = create_engine('sqlite:///documents.db')
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
