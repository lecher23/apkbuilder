# coding:utf-8
from __future__ import unicode_literals
import logging


class BuildExecutor(object):
    def __init__(self, s_processors, params):
        self.params = params
        self.processors = s_processors

    def execute(self):
        for processor in self.processors:
            logging.info('begin process:%s\nparams:%s', processor, self.params)
            pkg = __import__(processor)
            module_name = processor[processor.rfind('.') + 1:]
            module = getattr(pkg, module_name)
            exit_code = module.do_work(self.params)
            if exit_code != 0:
                logging.info('do process {} failed, exit code: {}'.format(processor, exit_code))
                return exit_code
        return 0
