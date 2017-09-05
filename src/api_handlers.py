# coding: utf-8

import os
import logging
import datetime
import tornado.web
import tornado.ioloop
from task_manager import TaskDataFor3rdPay, TaskDataForSmsPay


class SubmitBuildHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self):
        task_data = self.init_task_data()
        self._init_common_params(task_data)
        if not task_data.validate_param():
            logging.warning('invalid params.')
            self.write("有参数为空")
            self.finish()
        else:
            if self.settings['builder'].add_task(task_data):
                self.redirect('/pkg/status')
            else:
                self.write("服务器准备关闭，不接受新的打包申请.")
                self.finish()

    def init_task_data(self):
        task_data = TaskDataFor3rdPay()
        task_data.channel = self.get_argument('channel').strip()
        task_data.dataeye = self.get_argument('dataeye').strip()
        return task_data

    def _init_common_params(self, task_data):
        prj_tag = self.get_argument('project')
        task_data.project_index = prj_tag
        task_data.conf_file = self.settings['conf_path']
        task_data.app_name = self.get_argument('name').strip()
        task_data.pkg = self.get_argument('pkg').strip()
        task_data.need_upload = self.get_argument('upload', '1')
        task_data.alias = self.get_argument('alias').strip()
        task_data.icon_path = self.get_icon_file()
        task_data.pull_code = self.get_argument('pullcode', 'true')
        task_data.git_address = self.settings['conf'].get_prj_git_address(prj_tag)
        task_data.branch = self.get_argument('ver')
        task_data.build_apk_dir = self.settings['conf'].get_prj_build_apk_dir(prj_tag)
        task_data.process_chain = self.settings['conf'].get_prj_process_chain(prj_tag)
        task_data.project_name = self.settings['conf'].get_prj_name(prj_tag)

    def get_icon_file(self):
        if not self.request.files:
            return ""
        remote_file = self.request.files['myfile'][0]
        ftype = self.get_file_suffix(remote_file['filename'])
        if ftype != 'png':
            self.write('<h2>错误的文件类型, 期望的文件类型是 png.</h2>')
            return None
        else:
            fname, fpath = self.get_tmp_file_path(ftype)
            with open(fpath, 'w') as fw:
                fw.write(remote_file['body'])
            return fpath

    def get_tmp_file_path(self, ftype):
        time_str = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        fname = '%s.%s' % (time_str, ftype)
        return fname, os.path.join(self.settings['root_path'], '.tmp/icons', fname)

    @staticmethod
    def get_file_suffix(fname):
        idx = fname.rfind('.')
        if idx < 0:
            return ''
        return fname[idx + 1:]


class SubmitSmsBuildHandler(SubmitBuildHandler):
    def init_task_data(self):
        prj_tag = self.get_argument('project')
        task_data = TaskDataForSmsPay()
        cn_names = self.settings['conf'].get_project_channel_keys(prj_tag)
        task_data.cn_names = cn_names
        for cn_name in cn_names:
            task_data.cn_vals.append(self.get_argument(cn_name))
        return task_data


class BuildStatusHandler(tornado.web.RequestHandler):
    def get(self):
        hours = self.get_argument('hours', 5)
        self.render('status.html', body=self.settings['builder'].get_build_summary(hours))


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class ChooseProjectHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('entrance.html', prj_list=self.settings['conf'].get_prj_list())


class SettingProjectPageHandler(tornado.web.RequestHandler):
    def post(self):
        prj = self.get_argument('project')
        name, pay_type, ver_list = self.settings['conf'].get_project_info(prj)
        if pay_type == '3rd':
            self.render('index_3rd.html', ver_list=ver_list, prj_name=name, prj_idx=prj)
        else:
            channel_list = self.settings['conf'].get_project_channels(prj)
            self.render('index_sms.html', ver_list=ver_list, channel_list=channel_list, prj_name=name, prj_idx=prj)
