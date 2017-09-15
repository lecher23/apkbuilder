# coding: utf-8

import os
import re
import logging
from xml.etree import ElementTree
import modules.defines as dfs
from utils import get_key_settings, exe_cmd, replace_icon

# relative path
strings_xml_path = "quicklive/src/main/res/values/strings.xml"
pay_conf_path = "quicklive/src/main/java/com/fy/bluelive/config/PayConfig.java"
build_conf_path = "quicklive/build.gradle"
apk_dir_path = "quicklive/build/outputs/apk"
res_dir_path = "quicklive/src/main/res"
icon_dir_prefix = "mipmap"
icon_dir_name_list = ('mipmap-hdpi',)
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

ch_list = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
           'w', 'x', 'y', 'z']

keytool_in = '''{0}
{0}
Spider
TMSLYLY
Cor.td
HonKong
ThreeSeason
86
y

'''


def update_strings_xml(fp, new_app_name, channel_id, dataeye_id, ofp):
    '''using xml to replace.'''
    xml_obj = ElementTree.parse(fp)
    root = xml_obj.getroot()
    flag = 0b111
    for node in root.getchildren():
        node_name = node.attrib["name"]
        if node_name == "app_name":
            node.text = new_app_name
            flag ^= 0b100
        elif node_name == 'channel_id':
            node.text = channel_id
            flag ^= 0b010
        elif node_name == 'dataeye_id':
            node.text = dataeye_id
            flag ^= 0b001
    if flag:
        logging.fatal("replace failed: tag[{}]".format(flag))
        return False
    xml_obj.write(ofp, encoding='utf-8')
    return True


def replace_app_id(fp, app_id, ofp):
    ptn = re.compile(r'(.*?defaultConfig\s*\{\s*applicationId\s+")(.*?)("\s+.*)')
    bptn = re.compile(r'(defaultConfig)')
    xptn = re.compile(r'(defaultConfig\s*\{[\s\S]*?release\s*\{[\s\S]*?)(\})')
    with open(fp) as f:
        ctnt = f.read()
        # add sign apk conf.
        ctnt = ptn.sub(lambda m: '{}{}{}'.format(m.group(1), app_id, m.group(3)), ctnt)
        ctnt = bptn.sub(lambda m: '{}{}'.format(sign_conf_str, m.group(1)), ctnt)
        ctnt = xptn.sub(lambda m: '{}{}{}'.format(m.group(1), release_sign_conf_str, m.group(2)), ctnt)
    if ofp:
        with open(ofp, 'w') as f:
            f.write(ctnt.encode("utf-8"))


def set_sign_params(fp_gradle_pts, key_file, alias, password):
    with open(fp_gradle_pts) as f:
        content = f.read()
    content += '\nRELEASE_KEY_PASSWORD={}\n' \
               'RELEASE_KEY_ALIAS={}\n' \
               'RELEASE_STORE_PASSWORD={}\n' \
               'RELEASE_STORE_FILE={}\n'.format(password, alias, password, key_file)
    with open(fp_gradle_pts, 'w') as f:
        f.write(content)


def do_work(params):
    prj_path = params['prj_dir']
    app_name = params['app_name']
    cid = params['channel']
    did = params['dataeye']
    pkg = params['pkg']
    icon = params['icon']
    work_dir = params['work_dir']
    '''adapter func entrance'''
    try:
        f1 = os.path.join(prj_path, strings_xml_path)
        if not update_strings_xml(f1, app_name, cid, did, f1):
            return dfs.err_replace_strings
        f3 = os.path.join(prj_path, build_conf_path)
        replace_app_id(f3, pkg, f3)
        f4 = os.path.join(prj_path, gradle_properties_path)
        key_setting = get_key_settings(work_dir) if not params['enable_debug'] else ('a', 'a', 'a')
        if not key_setting:
            return dfs.err_make_key_file
        params['keystore'] = key_setting[0]
        set_sign_params(f4, *key_setting)
        if icon and not replace_icon(prj_path, res_dir_path, icon_dir_prefix, icon):
            return dfs.err_cp_icon
    except Exception:
        logging.exception("prepare build conf file failed.")
        return dfs.err_prepare_app_conf
    return 0
