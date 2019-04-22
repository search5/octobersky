from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

db_user, db_password, db_name = ('october_sky', 'db_user_password', 'october_sky')
db_connection_name = '<db_connection_name>'
engine_url = 'postgresql+psycopg2://{0}:{1}@'.format(db_user, db_password)

if os.environ.get('GAE_ENV') == 'standard':
    # If deployed, use the local socket interface for accessing Cloud SQL
    host = '/cloudsql/{}'.format(db_connection_name)
    engine_url = '{0}/{1}?host={2}'.format(engine_url, db_name, host)
else:
    host, db_user, db_password, db_name = (
        "localhost", 'october_sky', 'db_user_password', 'october_sky')
    engine_url = '{0}{1}:5434/{2}'.format(engine_url, host, db_name)

engine = create_engine(engine_url, convert_unicode=True, echo=True)
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
