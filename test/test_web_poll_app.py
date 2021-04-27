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
    """
    Test cases for DBWriter class
    """
    def setUp(self):
        self.db_writer = db_writer.DBWriter()
        self.db_writer.cur.execute(" \
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

        q1 = db_writer.DBWriter.create_query_string(data[0].keys(), table='web_monitor_test')
        self.db_writer.execute(q1, data)
        self.db_writer.cur.execute("SELECT * FROM web_monitor_test;")
        results = self.db_writer.cur.fetchall()
        assert len(results) == 3

    def tearDown(self):
        self.db_writer.cur.execute("DROP TABLE web_monitor_test")
        self.db_writer.conn.commit()
        self.db_writer.cur.close()
        self.db_writer.conn.close()

class PollWebEventTester(unittest.TestCase):
    """
    Test cases for pollWebEvent class
    """
    def setUp(self):
        self.pwe = pollWebEvent.PollWebEvent()

    def test_poll_web_event_2(self):
        website = self.pwe.websites[0]
        self.pwe.web_monitor(website.get('url'), regex=website.get('regex'))
        assert self.pwe.key['url'] == 'http://www.google.com/'
        assert self.pwe.value['pattern_in_page'] == None
        assert self.pwe.value['error_code'] == 200

    def test_poll_web_event_3(self):
        website = self.pwe.websites[1]
        self.pwe.web_monitor(website.get('url'), regex=website.get('regex'))
        assert self.pwe.key['url'] == 'https://docs.docker.com/compose/'
        assert self.pwe.value['pattern_in_page'] == True
        assert self.pwe.value['error_code'] == 200

    def test_poll_web_event_4(self):
        website = self.pwe.websites[3]
        self.pwe.web_monitor(website.get('url'), regex=website.get('regex'))
        assert self.pwe.key['url'] == 'https://docs.docker.com/copose/'
        assert self.pwe.value['pattern_in_page'] == False
        assert self.pwe.value['error_code'] == 403

class KafkaTester(unittest.TestCase):
    """
    Testcases for kafka consumer/producer classes (WebMonitorApp_C, WebMonitorApp_P)
    """
    def setUp(self):
        self.wm_c = web_poll_consumer_app.WebMonitorApp_C(web_poll_consumer_app.kafka_config)
        self.wm_p = web_poll_producer_app.WebMonitorApp_P(web_poll_producer_app.kafka_config)
        self.pwe = pollWebEvent.PollWebEvent()
        self.wm_c.consumer.subscribe([self.pwe.topic_name])

    def test_kafka_5(self):
        assert self.wm_c.consumer.topics() == {'poll_web'}

    def test_kafka_6(self):
        website = self.pwe.websites[1]
        self.pwe.web_monitor(website.get('url'), regex=website.get('regex'))
        record_metadata = self.wm_p.producer.send(self.pwe.topic_name, key=self.pwe.key, value=self.pwe.value)
        self.wm_p.producer.flush()
        
        self.wm_c.consumer.topics()
        self.wm_c.consumer.poll()
        self.wm_c.consumer.seek(record_metadata.value.topic_partition, record_metadata.value.offset)
        res = self.wm_c.consumer.poll(100)

        if res:
            messages = res[TopicPartition(topic=self.pwe.topic_name, partition=0)]
            assert len(messages) == 1

            for message in messages:
                assert message.offset == record_metadata.value.offset
                assert message.key['url'] == self.pwe.key['url']
                assert message.key['access_time'] == self.pwe.key['access_time'].isoformat()
                assert message.value['error_code'] == self.pwe.value['error_code']
                assert message.value['http_response_time_in_s'] == self.pwe.value['http_response_time_in_s']
                assert message.value['pattern_in_page'] == self.pwe.value['pattern_in_page']
                assert message.value['regex'] == self.pwe.value['regex']

    def tearDown(self):
        self.wm_c.consumer.close()

if __name__ == '__main__':
    unittest.main()
