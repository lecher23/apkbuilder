# coding: utf-8

import os
import time
import logging
import subprocess
import modules.defines as dfs


def get_signed_apk(apk_dir):
    for f in os.listdir(apk_dir):
        if f.endswith("-release.apk"):
            return os.path.join(apk_dir, f)
    return None


def do_work(params):
    gradle_bin = params['compiler']
    prj_path = params['prj_dir']
    out_file = params['log_file']
    args = [gradle_bin, "build"]
    start = time.time()
    logging.info('begin build process with cmd[{}]'.format(' '.join(args)))
    exit_code = subprocess.call(args=args, cwd=prj_path, stderr=out_file, stdout=out_file)
    if exit_code != 0:
        logging.fatal("build process exit abnormal:[{}]".format(exit_code))
    else:
        logging.info("build success.")
    logging.info("build cost:[{}]".format(time.time() - start))
    if exit_code != 0:
        return dfs.err_build_apk
    apk_dir_path = params['apk_dir']
    params['signed_apk_path'] = get_signed_apk(os.path.join(prj_path, apk_dir_path))
    return 0
