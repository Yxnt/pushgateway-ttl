from prometheus_client.parser import text_string_to_metric_families
import logging
from requests import session
from urllib.parse import urljoin
from os import environ
from typing import Tuple, AnyStr, NoReturn
import requests
import time

req_session = session()
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)


def get_env() -> Tuple:
    TTL = int(environ.get('TTL', '10'))
    PUSHGATEWAY_URL = environ.get('PUSHGATEWAY_URL', '')
    PUSH_WEBHOOK_URL = environ.get('PUSH_WEBHOOK_URL', '')
    return TTL, PUSHGATEWAY_URL, PUSH_WEBHOOK_URL


def push_message_to_webhook(webhook_url: str, msg: str) -> NoReturn:
    try:
        requests.post(webhook_url, json={"text": msg}, timeout=3)
    except Exception as e:
        logging.warning("请求webhook异常")


def get_metrics(request_url: str) -> NoReturn:
    resp = req_session.get(request_url, timeout=10)
    assert resp.status_code == 200, "请求 metrics 接口出错"
    return resp.text


def delete_expired_job(request_url: str) -> NoReturn:
    resp = req_session.delete(request_url)
    if resp.status_code == 202:
        logging.info("删除 job 成功")
    else:
        logging.info("删除 job 失败")


def parse_metrics(ttl: int, metrics_text: str) -> AnyStr:
    cur_time = time.time()
    families = text_string_to_metric_families(metrics_text)
    for family in families:
        for sample in family.samples:
            if sample.name == 'push_time_seconds':
                if cur_time - sample.value > ttl:
                    job_name = sample.labels['job']
                    yield job_name


def main():
    ttl, pushgateway_url, webhook_url = get_env()
    metrics_url = urljoin(pushgateway_url, '/metrics')
    while True:
        metrics_data = get_metrics(metrics_url)
        for job in parse_metrics(ttl, metrics_data):
            message = f"获取到过期的 job: {job}"
            push_message_to_webhook(webhook_url, msg=message)
            logging.info(message)
            job_url = urljoin(pushgateway_url, f'/metrics/job/{job}')
            message = f'开始删除过期 job: {job}'
            logging.info(message)
            delete_expired_job(job_url)

        time.sleep(ttl)


if __name__ == '__main__':
    main()
