# coding:utf-8


import subprocess
import tornado.ioloop
import time
import fcntl
import functools
import os
import logging


class GenericSubprocess(object):
    def __init__(self, timeout=-1, **popen_args):
        self.args = dict()
        self.args["stdout"] = subprocess.PIPE
        self.args["stderr"] = subprocess.PIPE
        self.args["close_fds"] = True
        self.args.update(popen_args)
        self.ioloop = None
        self.expiration = None
        self.pipe = None
        self.timeout = timeout
        self.streams = []
        self.has_timed_out = False

    def start(self):
        """Spawn the task.
        Throws RuntimeError if the task was already started."""
        if not self.pipe is None:
            raise RuntimeError("Cannot start task twice")
        self.ioloop = tornado.ioloop.IOLoop.instance()
        if self.timeout > 0:
            self.expiration = self.ioloop.add_timeout(time.time() + self.timeout, self.on_timeout)
        self.pipe = subprocess.Popen(**self.args)
        self.streams = [(self.pipe.stdout.fileno(), []),
                        (self.pipe.stderr.fileno(), [])]
        for fd, d in self.streams:
            flags = fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NDELAY
            fcntl.fcntl(fd, fcntl.F_SETFL, flags)
            self.ioloop.add_handler(fd,
                                    self.stat,
                                    self.ioloop.READ | self.ioloop.ERROR)

    def on_timeout(self):
        self.has_timed_out = True
        self.cancel()

    def cancel(self):
        """Cancel task execution
        Sends SIGKILL to the child process."""
        try:
            self.pipe.kill()
        except:
            pass

    def stat(self, *args):
        '''Check process completion and consume pending I/O data'''
        self.pipe.poll()
        if not self.pipe.returncode is None:
            '''cleanup handlers and timeouts'''
            if not self.expiration is None:
                self.ioloop.remove_timeout(self.expiration)
            for fd, dest in self.streams:
                self.ioloop.remove_handler(fd)
            '''schedulle callback (first try to read all pending data)'''
            self.ioloop.add_callback(self.on_finish)
        for fd, dest in self.streams:
            while True:
                try:
                    data = os.read(fd, 4096)
                    if len(data) == 0:
                        break
                    dest.extend([data])
                except:
                    break

    @property
    def stdout(self):
        return self.get_output(0)

    @property
    def stderr(self):
        return self.get_output(1)

    @property
    def status(self):
        return self.pipe.returncode

    def get_output(self, index):
        return "".join(self.streams[index][1])

    def on_finish(self):
        raise NotImplemented()

    def __del__(self):
        logging.info('I am dead.')


class Subprocess(GenericSubprocess):
    def __init__(self, callback, *args, **kwargs):
        self.callback = callback
        self.done_callback = False
        GenericSubprocess.__init__(self, *args, **kwargs)

    def on_finish(self):
        if not self.done_callback:
            self.done_callback = True
            '''prevent calling callback twice'''
            self.ioloop.add_callback(
                functools.partial(self.callback, self.status, self.stdout, self.stderr, self.has_timed_out))


if __name__ == "__main__":
    ioloop = tornado.ioloop.IOLoop.instance()


    def print_timeout(status, stdout, stderr, has_timed_out):
        assert (status != 0)
        assert (has_timed_out)
        print "OK status:", repr(status), "stdout:", repr(stdout), "stderr:", repr(stderr), "timeout:", repr(
            has_timed_out)


    def print_ok(status, stdout, stderr, has_timed_out):
        assert (status == 0)
        assert (not has_timed_out)
        print "OK status:", repr(status), "stdout:", repr(stdout), "stderr:", repr(stderr), "timeout:", repr(
            has_timed_out)


    def print_error(status, stdout, stderr, has_timed_out):
        assert (status != 0)
        assert (not has_timed_out)
        print "OK status:", repr(status), "stdout:", repr(stdout), "stderr:", repr(stderr), "timeout:", repr(
            has_timed_out)


    def stop_test():
        ioloop.stop()


    t1 = Subprocess(print_timeout, timeout=3, args=["sleep", "5"])
    t2 = Subprocess(print_ok, timeout=3, args=["ip", "a"])
    t3 = Subprocess(print_ok, timeout=3, args=["sleepdsdasdas", "1"])
    t4 = Subprocess(print_error, timeout=3, args=["cat", "/etc/sdfsdfsdfsdfsdfsdfsdf"])
    t1.start()
    t2.start()
    try:
        t3.start()
        assert False, ""
    except:
        print "OK"
    t4.start()
    ioloop.add_timeout(time.time() + 10, stop_test)
    ioloop.start()
