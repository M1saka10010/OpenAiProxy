from gevent import monkey
monkey.patch_all(thread=False)
# 是否开启debug模式
debug = False
# 访问地址
bind = "0.0.0.0:80"
# 工作进程数
workers = 1
# 设置协程模式
worker_class = "gevent"
# 最大客户端并发数量，默认情况下这个值为1000。此设置将影响gevent和eventlet工作模式
worker_connections = 500
# 超时时间
timeout = 600
# 输出日志级别
loglevel = 'error'
# 存放日志路径
pidfile = "log/gunicorn.pid"
# 存放日志路径
accesslog = "log/access.log"
# 存放日志路径
errorlog = "log/debug.log"
# gunicorn + apscheduler场景下，解决多worker运行定时任务重复执行的问题
preload_app = True
