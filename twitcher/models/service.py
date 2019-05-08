from sqlalchemy import (
    Column,
    Index,
    Integer,
    Boolean,
    Text,
)

from .meta import Base


class Service(Base):
    __tablename__ = 'services'
    id = Column(Integer, primary_key=True)
    url = Column(Text)
    name = Column(Text)
    type = Column(Text)
    purl = Column(Text)
    # public = Column(Boolean)
    auth = Column(Text)
    # verify = Column(Boolean)


Index('name_index', Service.name, unique=True, mysql_length=255)
