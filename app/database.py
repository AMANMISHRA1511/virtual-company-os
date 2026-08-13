from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
engine=create_engine('sqlite:///./virtual_company.db',connect_args={'check_same_thread':False})
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
class Base(DeclarativeBase): pass
def get_db():
    db=SessionLocal()
    try: yield db
    finally: db.close()
