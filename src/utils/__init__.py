# coding=utf-8

from __future__ import unicode_literals
import os
import time
import random
import logging
import commands

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

num_dict = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
            'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
            'U', 'V', 'W', 'X', 'Y', 'Z')
num_dict_size = len(num_dict)


def gen_uni_code():
    now = int(time.time() * 1000)
    res = []
    while now >= num_dict_size:
        res.append(num_dict[now % num_dict_size])
        now /= num_dict_size
    res.append(num_dict[now])
    return ''.join(reversed(res))


def get_key_settings(work_dir):
    pwd = "".join(random.sample(ch_list, 16))
    with open(os.path.join(work_dir, 'genkey.in'), "w") as f:
        f.write(keytool_in.encode('utf-8').format(pwd))
    alias = "".join(random.sample(ch_list, 8))
    key_name = "{}-{}.keystore".format(alias, pwd)
    cmd = 'cd {} && keytool -genkey -v -keystore {} -alias {} ' \
          '-keyalg RSA -keysize 1024 -validity 90 < genkey.in'.format(work_dir, key_name, alias)
    s, o = commands.getstatusoutput(cmd)
    if s != 0:
        logging.fatal('make key file failed.[{}]'.format(cmd))
        return None
    return os.path.join(work_dir, key_name), alias, pwd


def exe_cmd(cmd):
    if isinstance(cmd, unicode):
        cmd = cmd.encode('utf-8')
    s, o = commands.getstatusoutput(cmd)
    if isinstance(o, str):
        o = o.decode('utf-8')
    if s != 0:
        logging.fatal('exe [{}] failed.reason:[{}]'.format(cmd.decode('utf-8'), o))
        return False
    logging.info('\n>>>:{}\n>>>:{}'.format(cmd.decode('utf-8'), o))
    return True


def replace_icon(prj_path, app_res_dir, icon_dir_prefix, icon_path):
    icon_dir_dir = os.path.join(prj_path, app_res_dir)
    icon_dirs = \
        [os.path.join(icon_dir_dir, f) for f in os.listdir(icon_dir_dir) if f.startswith(icon_dir_prefix)]
    for icon_dir in icon_dirs:
        logging.info('replace app icon in dir {}.'.format(icon_dir))
        if not exe_cmd('cp {} {}/ic_launcher.png'.format(icon_path, icon_dir)):
            return False
    return True


def safestr(ori):
    return ori.encode('utf-8') if isinstance(ori, unicode) else ori
