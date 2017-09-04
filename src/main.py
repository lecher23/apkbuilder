# coding: utf-8

import sys

reload(sys)
sys.setdefaultencoding("utf-8")

import os

CUR_PATH = os.getcwd()
if not os.path.exists(os.path.join(CUR_PATH, 'src')):
    sys.stderr.write('you must under project root dir.\n')
    exit(1)
sys.path.append(os.path.join(CUR_PATH, 'src'))

import torndb
import tornado.web
import tornado.ioloop
import api_handlers
import cfg_wrapper


def run(port, debug=False):
    settings['conf'] = cfg_wrapper.CfgWrapper(os.path.join(CUR_PATH, 'confs/srv.json'))
    app = tornado.web.Application(
        [
            (r'/pkg/build3rd', api_handlers.SubmitBuildHandler),
            (r'/pkg/buildsms', api_handlers.SubmitSmsBuildHandler),
            (r'/pkg/index', api_handlers.ChooseProjectHandler),
            (r'/pkg/status', api_handlers.BuildStatusHandler),
            (r'/pkg/setting', api_handlers.SettingProjectPageHandler)
        ],
        **settings
    )
    if debug:
        app.listen(port)
    else:
        app.listen(5007, address='127.0.0.1', xheaders=True)

    def stop_server(signum, frame):
        import logging
        logging.info("receive signal %d. begin stop process" % signum)
        settings['builder'].stop_builder(lambda: tornado.ioloop.IOLoop.current().stop())

    import signal
    signal.signal(signal.SIGTERM, stop_server)
    signal.signal(signal.SIGINT, stop_server)
    signal.signal(signal.SIGQUIT, stop_server)

    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    from tornado.options import options
    from workflow import BuildManager

    default_params = {
        '--log-to-stderr': 'True',
        '--log_file_prefix': os.path.join(CUR_PATH, 'logs/server.log'),
        '--logging': 'info',
        '--log_rotate_mode': 'time'
    }
    sys.argv += ['%s=%s' % (k, v) for k, v in default_params.items()]
    options.parse_command_line()

    bm = BuildManager(CUR_PATH)
    bm.run()
    settings = {
        'login_url': '/pkg/static/login.html',
        'cookie_secret': 'super-FanYu',
        'template_path': os.path.join(CUR_PATH, 'pages/views'),
        'static_path': os.path.join(CUR_PATH, 'pages/statics'),
        'static_url_prefix': '/pkg/static/',
        'root_path': CUR_PATH,
        'db': torndb.Connection('139.196.148.39', 'mimi2_db', 'mimi2_user', 'mimi2_111222', time_zone='+8:00'),
        'builder': bm
    }
    run(5007, True)
