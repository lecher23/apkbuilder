# coding: utf-8

import datetime
import json
import logging
import os
import urllib
import tornado.ioloop
import tornado.web
import requests

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from modules.defines import ErrMapping
from utils.tsubprocess import Subprocess
from utils import exe_cmd

BuildStatus = [
    ('等待打包', '#8B864E'),
    ('打包中', '#082E54'),
    ('打包成功', '#00FF00'),
    ('打包失败', '#990033')
]


class BuildManager(object):
    def __init__(self, root_path):
        self.finished_tasks = []
        self.waiting_tasks = []
        self.io_loop = tornado.ioloop.IOLoop.current()
        self.check_interval = 3000
        self.timer = tornado.ioloop.PeriodicCallback(self.do_build, self.check_interval)
        self.root_path = root_path
        self.subprocess = None
        self.current_task = None
        self.stop = False
        self.stop_callback = None
        self.build_history_file = os.path.join(root_path, 'data/build_history.data')
        self.dingtalk_entrance = 'https://oapi.dingtalk.com/robot/send?' \
                                 'access_token=558efa7f72a829910c234bb18c4a4f86855c1490bbd6fe4669d98f4daf7686cd'
        self.admin_hosts = [
            "admin.91cashmobi.com/fyadminsys/bale/baleEnd",
            "admin1.91cashmobi.com/fyadminsys/bale/baleEnd"
        ]

    def stop_builder(self, callback):
        self.stop = True
        self.stop_callback = callback

    def do_build(self):
        if self.waiting_tasks:
            self.timer.stop()
            self.current_task = self.waiting_tasks.pop(0)
            self.process_task()
        elif self.stop:
            self.stop_callback()

    def process_task(self):
        '''十分钟内必须结束'''
        try:
            self.subprocess = Subprocess(
                self.on_build_finish, timeout=600, args=self.current_task.get_build_args(), cwd=self.root_path)
            self.current_task.begin_build()
            self.subprocess.start()
        except Exception:
            logging.exception('start task process failed.')
            self.subprocess = None
            self.current_task.finish_build(False, "启动编译进程失败")
            self.finished_tasks.append(self.current_task)
            self.timer.start()

    def run(self):
        self.timer.start()

    def get_build_summary(self, hours_wanted):
        now = datetime.datetime.now() - datetime.timedelta(hours=hours_wanted)
        out = [task.serialize() for task in reversed(self.waiting_tasks) if task.is_later_than_datetime(now)]
        if self.current_task:
            out.append(self.current_task.serialize())
        out += [task.serialize() for task in reversed(self.finished_tasks) if task.is_later_than_datetime(now)]
        return '\n'.join(out)

    def on_build_finish(self, status, stdout, stderr, has_timed_out):
        if has_timed_out:
            logging.fatal('build task time out:\nout:[{}]\nerr:[{}]'.format(stdout, stderr))
            self.current_task.finish_build(False, '执行编译任务超时')
        elif status != 0:
            logging.fatal('build task failed with exit code: [{}]\nout:[{}]\nerr:[{}]'.format(status, stdout, stderr))
            self.current_task.finish_build(False, self.convert_err_code(status))
        else:
            self.current_task.finish_build(True, stdout)
        self.subprocess = None
        self.timer.start()
        self.notify_admin_system()
        self.notify_dingtalk()
        self.finished_tasks.append(self.current_task)
        self.write_build_result()
        self.current_task = None

    def notify_admin_system(self):
        params = {
            'channelId': self.current_task.get_app_id(),
            'apkUrl': self.current_task.get_download_url()
        }
        for host in self.admin_hosts:
            r = requests.post(host, params=params)
            logging.warning(
                'notify server with params [%s] %s', params, 'success' if r.status_code == 200 else 'failed')

    def notify_dingtalk(self):
        body = json.dumps({
            "msgtype": "text",
            "text": {
                "content": "打包结果通知:[{}]打包{}\n".format(
                    self.current_task.alias,
                    "成功, 细节:\n公网链接:{}\n内网下载:{}".format(
                        self.current_task.get_download_url(), self.current_task.get_inner_dl()) if
                    self.current_task.is_build_success() else "失败, 原因:\n{}".format(self.current_task.output)
                )
            },
            "at": {
                "atMobiles": [
                    "13486310061"
                ],
                "isAtAll": True
            }
        }).encode('utf-8')
        req = HTTPRequest(url=self.dingtalk_entrance, method='POST', body=body, headers={
            "Content-Type": "application/json"
        })
        AsyncHTTPClient().fetch(
            req, callback=lambda rsp: logging.info(
                '[curl -X POST "{}" -H \'Content-Type: application/json\' -d \'{}\'] result:[{}]'.format(
                    self.dingtalk_entrance, body, rsp.body.replace('<br/>', '\n'))), raise_error=False)

    def write_build_result(self):
        if self.current_task:
            with open(self.build_history_file, 'a') as f:
                f.write(str(self.current_task) + '\n\n')

    def add_task(self, task_data):
        if not self.stop:
            self.waiting_tasks.append(task_data)
            return True
        return False

    @staticmethod
    def convert_err_code(code):
        return ErrMapping.get(code, "未知错误:{}".format(code))

    def __str__(self):
        out = [str(item) for item in self.finished_tasks]
        # self.app_name, self.channel, self.dataeye, self.pkg, self.sdk, self.pull_code, self.icon_path,
        return 'AppName|Channel|DataEye|AppID|PaySDK|PullCode|IconPath\n\n'.join(out)


