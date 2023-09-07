import configparser

import requests


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
    except Exception as e:
        print(e)
        return None
    url_login = url_base + '/chatgpt/login'
    for (userName, passWord) in account:
        data = {
            'username': userName,
            'password': passWord
        }
        r = requests.post(url_login, json=data)
        if r.status_code == 200:
            access_token = r.json()['accessToken']
            access_tokens.append(access_token)
        else:
            print(r.status_code)
    return access_tokens


def update_key():
    access_tokens = get_token(get_account())
    if access_tokens is None:
        return None
    with open('accessToken.txt', 'w') as f:
        for access_token in access_tokens:
            f.write(access_token + ',')
    return access_tokens


if __name__ == '__main__':
    update_key()
