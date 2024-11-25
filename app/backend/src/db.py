import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

db_user = os.environ["APP_DB_USER"]
db_password = os.environ["APP_DB_PASSWORD"]
db_host = "db"
db_name = os.environ["APP_DB_NAME"]
db_url = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
engine = create_engine(db_url, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def dispose():
    engine.dispose()


def create_db_and_tables():
    Base.metadata.create_all(engine)


def get_session():
    with SessionLocal() as session:
        yield session
