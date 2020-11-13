import logging
import re
import os
import sys
import requests
import time
from bs4 import BeautifulSoup
from core.login import Loginer

class LectureSelector(Loginer):
    def __init__(self, user_info, urls, interval):
        super().__init__(user_info, urls)
        self._logger = logging.getLogger("Lecture")
        self._S = requests.session()
        self._interval = interval

    def select_lecture(self):
        try:
            res = self._S.get(url=self._urls['lecture_info_url']['http'], headers=self.headers, timeout=5)
        except requests.Timeout:
            res = self._S.get(url=self._urls['lecture_info_url']['https'], headers=self.headers)
            
        bsobj = BeautifulSoup(res.text, "html.parser")
        table = bsobj.tbody
        tr_all = table.find_all("tr")
        for tr in tr_all:
            td_all = tr.find_all('td')
            name, _, lec_time, _, tea, _, op = td_all
            name = name.string
            lec_time = lec_time.string
            tea = tea.string
            if "预约已结束" in op.text:
                continue
            self._logger.info("讲座名称: {}".format(name))
            self._logger.info("讲座时间: {}".format(lec_time))
            self._logger.info("主讲人: {}".format(tea))
            _, click = op.find_all('a')
            text = click.attrs["onclick"]
            res = re.findall(r"'(.*?)'", text)
            rid, rtime = res
            data = {
                "lectureId": rid,
                "communicationAddress": rtime
            }
            try:
                res = self._S.post(url = self._urls['lecture_sign_url']['http'], headers=self.headers, data=data, timeout=5)
            except requests.Timeout:
                res = self._S.post(url = self._urls['lecture_sign_url']['http'], headers=self.headers, data=data)
            if res.text != "countFail":
                self._logger.warning("抢课成功")
                if self._urls['wechat_push_url'] and self._user_info['SCKEY']:
                    url = self._urls['wechat_push_url'] + self._user_info['SCKEY'] + ".send"
                    desp = ""
                    if name: desp += "讲座名称: " + name + "\n\n"
                    if lec_time: desp += "讲座时间: " + lec_time + "\n\n"
                    if tea: desp += "主讲人: " + tea + "\n\n"
                    desp += "当前时间: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "\n\n"
                    data = {
                        "text": "抢课成功",
                        "desp": desp
                    }
                    res = requests.post(url=url, data=data)
            print("===================================================")

    def run(self):
        self.login()
        while True:
            self._logger.info("开始抢课")
            self.select_lecture()
            self._logger.info("结束抢课")
            time.sleep(self._interval)