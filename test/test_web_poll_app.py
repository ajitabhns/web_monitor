import unittest
import psycopg2
import datetime
import yaml
import sys
import os
from kafka.structs import TopicPartition

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import db_writer
import pollWebEvent
import web_poll_consumer_app
import web_poll_producer_app

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
    def setUp(self):
        self.wm_c = web_poll_consumer_app.WebMonitorApp_C(web_poll_consumer_app.kafka_config)
        self.wm_p = web_poll_producer_app.WebMonitorApp_P(web_poll_producer_app.kafka_config)
        self.pwe = pollWebEvent.PollWebEvent()
        self.wm_c.consumer.subscribe([self.pwe.topic_name])

    def test_consumer_4(self):
        assert self.wm_c.consumer.topics() == {'poll_web'}

    def test_producer_5(self):
        website = self.pwe.websites[1]
        key, value = self.pwe.web_monitor(website.get('url'), regex=website.get('regex'))
        record_metadata = self.wm_p.producer.send(self.pwe.topic_name, key=key, value=value)
        self.wm_p.producer.flush()
        
        self.wm_c.consumer.topics()
        self.wm_c.consumer.poll()
        self.wm_c.consumer.seek(record_metadata.value.topic_partition, record_metadata.value.offset)
        res = self.wm_c.consumer.poll(100)

        if res:
            messages = res[TopicPartition(topic=self.pwe.topic_name, partition=0)]
            assert len(messages) == 1

            for message in messages:
                assert msg.offset == record_metadata.value.offset
                assert msg.key == key
                print(f'{message}')
                print(key)

    def tearDown(self):
        self.wm_c.consumer.close()

if __name__ == '__main__':
    unittest.main()
