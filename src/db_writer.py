import psycopg2
from psycopg2 import sql
import os
import datetime
import json
import logging
import yaml

logger = logging.getLogger('web_poll_consumer_app.db_writer')

db_config = yaml.load(open(os.path.join(os.path.dirname(__file__), 'config', 'db_config.yml')), Loader=yaml.Loader)

class DBWriter():
    """
    A DB helper class to perform database operations
    """
    def __init__(self, db_connect_str=None):
        if not db_connect_str:
            db_connect_str = self.get_db_connect_str()
        self.db_connect_str = db_connect_str

    @staticmethod
    def get_db_connect_str():
        return f"dbname={db_config['pg-test']['db_name']} \
                    user={db_config['pg-test']['db_user']} \
                    password={db_config['pg-test']['db_password']} \
                    host={db_config['pg-test']['db_host']} \
                    port={db_config['pg-test']['db_port']}"

    @staticmethod
    def create_query_string(vars=None, table='web_monitor'):
        q1 = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(', ').join(map(sql.Identifier, vars.keys())),
            sql.SQL(', ').join(map(sql.Placeholder, vars))
        )
        return q1
    
    def execute(self, q, vars=None):
        try:
            with psycopg2.connect(self.db_connect_str) as conn:
                with conn.cursor() as cur:
                    logger.info(cur.mogrify(q, vars))
                    cur.execute(q, vars=vars)
            conn.close()
        except psycopg2.Error as e:
            logger.error(f'{e.diag.severity} - {e.diag.message_primary}')

# def json_serial(obj):
#     """JSON serializer for objects not serializable by default json code"""

#     if isinstance(obj, (datetime, date)):
#         return obj.isoformat()
#     raise TypeError ("Type %s not serializable" % type(obj))

if __name__ == '__main__':
    key = {'url': 'https://docs.docker.com/compose/', 'access_time': datetime.datetime(2021, 4, 23, 22, 14, 44, 989032)} 
    value = {'error_code': 200, 'http_response_time_in_s': 0.08, 'pattern_in_page': True, 'regex': 'test'}
    names = {**key, **value}
    db_writer = DBWriter()
    q1 = db_writer.create_query_string(names)
    db_writer.execute(q1, vars=names)