from kafka import KafkaConsumer
import json
import logging
import random
import os
from db_writer import DBWriter
from pollWebEvent import PollWebEvent

logger = logging.getLogger('web_poll_consumer_app.consumer')

class Consumer():
    def __init__(self, hostname, port, group_id, cert_folder):
        self.consumer = KafkaConsumer(
            client_id = "client1",
            group_id = group_id,
            bootstrap_servers = hostname+":"+str(port),
            security_protocol = "SSL",
            ssl_cafile=os.path.join(cert_folder, "ca.pem"),
            ssl_certfile=os.path.join(cert_folder, "service.cert"),
            ssl_keyfile=os.path.join(cert_folder, "service.key"),
            value_deserializer = lambda v: json.loads(v.decode('utf-8')),
            key_deserializer = lambda v: json.loads(v.decode('utf-8')),
            max_poll_records = 10
        )

    def subscribe(self, topic_name):
        self.consumer.subscribe(topics=[topic_name])
        logger.info(self.consumer.topics())

    def close(self):
        self.consumer.close()

    def run(self):
        db_writer = DBWriter()

        for message in self.consumer:
            try:
                logger.info(f"{message.partition} - {message.offset}: k={message.key} v={message.value}")
                names = {**message.key, **message.value}
                q1 = db_writer.create_query_string(names)
                db_writer.execute(q1, vars=names)
            except:
                logger.error(f"Failed to write message - {message.key} to db")