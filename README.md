# Web Monitoring App

A kafka producer-consumer system which polls multiple websites periodically and put the resulting metrices to a backend PostgreSQL database

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install contents in the requirements.txt in the project.

```bash
pip3 install -r requirements.txt
```

## Usage

### Consumer
```bash
py web_poll_consumer_app.py
```
### Producer
```bash
py web_poll_producer_app.py
```
