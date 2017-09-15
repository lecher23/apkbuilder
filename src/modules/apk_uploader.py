# coding:utf-8

import os
import sys
import datetime
import logging

import modules.defines as dfs
from utils.ucloud.ufile import putufile
from utils import exe_cmd


def do_work(params):
    output_apk_name = params['output']
    do_upload = params['upload']
    domain = params['cdn_domain']
    public_key = params['cdn_pub_key']
    private_key = params['cdn_prv_key']
    apk_bucket = params['cdn_bucket']
    signed_apk_path = params['signed_apk_path']

    if not signed_apk_path:
        logging.fatal("can not find signed apk.")
        return dfs.err_find_built_apk
    logging.info("singed apk:{}".format(signed_apk_path))
    out_file_name = '{}-{}.apk'.format(output_apk_name, datetime.datetime.now().strftime('%H%M%S'))
    local_file_name = output_apk_name + '.apk'
    cmd = 'cp {} {}'.format(signed_apk_path, os.path.join(os.getcwd(), 'apk_files/', local_file_name))
    if not exe_cmd(cmd):
        logging.fatal('copy apk failed.')
        return dfs.err_cp_apk
    if do_upload:
        try:
            # 构造上传对象，并设置公私钥
            handler = putufile.PutUFile(public_key, private_key)
            # upload small file to public bucket
            logging.info('start upload file to public bucket')
            # 上传到目标空间后保存的文件名
            key = "auto/{}".format(out_file_name)
            # 请求上传
            ret, resp = handler.putfile(apk_bucket, key, signed_apk_path)
        except:
            logging.exception('upload apk failed.')
            return dfs.err_upload_apk
        logging.info('ucloud response:[{}]'.format(resp.content))
        if resp.status_code == 200:
            url = 'http://{}/{}'.format(domain, key)
            logging.info("upload success: url[{}]".format(url))
            sys.stdout.write(url)
            return 0
        logging.fatal("upload failed.")
        return dfs.err_upload_apk
    return 0
