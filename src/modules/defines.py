# coding: utf-8

err_cp_prj = 1
err_prepare_app_conf = 2
err_build_apk = 3
err_upload_apk = 4
err_make_key_file = 5
err_clear_old_apk = 6
err_cp_icon = 7
err_cp_apk = 8
err_pull_code = 9
err_invalid_repo = 10
err_replace_strings = 11
err_invalid_param = 12
err_find_built_apk = 13
err_bad_build_gradle_file = 14
err_replace_so_signature = 15
err_build_so = 16
err_unzip_apk = 17
err_add_shell_to_so = 18
err_clear_apk_so = 19
err_mv_so_to_apk = 20
err_zip_apk = 21
err_get_so_from_build_dir = 22
err_gen_keystore = 23
err_unzip_target_apk = 24
err_resign_apk = 25
err_make_dir = 26
err_get_pub_key = 27
err_csr_file_not_exist = 28
err_get_pub_raw_str = 29
err_get_pub_str = 30
err_cp_encrpt_prj = 31
err_for_future = 999

ErrMapping = {
    err_cp_prj: "拷贝工程目录失败",
    err_prepare_app_conf: "修改编译配置失败",
    err_build_apk: "编译失败",
    err_upload_apk: "上传APK到CDN失败",
    err_make_key_file: "创建签名所需要的KEY失败",
    err_clear_old_apk: "清除编译缓存失败",
    err_cp_icon: "拷贝应用图标失败",
    err_cp_apk: "拷贝APK到产出目录失败",
    err_pull_code: "从GIT拉代码失败",
    err_invalid_repo: "错误的GIT仓库地址",
    err_replace_strings: "替换strings.xml失败",
    err_invalid_param: "启动打包进程参数错误",
    err_find_built_apk: "找不到打包后的APK",
    err_bad_build_gradle_file:"找不到gradle程序",
    err_replace_so_signature: "替换lib库中签名失败",
    err_build_so:"编译lib库失败",
    err_unzip_apk: "解压APK失败",
    err_add_shell_to_so: "给lib库加壳失败",
    err_clear_apk_so: "清理apk中lib库失败",
    err_mv_so_to_apk: "移动加壳后的lib库到APK失败",
    err_zip_apk: "APK重新归档失败",
    err_get_so_from_build_dir:"从编译工程中获取不到lib库",
    err_gen_keystore: "生成keystore签名文件失败",
    err_unzip_target_apk: "解压目标APK失败",
    err_resign_apk: "重新签名APK失败",
    err_make_dir:"创建文件夹失败",
    err_get_pub_key: "获取公钥失败",
    err_csr_file_not_exist: "CSR文件不存在",
    err_get_pub_raw_str: "获取原始公钥字符串失败",
    err_get_pub_str: "获取公钥字符串失败",
    err_cp_encrpt_prj: "拷贝lib工程代码失败",
    99: "系统异常,请联系管理员:licheng@touchtogame.com"
}

