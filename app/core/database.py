import uuid6
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


@event.listens_for(Base, "init", propagate=True)
def _set_uuid7_id(target, args, kwargs):
    """Assign a UUID7 string ID at object instantiation if not provided."""
    mapper = target.__class__.__mapper__
    if "id" in mapper.columns and "id" not in kwargs:
        col = mapper.columns["id"]
        if col.primary_key and col.type.python_type is str:
            kwargs["id"] = str(uuid6.uuid7())


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
