"""
SQLAlchemy models for the Haggle Service Marketplace.

Only Provider is persisted to the database.
Job objects live in memory and flow to the voice agent.
"""

from sqlalchemy import Column, Integer, String, Float, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

Base = declarative_base()


class Provider(Base):
    """
    Provider model - the ONLY thing persisted to the database.
    
    Stores service providers found via Grok Fast Search.
    """
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    estimated_price = Column(Float, nullable=True)
    raw_result = Column(JSON, default={})

    def __repr__(self):
        return f"<Provider(id={self.id}, name='{self.name}', phone='{self.phone}')>"


# Database setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database, creating all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

