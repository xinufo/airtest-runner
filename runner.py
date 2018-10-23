# -*- coding: utf-8 -*-

import unittest
import os
import sys
import six
import traceback
import types
import time
from io import open
from airtest.cli.parser import runner_parser
from airtest.core.api import G, auto_setup, log
from airtest.core.settings import Settings as ST
from airtest.utils.compat import decode_path
from copy import copy

class MyAirtestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args = args

        setup_by_args(args)

        # setup script exec scope
        cls.scope = copy(globals())

    def setUp(self):
        if self.args.log and self.args.recording:
            for dev in G.DEVICE_LIST:
                try:
                    dev.start_recording()
                except:
                    traceback.print_exc()
        # 设置日志路径
        auto_setup(logdir=self._logdir)

    def tearDown(self):
        if self.args.log and self.args.recording:
            for k, dev in enumerate(G.DEVICE_LIST):
                try:
                    output = os.path.join(self.args.log, "recording_%d.mp4" % k)
                    dev.stop_recording(output)
                except:
                    traceback.print_exc()

    def runTest(self):
        try:
            # 调用脚本中的runCase方法并传递scope供脚本使用
            self.runCase(self.scope)
        except Exception as err:
            tb = traceback.format_exc()
            log("Final Error", tb)
            six.reraise(*sys.exc_info())

    @property
    def logdir(self):
        return self._logdir

    @logdir.setter
    def logdir(self, value):
        self._logdir = value

def setup_by_args(args):
    # init devices
    if isinstance(args.device, list):
        devices = args.device
    elif args.device:
        devices = [args.device]
    else:
        devices = []
        print("do not connect device")

    # set base dir to find tpl
    args.script = decode_path(args.script)

    # set log dir
    if args.log is True:
        print("save log in %s/log" % args.script)
        args.log = os.path.join(args.script, "log")
    elif args.log:
        print("save log in '%s'" % args.log)
        args.log = decode_path(args.log)
    else:
        print("do not save log")

    # guess project_root to be basedir of current .air path
    project_root = os.path.dirname(args.script) if not ST.PROJECT_ROOT else None
    # 此处不设置日志路径，防止生成多余的log.txt
    auto_setup(args.script, devices, None, project_root)

def new_case(py, logdir):
    """实例化MyAirtestCase并绑定runCase方法"""
    with open(py, 'r', encoding="utf8") as f:
        code = f.read()
    obj = compile(code.encode("utf-8"), py, "exec")
    ns = {}
    ns["__file__"] = py
    # exec obj in ns
    exec(obj, ns)
    func = ns["runCase"]
    case = MyAirtestCase()
    pyfilename = os.path.basename(py).replace(".py", "")
    # 设置属性以便在setUp中设置日志路径
    case.logdir = os.path.join(logdir, pyfilename)
    # 绑定runCase方法
    case.runCase = types.MethodType(func, case)
    return case

def init_log_folder():
    """初始化日志根目录"""
    name = time.strftime("log_%Y%m%d_%H%M%S", time.localtime())
    if not os.path.exists(name):
        os.mkdir(name)
    return name

def run_script(parsed_args, testcase_cls=MyAirtestCase):
    global args  # make it global deliberately to be used in MyAirtestCase & test scripts
    args = parsed_args
    dir = os.path.dirname(os.path.realpath(__file__))
    suites = []
    pys = []

    # 获取所有用例集
    for f in os.listdir(dir):
        if f.endswith("用例集"):
            f = os.path.join(dir, f)
            if os.path.isdir(f):
                suites.append(f)

    # 获取所有脚本
    for s in suites:
        for f in os.listdir(s):
            if f.endswith(".py") and not f.startswith("__"):
                pys.append(os.path.join(s, f))

    logdir = os.path.join(dir, init_log_folder())
    args.log = logdir
    suite = unittest.TestSuite()

    # 添加脚本
    for py in pys:
        case = new_case(py, logdir)
        suite.addTest(case)

    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        sys.exit(-1)

if __name__ == "__main__":
    ap = runner_parser()
    args = ap.parse_args()
    run_script(args, MyAirtestCase)