# coding: utf-8
from __future__ import unicode_literals
import sys

if __name__ == "__main__":
    sys.path.append('/home/licheng/workspace/fanyu_git/mytools/auto_build_apk/src')

import os
import re
import logging
import commands
from xml.etree import ElementTree
import modules.defines as dfs
from utils import get_key_settings, replace_icon

# relative path
core_dir_name = 'meinvshipin_sms'
android_manifest_path = "{}/AndroidManifest.xml".format(core_dir_name)
build_conf_path = "{}/build.gradle".format(core_dir_name)
apk_dir_path = "{}/build/outputs/apk".format(core_dir_name)
res_dir_path = "{}/res".format(core_dir_name)
icon_dir_prefix = "drawable"
icon_dir_name_list = ('drawable-hdpi',)
gradle_properties_path = "gradle.properties"

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

xml_namespace = '{http://schemas.android.com/apk/res/android}'


def _get_xml_namespace(ele):
    logging.info('element tag:{}'.format(ele.tag))
    m = re.match(r'\{.*?\}', ele.tag)
    return m.group(0) if m else ""


def update_android_manifest_xml(fp, app_name, kv_pay_label):
    obj = ElementTree.parse(fp)
    logging.info('xml namespace:{}'.format(xml_namespace))
    app = obj.find('application')
    app.set(xml_namespace + 'label', app_name)
    settled = set()
    for meta_data in app.findall('meta-data'):
        meta_name = meta_data.get(xml_namespace + 'name')
        if meta_name in kv_pay_label:
            meta_data.set(xml_namespace + 'value', kv_pay_label[meta_name])
            settled.add(meta_name)
    for k in kv_pay_label.keys():
        if k not in settled:
            logging.fatal('expect replace channel [{}] to [{}], actual not.'.format(k, kv_pay_label[k]))
            return dfs.err_replace_strings
    obj.write(fp, encoding='utf-8')
    cmd = 'sed -i s/xmlns:ns0/xmlns:android/g {0} && sed -i s/ns0:/android:/g {0}'.format(fp)
    s, o = commands.getstatusoutput(cmd)
    if s != 0:
        logging.fatal('replace namespace alias failed with cmd [{}]'.format(cmd))
        return dfs.err_replace_strings
    return 0


def replace_app_id(fp, app_id, fp_mainifest):
    ptn = re.compile(r'(.*?defaultConfig\s*\{\s*applicationId\s+")(.*?)("\s+.*)')
    bptn = re.compile(r'(defaultConfig)')
    xptn = re.compile(r'(defaultConfig\s*\{[\s\S]*?release\s*\{[\s\S]*?)(\})')
    with open(fp) as f:
        ctnt = f.read()
        if ctnt.find('signingConfigs') >= 0:
            logging.fatal('signingConfigs already in {}, abort.'.format(fp))
            return dfs.err_replace_strings
        res = ptn.findall(ctnt)
        if not res or len(res) > 1:
            return dfs.err_bad_build_gradle_file
        old_app_id = res[0][1]
        # add sign apk conf.
        ctnt = ptn.sub(lambda m: '{}{}{}'.format(m.group(1), app_id, m.group(3)), ctnt)
        ctnt = bptn.sub(lambda m: '{}{}'.format(sign_conf_str, m.group(1)), ctnt)
        ctnt = xptn.sub(lambda m: '{}{}{}'.format(m.group(1), release_sign_conf_str, m.group(2)), ctnt)
    if fp:
        with open(fp, 'w') as f:
            f.write(ctnt.encode("utf-8"))
    cmd = 'sed -i "s/{}/{}/g" {}'.format(old_app_id.replace('.', '\\.'), app_id, fp_mainifest)
    logging.info('exe cmd[{}]'.format(cmd))
    s, o = commands.getstatusoutput(cmd)
    if s != 0:
        logging.fatal('repace appid in {} failed.reason:[{}]'.format(fp_mainifest, o))
        return dfs.err_replace_strings
    return 0


def set_sign_params(fp_gradle_pts, key_file, alias, password):
    with open(fp_gradle_pts) as f:
        content = f.read()
    keys = ('RELEASE_KEY_PASSWORD', 'RELEASE_KEY_ALIAS', 'RELEASE_STORE_PASSWORD', 'RELEASE_STORE_FILE')
    for key in keys:
        if content.find(key) >= 0:
            logging.fatal('param [{}] already defined in [{}]'.format(key, fp_gradle_pts))
            return dfs.err_replace_strings
    content += '\nRELEASE_KEY_PASSWORD={}\n' \
               'RELEASE_KEY_ALIAS={}\n' \
               'RELEASE_STORE_PASSWORD={}\n' \
               'RELEASE_STORE_FILE={}\n'.format(password, alias, password, key_file)
    with open(fp_gradle_pts, 'w') as f:
        f.write(content)
    return 0


def do_work(params):
    logging.info('update project settings.')
    prj_path = params['prj_dir']
    app_name = params['app_name']
    pkg = params['pkg']
    icon = params['icon']
    channel_list = params['chn_name'].split(',')
    channel_values = params['chn_val'].split(',')
    work_dir = params['work_dir']

    if len(channel_list) != len(channel_values):
        return dfs.err_invalid_param
    cn_setting = {channel_list[i]: val for i, val in enumerate(channel_values)}
    '''adapter func entrance'''
    try:
        f1 = os.path.join(prj_path, android_manifest_path)
        exit_code = update_android_manifest_xml(f1, app_name, cn_setting)
        if exit_code != 0:
            return dfs.err_replace_strings
        f3 = os.path.join(prj_path, build_conf_path)
        exit_code = replace_app_id(f3, pkg, f1)
        if exit_code != 0:
            return exit_code
        f4 = os.path.join(prj_path, gradle_properties_path)
        key_setting = get_key_settings(work_dir) if not params['enable_debug'] else ('a', 'a', 'a')
        if not key_setting:
            return dfs.err_make_key_file
        ec = set_sign_params(f4, *key_setting)
        if ec != 0:
            return ec
        if icon and not replace_icon(prj_path, res_dir_path, icon_dir_prefix, icon):
            return dfs.err_cp_icon
    except Exception:
        logging.exception("prepare build conf file failed.")
        return dfs.err_prepare_app_conf
    return 0


if __name__ == "__main__":
    tp = {
        'prj_dir': '/home/licheng/workspace/fanyu_git/mytools/auto_build_apk/data',
        'app_name': '123',
        'pkg': 'sbcg.b.s',
        'icon': '/home/licheng/workspace/fanyu_git/mytools/auto_build_apk/data/build_history.data',
        'enable_debug': True,
        'cn_keys': 'qipaChannelid,maiguangChannelid,moxinChannelid,moxinChname,yufengChannelid,lemiChannelid,weiyunChannelid,YY_CID,yuanlangChannelid,data_eye_channelid',
        'cn_vals': '1,2,3,4,5,6,7,8,9,10'
    }
