# coding: utf-8

from __future__ import unicode_literals
import os
import sys
import json
import datetime
import logging
import modules.defines as dfs
from optparse import OptionParser
from utils import exe_cmd

sys.path.append(os.path.join(os.getcwd(), 'src'))

if __name__ == "__main__":
    parser = OptionParser()

    # common options
    parser.add_option('-v', '--version', dest='build_ver', default="3rd", help='build version: 3rd|sms.')
    parser.add_option('-a', '--app', dest='app_name', help='app name.')
    parser.add_option('-p', '--pkg', dest='pkg_name', help='package name.')
    parser.add_option('-i', '--icon', dest='icon', default="", help='package name.')
    parser.add_option('-o', '--output', dest='alias', default="", help='output file name.')
    parser.add_option('-A', '--apkdir', dest='apkdir', help='apk dir built by processor.')
    parser.add_option('-U', '--update', dest='pull_code', default="false", help='pull code from git.')
    # parser.add_option('-g', '--git', dest='git_addr', help='git ssh address.')
    # parser.add_option('-P', '--processors', dest='processors', help='processors list, use , split.')
    parser.add_option('-I', '--index', dest='prj_idx', help='project index in conf list.')
    parser.add_option('-e', '--config', dest='conf_file', help='project conf file.')
    parser.add_option('-b', '--branch', dest='git_branch', default="invalid", help='pull code from git.')
    parser.add_option('-u', '--upload', dest='need_upload', action="store_true", default=False,
                      help='upload apk to ucloud.')
    parser.add_option('-D', '--debug', dest='debug', action="store_true", default=False, help='open debug mode.')
    parser.add_option('-C', '--compiler', dest='compiler', default="gradle", help='pull code from git.')

    # options for 3rd project.
    parser.add_option('-c', '--channel', dest='channel_id', help='channel id in app.')
    parser.add_option('-d', '--dataeye', dest='dataeye_id', help='dataeye id.')

    # options for sms project.
    parser.add_option('-L', '--channelNames', dest='chn_name_list', help='channel name list, split by ",".')
    parser.add_option('-l', '--channelValues', dest='chn_val_list', help='channel value list, split by ",".')

    options, args = parser.parse_args()
    try:
        if not options.app_name or not options.pkg_name:
            raise AttributeError("Some args required.")
        options.pull_code = ('false', 'true').index(options.pull_code)
    except AttributeError as e:
        import traceback

        traceback.print_exc()
        parser.print_help()
        exit(dfs.err_invalid_param)

    exit_code = 0
    fp_log_file = None
    params = {}

    try:
        obj = json.load(open(options.conf_file))
        apk_conf = obj['prj'][int(options.prj_idx)]
        ucloud_conf = obj['ucloud']

        tmp_dir = os.path.join(os.getcwd(), '.tmp')
        work_dir = os.path.join(
            tmp_dir, 'prj-{}'.format(datetime.datetime.today().strftime('%Y%m%d-%H%M%S')))
        os.mkdir(work_dir)

        log_file = os.path.join(work_dir, 'auto-build.log')
        logging.basicConfig(level=logging.INFO,
                            format='[%(levelname)s][%(filename)s:%(lineno)d][%(asctime)s]:%(message)s',
                            datefmt='%a, %d %b %Y %H:%M:%S',
                            filename=log_file)
        fp_log_file = open(os.path.join(work_dir, 'gradle.log'), "w")
        params = {
            'log_file': fp_log_file,
            'top_dir': os.getcwd(),
            'app_name': options.app_name,
            'pkg': options.pkg_name,
            'upload': options.need_upload,
            'icon': options.icon,
            'output': options.alias,
            'update_code': options.pull_code,
            'git_address': apk_conf['git'],
            'git_branch': options.git_branch,
            'apk_dir': options.apkdir,
            'tmp_dir': tmp_dir,
            'cdn_domain': ucloud_conf['cdn_domain'],
            'cdn_pub_key': ucloud_conf['cdn_pub_key'],
            'cdn_prv_key': ucloud_conf['cdn_prv_key'],
            'cdn_bucket': ucloud_conf['cdn_bucket'],
            'enable_debug': options.debug,
            'compiler': options.compiler,
            'work_dir': work_dir,
            'apk_conf': apk_conf
        }

        if options.build_ver == '3rd':
            params['channel'] = options.channel_id
            params['dataeye'] = options.dataeye_id
        elif options.build_ver == 'sms':
            params['chn_name'] = options.chn_name_list
            params['chn_val'] = options.chn_val_list
        else:
            exit(dfs.err_invalid_param)
        params = {k: v.decode('utf-8') if isinstance(v, str) else v for k, v in params.items()}

        from build_executor import BuildExecutor

        be = BuildExecutor(apk_conf['build_processors'], params)
        exit_code = be.execute()
    except Exception as e:
        import traceback

        exit_code = 99
        traceback.print_exc()
    finally:
        if fp_log_file:
            fp_log_file.close()
        if 'prj_dir' in params and False:
            if not exe_cmd('rm -rf {}'.format(params['prj_dir'])):
                logging.warning('delete prj [{}] failed'.format(params['prj_dir']))
    exit(exit_code)