class TaskData(object):
    def __init__(self):
        self.conf_file = None
        self.project_index = None
        self.project_name = None
        self.app_name = None
        self.pkg = None
        self.need_upload = None
        self.alias = None
        self.icon_path = None
        self.status = 0
        self.output = None
        self.pull_code = None
        self.init_time = datetime.datetime.now()
        self.start_time = None
        self.end_time = None
        self.git_address = None
        self.branch = None
        self.build_apk_dir = None
        self.process_chain = None
        self.args = None
        self.inner_host = 'http://git.leeqo.cn:8000'

    @staticmethod
    def str_datetime(dt):
        return dt.strftime('%m-%d %H:%M:%S') if dt else '00-00 00:00:00'

    def __str__(self):
        return '\n'.join([
            'build command: [{}]'.format(' '.join(self.args)),
            'build  result: {}'.format(BuildStatus[self.status][0]),
            'build    time: {}  ->  {}'.format(
                self.start_time.strftime('%m-%d %H:%M:%S') if self.start_time else '00-00 00:00:00',
                self.end_time.strftime('%m-%d %H:%M:%S') if self.end_time else '00-00 00:00:00'),
            'stdout       : [{}]'.format(self.output)
        ])

    def is_later_than_datetime(self, target_date):
        return self.init_time >= target_date

    def format_time(self):
        return '开始:{}<br/>结束:{}'.format(
            self.start_time.strftime('%m-%d %H:%M:%S') if self.start_time else '00-00 00:00:00',
            self.end_time.strftime('%m-%d %H:%M:%S') if self.end_time else '00-00 00:00:00'
        )

    def serialize(self):
        st_info = BuildStatus[self.status]
        s = '<tr>' \
            '<td>{0}</td>' \
            '<td>{1}</td>' \
            '<td>{2}</td>' \
            '<td>{3}</td>' \
            '<td><font color="{4}">{5}</font></td>' \
            '<td>{6}</td>' \
            '</tr>'

        if self.is_build_success():
            result = '下载链接: {}<br/><a target=\"_blank\" href=\"{}\">内网下载</a>'.format(
                self.output, self.get_inner_dl())
        else:
            result = self.output
        args = (self.format_time(), self.project_name, self.app_name, self.alias, st_info[1], st_info[0], result)
        logging.debug('%s', [type(item) for item in args])
        return s.format(*[arg.encode('utf-8') if isinstance(arg, unicode) else arg for arg in args])

    def get_inner_dl(self):
        return "{}/{}.apk".format(self.inner_host, self.alias)

    def begin_build(self):
        self.status = 1
        self.start_time = datetime.datetime.now()

    def finish_build(self, success, output):
        self.status = 2 if success else 3
        self.output = output
        self.end_time = datetime.datetime.now()

    def is_build_success(self):
        return self.status == 2

    def validate_param(self):
        if not self.app_name or not self.pkg or not self.validate_prv_param() \
                or self.icon_path is None or not self.alias or not self.git_address \
                or not self.branch or not self.build_apk_dir:
            return False
        return True

    def get_build_args(self):
        self.args = ['python', 'src/auto_apk.py', '-a', self.app_name,
                     '-p', self.pkg, '-o', self.alias, '-U', self.pull_code, '-b', self.branch,
                     '-e', self.conf_file, '-A', self.build_apk_dir, '-I', self.project_index]
        if self.need_upload == '1':
            self.args.append('-u')
        if self.icon_path:
            self.args.append('-i')
            self.args.append(self.icon_path)
        self.get_build_prv_args()
        self.args = [arg.encode('utf-8') if isinstance(arg, unicode) else arg for arg in self.args]
        logging.info('build cmd: [%s]', self.args)
        return self.args

    def debug(self):
        for attr in dir(self):
            if not attr.startswith('_'):
                val = getattr(self, attr)
                print("{}={}".format(attr, val))

    def get_download_url(self):
        if self.is_build_success():
            return self.output.strip()
        raise Exception('build failed. there is no download url.')

    def validate_prv_param(self):
        raise NotImplementedError()

    def get_build_prv_args(self):
        raise NotImplementedError()

    def get_app_id(self):
        raise NotImplementedError()


class TaskDataFor3rdPay(TaskData):
    def __init__(self):
        super(TaskDataFor3rdPay, self).__init__()
        self.channel = None
        self.dataeye = None

    def validate_prv_param(self):
        if not self.channel or not self.dataeye:
            return False
        return True

    def get_build_prv_args(self):
        self.args += ['-c', self.channel, '-d', self.dataeye, '-v', '3rd']

    def get_app_id(self):
        return self.channel


class TaskDataForSmsPay(TaskData):
    def __init__(self):
        super(TaskDataForSmsPay, self).__init__()
        self.cn_names = []
        self.cn_vals = []
        self.key_channel = None

    def validate_param(self):
        if not self.cn_names or not self.cn_vals:
            return False
        return True

    def get_build_prv_args(self):
        self.args += ['-L', ','.join(self.cn_names), '-l', ','.join(self.cn_vals), '-v', 'sms']

    def get_app_id(self):
        return self.key_channel
