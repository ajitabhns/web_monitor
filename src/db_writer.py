import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch
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
        self.conn = psycopg2.connect(self.db_connect_str)
        self.cur = self.conn.cursor()

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
            sql.SQL(', ').join(map(sql.Identifier, vars)),
            sql.SQL(', ').join(map(sql.Placeholder, vars))
        )
        logger.info(q1)
        return q1
    
    def execute(self, q, arglist):
        try:
            execute_batch(self.cur, q, arglist)
            self.conn.commit()
        except psycopg2.Error as e:
            logger.error(f'{e.diag.severity} - {e.diag.message_primary}')
            raise

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

# def json_serial(obj):
#     """JSON serializer for objects not serializable by default json code"""

#     if isinstance(obj, (datetime, date)):
#         return obj.isoformat()
#     raise TypeError ("Type %s not serializable" % type(obj))

if __name__ == '__main__':
    key = {'url': 'https://docs.docker.com/compose/', 'access_time': datetime.datetime(2022, 4, 23, 22, 14, 44, 989032)} 
    value = {'error_code': 200, 'http_response_time_in_s': 0.08, 'pattern_in_page': True, 'regex': 'test'}
    names = []

    for i in range(100):
        key['access_time'] += datetime.timedelta(0, i+1)
        kv = {**key, **value}
        names.append(kv)
    db_writer = DBWriter()
    q1 = db_writer.create_query_string(kv.keys())
    db_writer.execute(q1, names)
    db_writer.close()