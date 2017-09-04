# coding: utf-8

from __future__ import unicode_literals
import re
import logging
import commands
from xml.etree import ElementTree
import modules.defines as dfs


class ManifestModifier(object):
    def __init__(self, fpath, namespace=None):
        self.fpath = fpath
        self.xml_namespace = namespace or '{http://schemas.android.com/apk/res/android}'

    def replace(self, target, value):
        pass

    @staticmethod
    def _get_xml_namespace(ele):
        logging.info('element tag:{}'.format(ele.tag))
        m = re.match(r'\{.*?\}', ele.tag)
        return m.group(0) if m else ""

    def update_android_manifest_xml(self, app_name, kv_pay_label):
        obj = ElementTree.parse(self.fpath)
        logging.info('xml namespace:{}'.format(self.xml_namespace))
        app = obj.find('application')
        app.set(self.xml_namespace + 'label', app_name)
        settled = set()
        for meta_data in app.findall('meta-data'):
            meta_name = meta_data.get(self.xml_namespace + 'name')
            if meta_name in kv_pay_label:
                meta_data.set(self.xml_namespace + 'value', kv_pay_label[meta_name])
                settled.add(meta_name)
        for k in kv_pay_label.keys():
            if k not in settled:
                logging.fatal('expect replace channel [{}] to [{}], actual not.'.format(k, kv_pay_label[k]))
                return dfs.err_replace_strings
        obj.write(self.fpath, encoding='utf-8')
        cmd = 'sed -i s/xmlns:ns0/xmlns:android/g {0} && sed -i s/ns0:/android:/g {0}'.format(fp)
        s, o = commands.getstatusoutput(cmd)
        if s != 0:
            logging.fatal('replace namespace alias failed with cmd [{}]'.format(cmd))
            return dfs.err_replace_strings
        return 0
