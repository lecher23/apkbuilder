# coding:utf-8

import os
import sys
import logging
import commands
import modules.defines as dfs
from ucloud.ufile import putufile


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
    out_file_name = '{}.apk'.format(output_apk_name)
    s, o = commands.getstatusoutput(
        'cp {} {}'.format(signed_apk_path, os.path.join(os.getcwd(), 'apk_files/', out_file_name)))
    if s != 0:
        logging.fatal(
            'copy [{}]->[{}] failed:[{}]'.format(
                signed_apk_path, os.path.join(os.getcwd(), 'apk/files/', out_file_name), o))
        return dfs.err_cp_apk
    if do_upload:
        # 构造上传对象，并设置公私钥
        handler = putufile.PutUFile(public_key, private_key)
        # upload small file to public bucket
        logging.info('start upload file to public bucket')
        # 上传到目标空间后保存的文件名
        key = "auto/{}".format(out_file_name)
        # 请求上传
        ret, resp = handler.putfile(apk_bucket, key, signed_apk_path)
        logging.info('ucloud response:[{}]'.format(resp.content))
        if resp.status_code == 200:
            url = 'http://{}/{}'.format(domain, key)
            logging.info("upload success: url[{}]".format(url))
            # print "下载链接: {}<br/>APK索引名:[{}],<a target=\"_blank\" href=\"http://git.leeqo.cn:8000\">索引页面</a>".\
            #     format(url, output_apk_name)
            sys.stdout.write(url)
            return 0
        logging.fatal("upload failed.")
        return dfs.err_upload_apk
    # print "下载链接: {}<br/>APK索引名:[{}],<a target=\"_blank\" href=\"http://git.leeqo.cn:8000\">索引页面</a>".format(
    # '', output_apk_name)
    return 0
