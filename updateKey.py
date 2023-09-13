import configparser
import logging
from time import sleep

import requests
from flask import Flask

app = Flask(__name__)


def get_account():
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')
        user_names = config.get('account', 'user')
        pass_words = config.get('account', 'password')
    except Exception as e:
        print(e)
        return None
    account = []
    for (userName, passWord) in zip(user_names.split(','), pass_words.split(',')):
        account.append([userName, passWord])
    return account


def get_token(account):
    config = configparser.ConfigParser()
    access_tokens = []
    try:
        config.read('config.ini')
        url_base = config.get('server', 'url_base')
        url_base = url_base.split(',')
    except Exception as e:
        print(e)
        return None
    url_login = []
    for url in url_base:
        url_login.append(url + '/chatgpt/login')
    url_num = len(url_login)
    url_count = 0
    for (userName, passWord) in account:
        data = {
            'username': userName,
            'password': passWord
        }
        r = requests.post(url_login[url_count], json=data)
        if r.status_code == 200:
            access_token = r.json()['accessToken']
            access_tokens.append([access_token, url_count])
        else:
            # 输出当前账号到日志中
            logging.error(userName)
            print(r.status_code)
        sleep(20)
        if url_count == url_num - 1:
            url_count = 0
        else:
            url_count += 1
    return access_tokens


def update_key(mode):
    if mode == 1:
        # 先读取accessToken.txt文件中的内容
        access_tokens = None
        try:
            with open('accessToken.txt', 'r') as f:
                data = f.read()
            data = data.split(',')
            # 去除空token
            data = list(filter(None, data))
            access_tokens = []
            for item in data:
                access_tokens.append(item.split(';'))
        except Exception as e:
            app.logger.error(e)
            print(e)
        if access_tokens is not None:
            return access_tokens

    access_tokens = get_token(get_account())
    if access_tokens is None:
        return None
    with open('accessToken.txt', 'w') as f:
        for item in access_tokens:
            f.write(str(item[0]) + ';' + str(item[1]) + ',')
    return access_tokens


if __name__ == '__main__':
    update_key(0)
