from consumer import Consumer
from db_writer import DBWriter
from pollWebEvent import PollWebEvent
import logging
import random
import yaml
import os
from web_logger import get_logger
from kafka.errors import KafkaError

kafka_config = yaml.load(open(os.path.join(os.path.dirname(__file__), 'config', 'kafka_config.yml')), Loader=yaml.Loader)    

logger = get_logger('web_poll_consumer_app')

def run_consumer():
    """
    Main function which pulls the web poll metrices from the web_poll topic
    and pushes the data to the table web_monitor.
    """
    hostname = kafka_config['kafka-test']['hostname']
    port = kafka_config['kafka-test']['port']
    cert_folder = kafka_config['kafka-test']['cert_folder']
    pwe = PollWebEvent()
    consumer = Consumer(hostname=hostname,
                        port=port,
                        group_id='demo_droup',
                        cert_folder=cert_folder)
    logger.info(f'bootstrap_connected() - {consumer.consumer.bootstrap_connected()}')
    try:
        consumer.subscribe(pwe.topic_name)
        consumer.run()
    except KafkaError as exc:
        logger.error(f'Exception during subscribing to topic - {exc}')
    finally:
        consumer.close()

if __name__ == '__main__':
    run_consumer()