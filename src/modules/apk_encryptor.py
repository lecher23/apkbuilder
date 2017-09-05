# coding=utf-8

import os
import re
import random
import logging
import commands
import subprocess
from utils import _call
import modules.defines as dfs

# so_seed_prj = "/home/android/playground/Cryptor"
upx = "/home/android/upx/src/upx.out"
so_seed_prj_path = '/home/android/playground/Cryptor'

cpp_path = "app/src/main/cpp"
built_so_apk_dir = "app/build/outputs/apk"
built_so_apk_name = 'app-release-unsigned.apk'
so_path_in_apk = "lib/armeabi/libnative-lib.so"
so_in_build_dir = "app/build/intermediates/transforms/stripDebugSymbol" \
                  "/release/folders/2000/1f/main/lib/armeabi/libnative-lib.so"

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


def build_so_prj(so_prj_path, gradle_bin, pub_key, out_file):
    counter = 0
    res = ['', '', '']
    for idx, ch in enumerate(pub_key):
        if counter < 8:
            pos = idx % len(res)
            res[pos] += ch
            counter += (1 if pos == len(res) - 1 else 0)
        else:
            res[2] += ch
    cpp_dir = os.path.join(so_prj_path, cpp_path)
    cmd = 'cd {} && sed -i \'s/%part1%/{}/g\' *.cpp && sed -i \'s/%part2%/{}/g\' *.cpp ' \
          '&& sed -i \'s/%part3%/{}/g\' *.cpp '.format(cpp_dir, *res)
    if not _call(cmd):
        return dfs.err_replace_so_signature
    args = [gradle_bin, 'build']
    out_file.write("-----build so-----\n")
    exit_code = subprocess.call(args=args, cwd=so_prj_path, stderr=out_file, stdout=out_file)
    if exit_code != 0:
        return dfs.err_build_so
    return 0


def replace_so_file(work_dir, so_prj_dir, unprotected_apk, keystore_file, from_apk=True):
    so_apk_unzip_dir = os.path.join(work_dir, 'app4so')
    fp_ori_so_apk = os.path.join(so_prj_dir, built_so_apk_dir, built_so_apk_name)
    if from_apk:
        # mkdir work_dir/app4so && cd work_dir/app4so && cp so.apk . && unzip so.apk
        cmd = 'mkdir {0} && cd {0} && cp {1} . && unzip {2}'.format(
            so_apk_unzip_dir, fp_ori_so_apk, built_so_apk_name
        )
        if not _call(cmd):
            return dfs.err_unzip_apk, None
    else:
        return dfs.err_for_future, None

    so_name = os.path.basename(so_path_in_apk)
    cmd = 'cd {0} && chmod +x {1} && {2} -9 -v -o {3} {1}'.format(so_apk_unzip_dir, so_path_in_apk, upx, so_name)
    if not _call(cmd):
        return dfs.err_add_shell_to_so, None
    # 解包目标APK
    name = os.path.basename(unprotected_apk)
    if not _call('cd {0} && cp {1} . ; apktool d {2}'.format(
            work_dir, unprotected_apk, name)):
        return dfs.err_unzip_target_apk, None
    path = os.path.join(work_dir, os.path.splitext(name)[0])
    arm_so_dir = os.path.join(path, 'lib/armeabi')
    # 直接替换lib下的文件
    cmd = "cd {} && cp {} .".format(arm_so_dir, os.path.join(so_apk_unzip_dir, '*.so'))
    if not _call(cmd):
        return dfs.err_mv_so_to_apk, None
    # 打包
    apk_file = 'safe-{}'.format(name)
    cmd = "cd {} && apktool b {} -o {}".format(work_dir, os.path.splitext(name)[0], apk_file)
    if not _call(cmd):
        return dfs.err_zip_apk, None
    # 签名, alias-password.keystore
    alias, pwd = os.path.splitext(os.path.basename(keystore_file))[0].split('-')
    pwd_file = os.path.join(work_dir, 'password')
    with open(pwd_file, 'w') as f:
        f.write(pwd + '\n')
    cmd = "cd {} && jarsigner -verbose -keystore  {} {} {} < {}".format(
        work_dir, keystore_file, apk_file, alias, pwd_file)
    if not _call(cmd):
        return dfs.err_resign_apk, None
    return 0, os.path.join(work_dir, apk_file)


