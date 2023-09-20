# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
import logging
import requests
import toml
import os
from parsel import Selector
from urllib.parse import urljoin

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)
cwd = os.getcwd()
env = os.environ.get("CONFIG")


def read_config(config_file):
    if os.path.isfile(os.path.join(cwd,config_file)):
        config = toml.load(config_file)
    else:
        config = toml.loads(env)
    cookies = config.get("COOKIES")
    url = config.get("URL")
    pushtoken = config.get("PUSHTOKEN")
    if not cookies or not url:
        logger.error("未在配置文件找到用户cookie或者天使动漫网址")
        return
    return (cookies, url.get("base_url"),pushtoken.get("token"))


def tsdm_login(cookie):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.36 Safari/537.36 Edg/97.0.1072.28",
        "Cookie": cookie,
    }
    login_url = urljoin(base_url, "forum.php")
    session = requests.Session()
    session.headers = headers
    login_response = session.get(login_url)
    selector = Selector(text=login_response.text)
    if selector.css("#ls_username") and selector.css("#ls_password"):
        logger.error("cookie已经失效，请重新登录获取cookie")
        return
    return session


def tsdm_work(session):
    work_url = urljoin(base_url, "plugin.php?id=np_cliworkdz:work")
    response = session.get(work_url)
    tips = Selector(text=response.text).xpath('//*[@id="messagetext"]/p[1]/text()')
    if tips:
        logger.info("打工%s" % "".join(tips.getall()))
        return None
    for n in range(1, 7):
        session.post(work_url, data={"act": "clickad"})
        logger.info("正在点击第%s广告" % n)
    response = session.post(work_url, data={"act": "getcre"})
    message = "打工完成，%s" % "".join(
        Selector(text=response.text)
        .css("#messagetext.alert_info p")
        .re("<p>(.*?)<br>(.*?)<script")
    )
    logger.info(message)
    return message


def checkin(session):
    checkin_url = urljoin(base_url, "plugin.php?id=dsu_paulsign:sign")
    response = session.get(checkin_url)
    from_hash = (
        Selector(text=response.text).xpath('//*[@id="qiandao"]/input/@value').get()
    )
    if not from_hash:
        return "TSDM已经签到"
    checkin_api = urljoin(
        base_url, "plugin.php?id=dsu_paulsign:sign&operation=qiandao&infloat=1&inajax=1"
    )
    data = {"formhash": from_hash, "qdxq": "ch", "qdmode": 3, "fastreply": 0}
    checkin_response = session.post(checkin_api, data=data)
    logger.info("TSDM签到成功")
    return "TSDM签到成功"

def main():
    global base_url
    cookies, base_url,pushToken = read_config("config.toml")
    for user, cookie in cookies.items():
        session = tsdm_login(cookie)
        if session:
            msg1 = checkin(session)
            msg2 = tsdm_work(session)
            if pushToken != None and msg2 !=None:
                content = "今日天使动漫论坛签到打工！\n"+msg1+"\n"+msg2
                requests.post('https://www.pushplus.plus/send', { 'token': pushToken, 'title': '天使动漫签到', 'content': content });

if __name__ == "__main__":
    main()
