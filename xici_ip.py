#!usr/bin/python
# -*- coding: utf-8 -*-
import requests
import queue
import threading
from lxml import etree

# 要爬取的URL
url = "http://www.we123.com/gzh/onclick/"

# 代理ip网站
proxy_url = "https://www.kuaidaili.com/free/inha/{page}/"


class MyThreadPool:
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self._pool = queue.Queue(maxsize)
        for _ in range(maxsize):
            self._pool.put(threading.Thread)

    def get_thread(self):
        return self._pool.get()

    def add_thread(self):
        self._pool.put(threading.Thread)


def get_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
        }
    response = requests.get(url, headers=headers)
    html_str = response.text
    return html_str


def proxy_get_url(url, prox):
    proxies = {}
    proxies["http"] = prox
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
        }
    response = requests.get(url, headers=headers, proxies=proxies, timeout=3)
    html_str = response.text
    return html_str


def ip_proxy(html_str):
    html = etree.HTML(html_str)
    ip_list = html.xpath('//tr/td[@data-title="IP"]/text()')
    port_list = html.xpath('//tr/td[@data-title="PORT"]/text()')
    http_list = []
    for i in range(len(ip_list)):
        http_proxy = ip_list[i] + ":" + port_list[i]
        http_list.append(http_proxy)
    return http_list


def available_ip(ip_list):
    for ip in ip_list:
        try:
            proxy_get_url('https://www.baidu.com/', ip)
        except Exception as e:
            continue
        IP_LIST.append(ip)


if __name__ == "__main__":
    IP_LIST = []
    pool = MyThreadPool(20)  # 线程池数
    # 验证代理ip
    for i in range(1, 20):  # 页数
        page_ip = get_url(proxy_url.format(page=i))
        ip_list = ip_proxy(page_ip)
        t = pool.get_thread()
        obj = t(target=available_ip, args=(ip_list,))
        obj.start()
    # 爬取网站
    for ip in IP_LIST:
        try:
            proxy_get_url(url, ip)
        except Exception as e:
            continue
        txt_path = u'H:/pycharmPro/zsxq/qggzh/proxy_ip.txt'
        with open(txt_path, 'a+', encoding='utf-8') as f:
            msg = 'http#{}\n'.format(ip)
            f.write(msg)
            print(ip)