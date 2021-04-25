from producer import Producer
from pollWebEvent import PollWebEvent
import logging
import random
import yaml
import os
from web_logger import get_logger

logger = get_logger('web_poll_producer_app')

kafka_config = yaml.load(open(os.path.join(os.path.dirname(__file__), 'config', 'kafka_config.yml')), Loader=yaml.Loader)   

def run_producer():
    """
    Main function which polls a list of web sites and pushes the metrices 
    to the poll_web topic.
    """
    hostname = kafka_config['kafka-test']['hostname']
    port = kafka_config['kafka-test']['port']
    cert_folder = kafka_config['kafka-test']['cert_folder']
    logger.info(f'hostname={hostname}, port={port}, cert_folder={cert_folder}')
    producer = Producer(hostname, port, cert_folder)
    logger.info(f'bootstrap_connected() - {producer.producer.bootstrap_connected()}')
    pwe = PollWebEvent()

    while True:
        try:
            website = random.choice(pwe.websites)
            key, value = pwe.web_monitor(website.get('url'), regex=website.get('regex'))
        except:
            logger.error(f"Request failed for {website.get('url')}")
            continue

        try:
            logger.info(f"Sending message {pwe.topic_name} - {key} - {value}")
            producer.send(pwe.topic_name, key, value)
        except:
            logger.error(f"Failed to send message {pwe.topic_name} - {key} - {value}")
            continue

if __name__ == '__main__':
    run_producer()
