# coding:utf-8

import json
from collections import namedtuple

Option = namedtuple('Option', ('value', 'text'))


class CfgWrapper(object):
    _empty_dict_ = {}

    def __init__(self, cfg_path):
        self.cfg_path = cfg_path
        self.prj_conf_list = []
        self.prj_list = []
        self.parse_conf_file()

    def parse_conf_file(self):
        obj = json.load(open(self.cfg_path))
        i = 0
        for prj_conf in obj['prj']:
            if prj_conf['enable']:
                self.prj_list.append(Option(value=i, text=prj_conf['name']))
                prj_conf['processors'] = self.get_processor(prj_conf['build_processors'])
                self.prj_conf_list.append(prj_conf)
                i += 1

    def get_prj_git_address(self, prj_tag):
        idx = int(prj_tag)
        if idx < len(self.prj_conf_list):
            return self.prj_conf_list[idx].get('git', None)

    def get_prj_build_apk_dir(self, prj_tag):
        idx = int(prj_tag)
        if idx < len(self.prj_conf_list):
            return self.prj_conf_list[idx].get('output', self._empty_dict_).get('apk_path', None)

    def get_prj_process_chain(self, prj_tag):
        idx = int(prj_tag)
        if idx < len(self.prj_conf_list):
            return self.prj_conf_list[idx].get('processors', None)

    @staticmethod
    def get_processor(raw):
        return ','.join(raw)

    def get_prj_list(self):
        return self.prj_list

    def get_project_info(self, prj_id):
        '''
        :param prj_id:
        :return: project name, project pay type, version list
        '''
        prj = self.prj_conf_list[int(prj_id)]
        return prj['name'], prj['pay_type'], [Option(value=v, text=k) for k, v in prj['versions'].items()]

    def get_prj_name(self, prj_id):
        return self.prj_conf_list[int(prj_id)]['name']

    def get_project_channels(self, prj_idx):
        return [Option(text=k, value=v) for k, v in self.prj_conf_list[int(prj_idx)]['channels'].items()]

    def get_project_channel_keys(self, prj_idx):
        return self.prj_conf_list[int(prj_idx)]['channels'].values()

    def get_project_key_channel(self, prj_idx):
        return self.prj_conf_list[int(prj_idx)].get('key-channels', '')
