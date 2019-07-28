from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from nanumlectures import settings
from nanumlectures.settings import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

DB_CONN_PARAMS = (DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME)

if not settings.INIT:
    DB_CONN_PARAMS = (os.environ['RDS_USERNAME'], os.environ['RDS_PASSWORD'], os.environ['RDS_HOSTNAME'],
                      os.environ['RDS_PORT'], os.environ['RDS_DB_NAME'])

engine_url = 'postgresql+psycopg2://{0}:{1}@{2}:{3}/{4}'.format(*DB_CONN_PARAMS)

engine = create_engine(engine_url, convert_unicode=True, echo=False)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import nanumlectures.models
    Base.metadata.create_all(bind=engine)

    from social_flask_sqlalchemy import models
    models.PSABase.metadata.create_all(bind=engine)


def drop_db():
    from social_flask_sqlalchemy import models
    models.PSABase.metadata.drop_all(bind=engine)

    Base.metadata.drop_all(bind=engine)
