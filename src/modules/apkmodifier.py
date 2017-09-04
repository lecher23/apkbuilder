# coding: utf-8

from __future__ import unicode_literals
import re
import os
import logging
import modules.defines as dfs
from xml.etree import ElementTree
from utils import _call

sign_conf_str = '''signingConfigs {
        releaseCfg {
            storeFile file(RELEASE_STORE_FILE)
            storePassword RELEASE_STORE_PASSWORD
            keyAlias RELEASE_KEY_ALIAS
            keyPassword RELEASE_KEY_PASSWORD
        }
    }
    '''

release_sign_conf_str = '    signingConfig signingConfigs.releaseCfg\n        '


class ApkModifier(object):
    def __init__(self, dir_prj_root, f_xml, f_gradle, namespace=None, dir_res=None, icon_name=None):
        self.dir_prj_root = dir_prj_root
        self.f_manifest = f_xml
        self.f_built_gradle = f_gradle
        self.f_prop_gradle = os.path.join(self.dir_prj_root, 'gradle.properties')
        self.dir_res = dir_res
        self.icon_dir_prefix = 'drawable'
        self.icon_file_name = icon_name or 'ic_launcher.png'
        self.xml_namespace = namespace or '{http://schemas.android.com/apk/res/android}'

    def set_appid_in_build_gradle(self, app_id):
        ptn = re.compile(r'(.*?defaultConfig\s*\{\s*applicationId\s+")(.*?)("\s+.*)')
        bptn = re.compile(r'(defaultConfig)')
        xptn = re.compile(r'(defaultConfig\s*\{[\s\S]*?release\s*\{[\s\S]*?)(\})')
        with open(self.f_built_gradle) as f:
            ctnt = f.read()
            if ctnt.find('signingConfigs') >= 0:
                logging.fatal('signingConfigs already in %s, abort.', self.f_built_gradle)
                return dfs.err_replace_strings
            res = ptn.findall(ctnt)
            if not res or len(res) > 1:
                return dfs.err_bad_build_gradle_file
            old_app_id = res[0][1]
            # add sign apk conf.
            ctnt = ptn.sub(lambda m: '{}{}{}'.format(m.group(1), app_id, m.group(3)), ctnt)
            ctnt = bptn.sub(lambda m: '{}{}'.format(sign_conf_str, m.group(1)), ctnt)
            ctnt = xptn.sub(lambda m: '{}{}{}'.format(m.group(1), release_sign_conf_str, m.group(2)), ctnt)
        with open(self.f_built_gradle, 'w') as f:
            f.write(ctnt.encode("utf-8"))
        cmd = 'sed -i "s/{}/{}/g" {}'.format(old_app_id.replace('.', '\\.'), app_id, self.f_manifest)
        if not _call(cmd):
            logging.fatal('repace appid in %s failed.', self.f_manifest)
            return dfs.err_replace_strings
        return 0

    def replace(self, target, value):
        pass

    @staticmethod
    def update_strings_xml(f_string, kv, f_out):
        '''using xml to replace.'''
        xml_obj = ElementTree.parse(f_string)
        root = xml_obj.getroot()
        replaced = set()
        for node in root.getchildren():
            node_name = node.attrib["name"]
            if node_name in kv:
                node.text = kv[node_name]
                replaced.add(node_name)
        if len(replaced) != len(kv):
            logging.fatal("replace failed: %s != %s", kv.keys(), replaced)
            return False
        xml_obj.write(f_out, encoding='utf-8')
        return True

    def update_manifest(self, app_name, meta_data_values):
        obj = ElementTree.parse(self.f_manifest)
        app_node = obj.find('application')
        self._set_app_name(app_node, app_name)
        code = self._set_meta_data(app_node, meta_data_values)
        if not code:
            return code
        obj.write(self.f_manifest, encoding='utf-8')
        return self._restore_namespace()

    def add_gradle_properties(self, key_file, alias, password):
        with open(self.f_prop_gradle) as f:
            content = f.read()
        keys = ('RELEASE_KEY_PASSWORD', 'RELEASE_KEY_ALIAS', 'RELEASE_STORE_PASSWORD', 'RELEASE_STORE_FILE')
        for key in keys:
            if content.find(key) >= 0:
                logging.fatal('param [{}] already defined in [{}]'.format(key, self.f_prop_gradle))
                return dfs.err_replace_strings
        content += '\nRELEASE_KEY_PASSWORD={}\n' \
                   'RELEASE_KEY_ALIAS={}\n' \
                   'RELEASE_STORE_PASSWORD={}\n' \
                   'RELEASE_STORE_FILE={}\n'.format(password, alias, password, key_file)
        with open(self.f_prop_gradle, 'w') as f:
            f.write(content)
        return 0

    def replace_icon(self, icon_path):
        icon_dirs = \
            [os.path.join(self.dir_res, f) for f in os.listdir(self.dir_res) if f.startswith(self.icon_dir_prefix)]
        replaced_count = 0
        for icon_dir in icon_dirs:
            f_icon = os.path.join(icon_dir, self.icon_file_name)
            if os.path.exists(f_icon):
                logging.info('replace app icon in dir {}.'.format(icon_dir))
                if not _call('cp {} {}'.format(icon_path, f_icon)):
                    return False
                replaced_count += 1
        return bool(replaced_count)

    @staticmethod
    def _get_xml_namespace(ele):
        logging.info('element tag:{}'.format(ele.tag))
        m = re.match(r'\{.*?\}', ele.tag)
        return m.group(0) if m else ""

    def _set_meta_data(self, app_node, values):
        settled = set()
        for meta_data in app_node.findall('meta-data'):
            meta_name = meta_data.get(self.xml_namespace + 'name')
            if meta_name in values:
                meta_data.set(self.xml_namespace + 'value', values[meta_name])
                settled.add(meta_name)
        for k in values.keys():
            if k not in settled:
                logging.fatal('expect replace channel [%s] to [%s], actual not.', k, values[k])
                return dfs.err_replace_strings
        return 0

    def _set_app_name(self, xml_obj, app_name):
        xml_obj.set(self.xml_namespace + 'label', app_name)

    def _restore_namespace(self):
        cmd = 'sed -i s/xmlns:ns0/xmlns:android/g {0} && sed -i s/ns0:/android:/g {0}'.format(self.f_manifest)
        return 0 if _call(cmd) else dfs.err_replace_strings
