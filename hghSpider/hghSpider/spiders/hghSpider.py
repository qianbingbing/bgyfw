# -*- coding: utf-8 -*-
from scrapy import Spider
from scrapy.http import Request
import ddddocr
import time
import requests
import base64
from selenium import webdriver
from hghSpider.settings import DEFAULT_REQUEST_HEADERS
from webdriver_manager.chrome import ChromeDriverManager
import datetime
import calendar
import json

class HghSpider(Spider):
    name = 'haoguihua'
    allowed_domains = ['bcsc2.bgyfw.com']
    order_list_url = 'https://bcsc2.bgyfw.com/bgyfw-gateway/sup/ps/order/getListByOthers?createTimeBegin={0}&createTimeEnd={1}&pageNo=1&pageSize=1000'
    order_detail_url = 'https://bcsc2.bgyfw.com/bgyfw-gateway/sup/ps/order/getDetailById?psOrderId={0}'
    invoice_info_url = 'https://bcsc2.bgyfw.com/bgyfw-gateway/sup/ps/order/queryInvoiceMsg?poOrderId={0}&psOrderId={1}'
    delivery_detail_url = 'https://bcsc2.bgyfw.com/bgyfw-gateway/sup/pd/delivery/getPrOrderDetailVOById?poOrderId={0}&prOrderId={1}&pdOrderId={2}'
    login_url = 'https://bcsc2.bgyfw.com/bgyfw-gateway/sup/login'


    def start_requests(self):
        # dcap = dict(DesiredCapabilities.CHROME)
        # dcap["phantomjs.page.settings.userAgent"] = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:25.0) Gecko/20100101 Firefox/25.0 ")
        # driver = webdriver.Chrome('./webdriver/chromedriver.exe')

        driver = webdriver.Chrome(ChromeDriverManager().install())
        while True:
            print("开始....")
            self.login(driver)
            if "产品管理" in driver.page_source:
                print('登陆成功')
                token = json.loads(driver.execute_script('return localStorage.getItem("pro__Access-Token");')).get('value')
                DEFAULT_REQUEST_HEADERS.update({"X-Access-Token":token})
                driver.quit()
                break
            else:
                self.login(driver)

        #获取对账单列表
        now = datetime.datetime.now()
        start_day = datetime.datetime(now.year,now.month,1).strftime('%Y-%m-%d')
        end_day = datetime.datetime(now.year,now.month,calendar.monthrange(now.year,now.month)[1]).strftime('%Y-%m-%d')
        print(start_day)
        print(end_day)
        result=requests.get(self.order_list_url.format(start_day,end_day),headers=DEFAULT_REQUEST_HEADERS)
        order_list = json.loads(result.text).get('result').get('records')
        index = 1
        for order in order_list:
            item_value = {}
            taxTotals = order.get('taxTotals')

            #获取psOderId
            psOrderId = order.get("id")
            print(psOrderId)

            #获取对账单code
            psOrderCode = order.get("psOrderCode")

            #设置文件名称
            file_name = str(index) + "_" + str(psOrderCode) + '_' + str(taxTotals) + '.xlsx'
            item_value['file_name'] = file_name

            #获取对账单详情
            order_details_resp = requests.get(self.order_detail_url.format(psOrderId), headers=DEFAULT_REQUEST_HEADERS)
            order_details = json.loads(order_details_resp.text)

            #获取订单poOderid
            orderId = order_details.get('result').get('poOrderId')


            #获取对账单明细列表
            psOrderSubDetailVOList = order_details.get('result').get('psOrderSubDetailVOList')
            pdOrderItemVOLists = []
            for psOrderSubDetail in psOrderSubDetailVOList:
                poOrderId = psOrderSubDetail.get('poOrderId')
                pdOrderId = psOrderSubDetail.get('pdOrderId')
                prOrderId = psOrderSubDetail.get('prOrderId')
                pdOrderCode = psOrderSubDetail.get('pdOrderCode')
                print(pdOrderCode)
                poOrderCode = psOrderSubDetail.get('poOrderCode')
                print(poOrderCode)

                delivery_detail_resp = requests.get(self.delivery_detail_url.format(poOrderId, prOrderId, pdOrderId),headers=DEFAULT_REQUEST_HEADERS)
                pdOrderItems= json.loads(delivery_detail_resp.text).get('result').get('prOrderProductDepartDetailVO').get('children')[0].get('children')[0].get('children')
                for item in pdOrderItems:
                    item_vaule = self.get_pdOrderItemVaule(item)
                    pdOrderItemVOLists.append(item_vaule)
            item_value['result_list'] = pdOrderItemVOLists
            index +=1
            yield Request(self.invoice_info_url.format(orderId,psOrderId), headers=DEFAULT_REQUEST_HEADERS,
                          callback=self.parse_item,meta={'item_value':item_value})

    def login(self,webdriver):
        webdriver.get('https://nbc-sup.bgyfw.com/#/home/index')
        webdriver.refresh()
        login_content = webdriver.find_element_by_class_name('login-content')
        login_content.find_element_by_xpath('//div[1]/div/div/span/input').clear()
        login_content.find_element_by_xpath('//div[1]/div/div/span/input').send_keys('china_dragon')
        login_content.find_element_by_xpath('//div[2]/div/div/span/input').clear()
        login_content.find_element_by_xpath('//div[2]/div/div/span/input').send_keys('WEIyx888')
        login_content.find_element_by_xpath('//div[3]/div[2]/img').click()
        time.sleep(2)
        img_base64 = login_content.find_element_by_xpath('//div[3]/div[2]/img').get_attribute('src')
        img_imf = img_base64.replace("data:image/jpg;base64", '')
        page_content = base64.b64decode(img_imf)
        ocr = ddddocr.DdddOcr()
        code = ocr.classification(page_content)
        print(code.lower())
        login_content.find_element_by_xpath('//div[3]/div[1]/div/div/div/span/input').send_keys(code)
        webdriver.find_element_by_xpath("//button[@type='button']").click()
        time.sleep(5)

    def get_pdOrderItemVaule(self,pdOrderItem):
        item = []
        #编号
        skuId = pdOrderItem.get('skuId')
        item.append(skuId)
        #商品名称
        productName = pdOrderItem.get('productName')
        item.append(productName)
        #发货数量
        shipQuantity = pdOrderItem.get('shipQuantity')
        item.append(shipQuantity)
        #已收货数量
        receiptQuantity = pdOrderItem.get('receiptQuantity')
        item.append(receiptQuantity)
        #计量单位
        unit = pdOrderItem.get('unit')
        item.append(unit)
        #含税单价
        taxPrice = pdOrderItem.get('taxPrice')
        item.append(taxPrice)
        #含税金额小计
        totalPrice = pdOrderItem.get('totalPrice')
        item.append(totalPrice)
        return item

    def parse_item(self,response):

        #获取商品信息
        item_value = response.meta['item_value']

        # 获取发票信息
        invoice_result = json.loads(response.text).get('result')

        '''解析发票信息'''
        invoice_info = []
        # 发票抬头
        invoiceTitle = invoice_result.get('invoiceTitle')
        invoice_info.append(invoiceTitle)
        # 纳税人识别号
        taxCode = invoice_result.get('taxCode')
        invoice_info.append(taxCode)
        # 地址
        address = invoice_result.get('address')
        invoice_info.append(address)
        # 电话
        tel = invoice_result.get('tel')
        invoice_info.append(tel)
        # 发票类型
        invoiceTypeText = invoice_result.get('invoiceTypeText')
        invoice_info.append(invoiceTypeText)
        # 开户银行
        bank = invoice_result.get('bank')
        invoice_info.append(bank)
        # 银行账户
        bankNo = invoice_result.get('bankNo')
        invoice_info.append(bankNo)
        # 收票单位
        billToParty = invoice_result.get('billToParty')
        invoice_info.append(billToParty)
        # 收票人
        billToer = invoice_result.get('billToer')
        invoice_info.append(billToer)
        # 收票人联系方式
        billToContact = invoice_result.get('billToContact')
        invoice_info.append(billToContact)
        item_value['invoice_info'] = invoice_info

        return item_value







