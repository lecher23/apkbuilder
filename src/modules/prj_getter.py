# coding: utf-8

import os
import logging
import modules.defines as dfs
from utils import exe_cmd


def do_work(params):
    logging.info('prepare project.')
    tmp_dir = params['tmp_dir']
    repo_addr = params['git_address']
    branch = params['git_branch']
    update_code = params['update_code']
    work_dir = params['work_dir']
    if not repo_addr.endswith('.git') or not repo_addr.startswith('git@'):
        logging.fatal('invalid repo address[{}]. expect ssh address.'.format(repo_addr))
        return dfs.err_invalid_repo
    repo_name = os.path.basename(repo_addr)[:-4]
    repo_dir_name = '{}-{}'.format(repo_name, branch)
    repo_dir_abs_path = os.path.join(tmp_dir, repo_dir_name)
    if os.path.exists(repo_dir_abs_path):
        cmd = 'cd {} && git checkout {} && git pull'.format(repo_dir_abs_path, branch) if update_code else None
    elif update_code:
        cmd = 'cd {0} && git clone {1} {2} && cd {2} && git checkout {3}'.format(
            tmp_dir, repo_addr, repo_dir_name, branch)
    else:
        return dfs.err_pull_code

    if cmd and not exe_cmd(cmd):
        logging.fatal('pull code from git failed.\ncmd:[{}]'.format(cmd))
        return dfs.err_pull_code

    prj_dir = os.path.join(work_dir, 'prj')
    cmd = 'cp -r {} {}'.format(repo_dir_abs_path, prj_dir)
    if not exe_cmd(cmd):
        logging.fatal('copy project [{}]->[{}]'.format(repo_dir_abs_path, work_dir))
        return dfs.err_cp_prj
    params['prj_dir'] = prj_dir
    params['work_dir'] = work_dir
    return 0
