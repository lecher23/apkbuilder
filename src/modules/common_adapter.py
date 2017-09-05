# coding: utf-8
import logging
import modules.defines as dfs
from apkmodifier import ApkModifier


def do_work(params):
    logging.info('update project settings.')
    prj_path = params['prj_dir']
    app_name = params['app_name']
    pkg = params['pkg']
    icon = params['icon']
    channel_list = params['chn_name'].split(',')
    channel_values = params['chn_val'].split(',')
    work_dir = params['work_dir']
    apk_conf = params['apk_conf']

    if len(channel_list) != len(channel_values):
        return dfs.err_invalid_param
    cn_setting = {channel_list[i]: val for i, val in enumerate(channel_values)}
    '''adapter func entrance'''
    try:
        m_apk = ApkModifier(prj_path, apk_conf)
        ec = m_apk.update_manifest(app_name, cn_setting)
        if ec:
            return ec
        ec = m_apk.set_appid_in_build_gradle(pkg)
        if ec:
            return ec
        key_setting = m_apk.gen_key_settings(work_dir) if not params['enable_debug'] else ('a', 'a', 'a')
        if not key_setting:
            return dfs.err_make_key_file
        ec = m_apk.add_gradle_properties(*key_setting)
        if ec:
            return ec
        if not m_apk.replace_icon(icon):
            return dfs.err_cp_icon
    except Exception:
        logging.exception("prepare build conf file failed.")
        return dfs.err_prepare_app_conf
    return 0
