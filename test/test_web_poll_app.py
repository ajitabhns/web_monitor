import unittest
import psycopg2
import datetime
import yaml
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from db_writer import DBWriter
# from pollWebEvent import PollWebEvent
from src import db_writer
from src import pollWebEvent


class DBWriterTester(unittest.TestCase):
    def setUp(self):
        self.connect_str = db_writer.DBWriter.get_db_connect_str()
        self.conn = psycopg2.connect(self.connect_str)
        self.cur = self.conn.cursor()
        self.cur.execute(" \
                CREATE TABLE web_monitor_test(url text, \
                access_time timestamp, \
                error_code integer, \
                http_response_time_in_s text, \
                pattern_in_page boolean, \
                regex text, \
                primary key (url, access_time))")


    def test_db_writer_1(self):
        data = [{'url': 'http://www.google.com/', 
                'access_time': datetime.datetime(2021, 4, 25, 9, 40, 29, 624075), 
                'error_code': 200, 'http_response_time_in_s': 0.21, 
                'pattern_in_page': None, 
                'regex': None},

                {'url': 'https://docs.docker.com/compose/', 
                'access_time': datetime.datetime(2021, 4, 25, 9, 40, 29, 790505), 
                'error_code': 200, 
                'http_response_time_in_s': 0.15, 
                'pattern_in_page': True, 
                'regex': 'environment'},

                {'url': 'https://aiven.io/blog?posts=30', 
                'access_time': datetime.datetime(2021, 4, 25, 9, 40, 31, 433970), 
                'error_code': 200, 
                'http_response_time_in_s': 1.04, 
                'pattern_in_page': True, 
                'regex': 'cloud'}]

        for names in data:
            q1 = db_writer.DBWriter.create_query_string(names, table='web_monitor_test')
            self.cur.execute(q1, vars=names)
            self.cur.execute("SELECT * FROM web_monitor_test;")
            results = self.cur.fetchall()
        assert len(results) == 3

    def tearDown(self):
        self.cur.execute("DROP TABLE web_monitor_test")
        self.cur.close()
        self.conn.close()

class PollWebEventTester(unittest.TestCase):
    def setUp(self):
        self.pwe = pollWebEvent.PollWebEvent()

    def test_poll_web_event_1(self):
        website = self.pwe.websites[0]
        key, value = self.pwe.web_monitor(website.get('url'), regex=website.get('regex'))
        assert key['url'] == 'http://www.google.com/'
        assert value['pattern_in_page'] == None
        assert value['error_code'] == 200

    def test_poll_web_event_2(self):
        website = self.pwe.websites[1]
        key, value = self.pwe.web_monitor(website.get('url'), regex=website.get('regex'))
        assert key['url'] == 'https://docs.docker.com/compose/'
        assert value['pattern_in_page'] == True
        assert value['error_code'] == 200

    def test_poll_web_event_3(self):
        website = self.pwe.websites[3]
        key, value = self.pwe.web_monitor(website.get('url'), regex=website.get('regex'))
        assert key['url'] == 'https://docs.docker.com/copose/'
        assert value['pattern_in_page'] == False
        assert value['error_code'] == 403

class KafkaTester(unittest.TestCase):
    def setUp():
        pass

    def tearDown():
        pass

if __name__ == '__main__':
    unittest.main()
