import logging
import random
import yaml
import os
import json
from datetime import datetime, date
from web_logger import get_logger
from kafka import KafkaProducer
from pollWebEvent import PollWebEvent
from kafka.errors import KafkaTimeoutError

logger = get_logger('web_poll_producer_app')

kafka_config = yaml.load(open(os.path.join(os.path.dirname(__file__), 'config', 'kafka_config.yml')), Loader=yaml.Loader)

class WebMonitorApp_P():
    def __init__(self, kafka_config):
        self.hostname = kafka_config['kafka-test']['hostname']
        self.port = kafka_config['kafka-test']['port']
        self.cert_folder = kafka_config['kafka-test']['cert_folder']
        self.pwe = PollWebEvent()
        self.producer = KafkaProducer(
            bootstrap_servers=self.hostname+":"+str(self.port),
            security_protocol="SSL",
            ssl_cafile=os.path.join(self.cert_folder, "ca.pem"),
            ssl_certfile=os.path.join(self.cert_folder, "service.cert"),
            ssl_keyfile=os.path.join(self.cert_folder, "service.key"),
            value_serializer=lambda v: json.dumps(v, default=self.json_serial).encode('utf-8'),
            key_serializer=lambda v: json.dumps(v, default=self.json_serial).encode('utf-8')
        )

    def run(self):
        """
        Main function which polls a list of web sites and pushes the metrices 
        to the poll_web topic.
        """
        logger.info(f'bootstrap_connected() - {self.producer.bootstrap_connected()}')

        while True:
            try:
                website = random.choice(self.pwe.websites)
                self.pwe.web_monitor(website.get('url'), regex=website.get('regex'))
            except:
                logger.error(f"Request failed for {website.get('url')}")
                continue

            try:
                logger.info(f"Sending message {self.pwe.topic_name} - {self.pwe.key} - {self.pwe.value}")
                self.producer.send(self.pwe.topic_name, key=self.pwe.key, value=self.pwe.value)
                self.producer.flush()
            except KafkaTimeoutError as e:
                logger.error(f"{e} {self.pwe.topic_name} - {self.pwe.key} - {self.pwe.value}")
                continue

    @staticmethod
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError ("Type %s not serializable" % type(obj))

if __name__ == '__main__':
    wm_p = WebMonitorApp_P(kafka_config)
    wm_p.run()
