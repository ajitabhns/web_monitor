import logging
import random
import yaml
import os
import json
from kafka import KafkaConsumer
from web_logger import get_logger
from db_writer import DBWriter
from pollWebEvent import PollWebEvent

from kafka.errors import KafkaError

kafka_config = yaml.load(open(os.path.join(os.path.dirname(__file__), 'config', 'kafka_config.yml')), Loader=yaml.Loader)    

logger = get_logger('web_poll_consumer_app')

MAX_RECORDS_BATCH = 100

class WebMonitorApp_C():
    def __init__(self, kafka_config):
        self.hostname = kafka_config['kafka-test']['hostname']
        self.port = kafka_config['kafka-test']['port']
        self.cert_folder = kafka_config['kafka-test']['cert_folder']
        self.pwe = PollWebEvent()
        self.db_writer = DBWriter()
        self.names = []
        self.q1 = None
        self.consumer = KafkaConsumer(
            client_id = "client1",
            group_id = "demo_group",
            bootstrap_servers = self.hostname+":"+str(self.port),
            security_protocol = "SSL",
            ssl_cafile=os.path.join(self.cert_folder, "ca.pem"),
            ssl_certfile=os.path.join(self.cert_folder, "service.cert"),
            ssl_keyfile=os.path.join(self.cert_folder, "service.key"),
            value_deserializer = lambda v: json.loads(v.decode('utf-8')),
            key_deserializer = lambda v: json.loads(v.decode('utf-8')),
            max_poll_records = 100
        )

    def run(self):
        """
        Main function which pulls the web poll metrices from the web_poll topic
        and pushes the data to the table web_monitor.
        """
      
        try:
            logger.info(f'bootstrap_connected() - {self.consumer.bootstrap_connected()}')
            self.consumer.subscribe([self.pwe.topic_name])
            
            for message in self.consumer:
                try:
                    logger.info(f"{message.partition} - {message.offset}: k={message.key} v={message.value}")
                    kv = {**message.key, **message.value}
                    self.names.append(kv)

                    if not (len(self.names) % MAX_RECORDS_BATCH):
                        if not self.q1:
                            self.q1 = self.db_writer.create_query_string(kv.keys())
                        self.db_writer.execute(self.q1, self.names)
                        self.names = []
                except Exception as e:
                    import traceback
                    logger.error(traceback.format_exc())
                    logger.error(f"Failed to write message - {message.key} to db")
        except KafkaError as exc:
            logger.error(f'Exception during subscribing to topic - {exc}')
            raise
        finally:
            self.db_writer.close()
            self.consumer.close()
       
if __name__ == '__main__':
    wm_c = WebMonitorApp_C(kafka_config)
    wm_c.run()