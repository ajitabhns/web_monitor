from kafka import KafkaProducer
import json
import os
import logging
from datetime import date, datetime

logger = logging.getLogger('web_poll_consumer_app.producer')

class Producer():
    def __init__(self, hostname, port, cert_folder):
        self.producer = KafkaProducer(
            bootstrap_servers=hostname+":"+str(port),
            security_protocol="SSL",
            ssl_cafile=os.path.join(cert_folder, "ca.pem"),
            ssl_certfile=os.path.join(cert_folder, "service.cert"),
            ssl_keyfile=os.path.join(cert_folder, "service.key"),
            value_serializer=lambda v: json.dumps(v, default=self.json_serial).encode('utf-8'),
            key_serializer=lambda v: json.dumps(v, default=self.json_serial).encode('utf-8')
        )

    @staticmethod
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError ("Type %s not serializable" % type(obj))


    def send(self, topic_name, key, value):
        self.producer.send(
            topic_name,
            key=key,
            value=value
        )

        self.producer.flush()