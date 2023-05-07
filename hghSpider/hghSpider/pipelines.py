# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from openpyxl import Workbook
import os
import shutil

class ExcelPipeline(object):
    def __init__(self):
        self.old_file_name = ""
        self.current_file_name = ""
        self.clean_old_file(os.path.join(os.getcwd(), "export_data"))

    def clean_old_file(self,file_path):
        ls = os.listdir(file_path)
        try:
            for i in ls:
                c_path = os.path.join(file_path, i)
                if os.path.isdir(c_path):
                    shutil.rmtree(c_path,True)
                else:
                    os.remove(c_path)
        except Exception as e:
            print(e)

    def process_item(self, item, spider):
        item.setdefault('file_name', '')
        item.setdefault('invoice_info', '')
        item.setdefault('result_list', '')
        invoice_info_list = item['invoice_info']
        result_lines = item['result_list']
        file_name = item['file_name']
        if file_name:
            self.current_file_name = os.path.join(os.getcwd(), "export_data\\" + file_name)
        if self.old_file_name == "" or self.current_file_name !=self.old_file_name:
            self.wb = Workbook()
            self.ws = self.wb.active

        if self.ws.max_row == 1:
            self.ws.append(['序号', '发票抬头', '纳税人识别号', '地址', '电话', '发票类型', '开户银行', '银行账号', '收票单位', '收票人', '收票人联系方式'])
            self.ws.append(invoice_info_list)
            self.ws.append(['编号', '商品名称', '发货数量', '已收货数量', '计量单位', '含税单价', '含税金额小计'])
        if result_lines:
            for line in result_lines:
                self.ws.append(line)
            self.wb.save(self.current_file_name)

        self.old_file_name = self.current_file_name
        return item
    def close_spider(self, spider):
        # 关闭
        self.wb.close()
        pass

