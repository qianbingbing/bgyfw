# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals

class HghspiderSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class HghspiderDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


import base64
import logging
import requests
from scrapy import settings
import random
import json
import time
from collections import defaultdict
from scrapy.downloadermiddlewares.retry import RetryMiddleware
# proxyServer = "http://d.jghttp.golangapi.com/getip?num=100&type=2&pro=&city=0&yys=0&port=1&time=1&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=1&regions="
# proxyUser = ""
# proxyPass = ""
# proxyAuth = "Basic " + base64.urlsafe_b64encode(bytes((proxyUser + ":" + proxyPass), "ascii")).decode("utf8")

# class ProxyMiddleware(object):
#     def process_request(self, request, spider):
#         print(requests.get(proxyServer).text)
#         request.meta["proxy"] = proxyServer
#         request.headers["Proxy-Authorization"] = proxyAuth


#代理ip
class ProxyMiddleware():

    def __init__(self):
        # super(RetryMiddleware, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.proxy_list = []
        self.proxy = ''
        self.get_random_proxy()
        self.stats = defaultdict(int)  # 默认值是0    统计次数
        self.max_failed = 3

    def get_random_proxy(self):
        try:
            response = requests.get('http://d.jghttp.golangapi.com/getip?num=10&type=2&pro=&city=0&yys=0&port=1&time=1&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=1&regions=')
            if response.status_code == 200:
                ip_list = json.loads(response.text).get("data")
                print(ip_list)
                ip = ip_list[0].get('ip')
                port = ip_list[0].get('port')
                self.proxy = "{}:{}".format(ip, port)
                # self.proxy_list.append(proxy)
                # self.proxy = random.choice(self.proxy_list)
                print(self.proxy)
        except:
            print("请求地址错误")
            self.proxy = ''
    def process_request(self, request, spider):
        request.meta['proxy'] = self.proxy
        print("process_requset::::当前使用的代理{}".format(request.meta.get('proxy')))
    def process_response(self, request, response, spider):
        # 请求成功
        cur_proxy = request.meta.get('proxy')
        # 判断是否被对方禁封
        if response.status >= 400:
            # 给相应的ip失败次数 +1
            self.stats[cur_proxy] += 1
            print("当前ip{}，第{}次出现错误状态码".format(cur_proxy, self.stats[cur_proxy]))

        # 当某个ip的失败次数累计到一定数量
        if self.stats[cur_proxy] >= self.max_failed:  # 当前ip失败超过3次
            print("当前状态码是{}，代理{}可能被封了".format(response.status, cur_proxy))
            self.get_random_proxy()
            # 将这个请求重新给调度器，重新下载
            return request
        # 状态码正常的时候，正常返回
        return response
    def process_exception(self, request, exception, spider):

        from twisted.internet.error import ConnectionRefusedError, TimeoutError, TCPTimedOutError
        cur_proxy = request.meta.get('proxy')   # 取出当前代理
        print("process_exception::::当前请求：{}，当前异常：{}".format(request, exception))
        print("process_exception::::请求发生异常,异常请求的代理ip:{}====".format(cur_proxy))
        print("process_exception::::当前使用的代理ip:{}====".format(self.proxy))
        if '10061' in str(exception) or '10060' in str(exception):
            if self.proxy in cur_proxy:
                self.get_random_proxy()
                print("process_exception::::已重新分配，新的請求代理ip为: {}".format(request.meta.get('proxy')))
                time.sleep(5)

        if cur_proxy and isinstance(exception, (ConnectionRefusedError, TimeoutError,TCPTimedOutError)):
            if self.proxy in cur_proxy:
                self.get_random_proxy()
                print("process_exception::::已重新分配，新的請求代理ip为: {}".format(request.meta.get('proxy')))
                time.sleep(5)
        return request
        # 针对超时和无响应的reponse,获取新的IP,设置到request中，然后重新发起请求
        # if '10061' in str(exception) or '10060' in str(exception):
        #     self.get_random_proxy()
        #
        # if self.proxy:
        #     current_proxy = f'http://{self.proxy}'
        #     request.meta['proxy'] = current_proxy
        #
        # if isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get('dont_retry', False):
        #     return self._retry(request, exception, spider)


        # #self.stats[cur_proxy] += 1
        # print("=====请求发生异常,异常请求的代理ip:{}====".format(cur_proxy))
        # #if self.stats[cur_proxy] >= self.max_failed:  # 当前ip失败超过3次
        # print("=====当前使用的代理ip:{}====".format(self.proxy))
        # if self.proxy in cur_proxy:
        #     # self.proxy_list.remove(self.proxy)
        #     self.get_random_proxy()
        #     request.meta['proxy'] = self.proxy
        #     time.sleep(5)
        # print("已重新分配，新的請求代理ip为: {}".format(request.meta.get('proxy')))
        # # 重新下载这个请求
        # return request


        # 针对超时和无响应的reponse,获取新的IP,设置到request中，然后重新发起请求
        # if '10061' in str(exception) or '10060' in str(exception):
        #     cur_proxy = request.meta.get('proxy')
        #     self.stats[cur_proxy] += 1
        #     print("当前ip{}，第{}次出现错误".format(cur_proxy, self.stats[cur_proxy]))
        #
        # if self.stats[cur_proxy] >= self.max_failed:  # 当前ip失败超过3次
        #     self.get_random_proxy()
        #     return request
        #
        # if isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get('dont_retry', False):
        #     return self._retry(request, exception, spider)

    # def remove_proxy(self, proxy):
    #     if proxy in self.proxy_list:
    #         self.proxy_list.remove(proxy)
    #         print("从代理列表中删除{}".format(proxy))