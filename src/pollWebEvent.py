import requests
import datetime
import re
import random
import yaml
import logging
import os
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger('web_poll_producer_app.pollWebEvent')

class Event:
    def __init__(self):
        self.key = None
        self.value = None
        self.topic_name = None

class PollWebEvent(Event):
    """
    A web poller using requests module to poll a url and collect HTTP
    response time, error code and oprtional regex pattern match
    """
    def __init__(self):
        super(PollWebEvent, self).__init__()
        self.topic_name = 'poll_web'
        self.websites = self.get_web_config()

    @staticmethod
    def get_web_config():
        with open(os.path.join(os.path.dirname(__file__), 'config', 'websites.yml')) as f:
            web_config = yaml.load(f, Loader=yaml.Loader)
        return web_config['websites']


    def web_monitor(self, url, regex=None):
        pattern_in_page = None
        http_response_time_in_s = None
        error_code = None

        self.key = {
            "url": url,
            "access_time": datetime.datetime.now()
        }

        try:
            res = requests.get(url, verify=False)

            http_response_time_in_s = round(res.elapsed.total_seconds(), 2)
            error_code = res.status_code

            if regex:
                pattern_in_page = re.search(regex, res.text) and True or False
        except requests.exceptions.ConnectionError:
            error_code = 521
            logger.error(f"Request failed for {url}!!!")
        
        self.value = {
            "error_code": error_code,
            "http_response_time_in_s": http_response_time_in_s,
            "pattern_in_page": pattern_in_page,
            "regex": regex
        }
    
if __name__ == '__main__':
    pwe = PollWebEvent()
    for website in pwe.websites:
        pwe.web_monitor(website.get('url'), regex=website.get('regex'))
        logger.info(f'{pwe.key}-{pwe.value}')
