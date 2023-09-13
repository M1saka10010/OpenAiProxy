import configparser
import logging
from queue import Queue
from threading import Thread

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, Response, stream_with_context, request
from flask_apscheduler import APScheduler
from gevent import sleep

import updateKey

app = Flask(__name__)
app.config['SCHEDULER_API_ENABLED'] = True
scheduler = APScheduler(BackgroundScheduler(timezone="Asia/Shanghai"))
scheduler.init_app(app)
scheduler.start()

# 读取配置文件
config = configparser.ConfigParser()

try:
    config.read('config.ini')
except Exception as e:
    app.logger.error(e)
    print(e)
    exit(-1)
if not config.getboolean('settings', 'debug'):
    import warnings

    warnings.filterwarnings("ignore")
# 用于存储访问令牌的队列
access_token_queue = Queue()
is_refreshing = False


def update_key(mode=0):
    global is_refreshing
    if is_refreshing:
        return None
    is_refreshing = True
    access_tokens = updateKey.update_key(mode)
    if access_tokens is None:
        return None
    global access_token_queue
    # 清空队列
    while not access_token_queue.empty():
        access_token_queue.get()
    for access_token in access_tokens:
        access_token_queue.put(access_token)
    is_refreshing = False


update_key(1)


def push_access_token(access_token):
    global access_token_queue
    wait_time = config.getint('settings', 'wait_time')
    # 检查访问令牌是否可用
    url_base = config.get('server', 'url_base')
    url_base = url_base.split(',')
    url_check = url_base[access_token[1]] + '/chatgpt/backend-api/accounts/check'
    headers = {
        'Authorization': f'Bearer {access_token[0]}'
    }
    sleep(wait_time)
    r = requests.get(url_check, headers=headers)
    if r.status_code == 200:
        access_token_queue.put(access_token)
    else:
        print(f'访问令牌 {access_token} 不可用')


# 创建一个装饰器用于从队列中获取访问令牌并处理请求
def get_access_token(func):
    def decorator(*args, **kwargs):
        global access_token_queue
        count = config.getint('settings', 'wait_time')
        while access_token_queue.empty() and count > 0:
            sleep(1)
            count -= 1
        if access_token_queue.empty():
            return Response(status=503)
        access_token = access_token_queue.get()
        # 传递访问令牌
        response = func(access_token, *args, **kwargs)
        # 将访问令牌放回队列
        Thread(target=push_access_token, args=(access_token,)).start()
        return response

    return decorator


@app.route('/v1/chat/completions', methods=['POST'])
@get_access_token
def reverse_proxy(access_token):
    url_base = config.get('server', 'url_base')
    url_base = url_base.split(',')
    # 获取api_key
    api_key = config.get('server', 'api_key')
    # 鉴权
    token = request.headers.get('Authorization')
    if token != api_key:
        if token != 'Bearer ' + api_key:
            return Response(status=401)

    url = []
    for base in url_base:
        url.append(f'{base}/imitate/v1/chat/completions')

    # 构建请求头
    headers = {
        'Authorization': f'Bearer {access_token[0]}'
    }

    # 构建请求
    r = requests.request(request.method, url[access_token[1]], headers=headers, data=request.data, stream=True)
    response = Response(stream_with_context(r.iter_content(chunk_size=1024)))
    response.headers['content-type'] = r.headers.get('content-type')
    return response


@app.route('/pool/count', methods=['GET'])
def pool_count():
    global access_token_queue
    return str(access_token_queue.qsize())


@app.route('/pool/refresh', methods=['GET'])
def pool_refresh():
    global is_refreshing
    if is_refreshing:
        return 'refreshing'
    try:
        Thread(target=update_key, args=(0,)).start()
    except Exception as err:
        app.logger.error(err)
        return 'error'
    return 'ok'


@app.route('/', methods=['GET'])
def index():
    # 读取index.html并返回
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()


# 每周二自动运行update_key
scheduler.add_job(func=update_key, id="update_key", trigger="cron", day_of_week="tue", hour=4, minute=0, args=(0,))

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    update_key(1)
    app.run(debug=True)
