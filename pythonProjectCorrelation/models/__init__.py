from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine("sqlite:///assessment.db")
Session = sessionmaker(engine)
Base = declarative_base()