def gen_key_store(work_dir):
    pwd = "".join(random.sample(ch_list, 16))
    with open("/tmp/keytool.in", "w") as f:
        f.write(keytool_in.format(pwd))
    alias = "".join(random.sample(ch_list, 6))
    key_file = "{}-{}.keystore".format(alias, pwd)
    cmd = 'cd {} && keytool -genkey -v -keystore {} -alias {} -keyalg RSA -keysize {} -validity 365' \
          '< /tmp/keytool.in'.format(work_dir, key_file, alias, 1024)
    if not _call(cmd):
        return dfs.err_gen_keystore
    with open(os.path.join(work_dir, 'password'), 'w') as f:
        f.write('{}\n'.format(pwd))
    return 0


def get_pub_key(work_dir, signed_apk_path):
    raw_apk_dir = os.path.join(work_dir, 'raw_apk')
    # move signed apk to work_dir/raw_apk
    if not _call('mkdir {1} && cp {0} {1}'.format(signed_apk_path, raw_apk_dir)):
        return dfs.err_make_dir, None
    # unzip apk
    signed_apk_name = os.path.basename(signed_apk_path)
    if not _call('cd {} && unzip {}'.format(raw_apk_dir, signed_apk_name)):
        return dfs.err_unzip_apk, None
    # get pub key
    csr_path = None
    for item in os.listdir(os.path.join(raw_apk_dir, 'META-INF')):
        if item.endswith('RSA'):
            csr_path = os.path.join(raw_apk_dir, 'META-INF', item)
    if not csr_path:
        return dfs.err_csr_file_not_exist, None
    cmd = "cd /tmp && openssl pkcs7 -in {} -inform DER -print_certs -out cert.pem " \
          "&& openssl x509 -in cert.pem -noout -text".format(csr_path)
    s, o = commands.getstatusoutput(cmd)
    logging.info('>>>{}\n>>>{}'.format(cmd, o))
    if s != 0:
        logging.fatal('exe [{}] failed.reason:[{}]'.format(cmd, o))
        return dfs.err_get_pub_key, None
    ptn = re.compile(r'Modulus:([\s\S]*?)Exponent')
    out = ptn.findall(o)
    if not out:
        logging.fatal('cannot find pub key in output:[{}]'.format(o))
        return dfs.err_get_pub_raw_str, None
    pub_key_list = re.compile(r'([a-f0-9]+)').findall(out[0])
    if not pub_key_list:
        logging.fatal('cannot find pub key detail in pub key:[{}]'.format(out[0]))
        return dfs.err_get_pub_str, None
    pub_key = ''.join(pub_key_list)
    for i, ch in enumerate(pub_key):
        if ch != '0':
            return 0, pub_key[i:]
    return 0, '0'


def do_work(params):
    gradle_bin = params['compiler']
    out_file = params['log_file']
    work_dir = params['work_dir']
    fp_keystore = params['keystore']
    signed_apk_path = params['signed_apk_path']

    ec, pub_key_str = get_pub_key(work_dir, signed_apk_path)
    if ec != 0:
        return ec
    tmp_so_prj_path = os.path.join(work_dir, 'CryptPrj')
    if not _call('cp -r {} {}'.format(so_seed_prj_path, tmp_so_prj_path)):
        return dfs.err_cp_encrpt_prj
    while 1:
        ec = build_so_prj(tmp_so_prj_path, gradle_bin, pub_key_str, out_file)
        if ec != 0:
            break
        ec, apk_file = replace_so_file(work_dir, tmp_so_prj_path, signed_apk_path, fp_keystore)
        if ec != 0:
            break
        # finally apk path.
        params['signed_apk_path'] = apk_file
        break
    # remove tmp project.
    _call("rm -rf {}".format(tmp_so_prj_path))
    return ec
