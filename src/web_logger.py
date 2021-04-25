import logging
import yaml
import os

kafka_config = yaml.load(open(os.path.join(os.path.dirname(__file__), 'config', 'kafka_config.yml')), Loader=yaml.Loader)

def get_logger(name):
    logger = logging.getLogger(name)
    fmt = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(os.path.join(kafka_config['kafka-test']['log_path'], f'{name}.log'))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    return logger