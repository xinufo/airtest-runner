# -*- coding: utf-8 -*-

import os
import io
import types
import shutil
import json
import jinja2
from airtest.utils.compat import decode_path
import airtest.report.report as R

HTML_FILE = "log.html"
HTML_TPL = "log_template.html"
STATIC_DIR = os.path.dirname(R.__file__)

def get_parger(ap):
    ap.add_argument("script", help="script filepath")
    ap.add_argument("--outfile", help="output html filepath, default to be log.html")
    ap.add_argument("--static_root", help="static files root dir")
    ap.add_argument("--log_root", help="log & screen data root dir, logfile should be log_root/log.txt")
    ap.add_argument("--record", help="custom screen record file path", nargs="+")
    ap.add_argument("--export", help="export a portable report dir containing all resources")
    ap.add_argument("--lang", help="report language", default="en")
    ap.add_argument("--plugins", help="load reporter plugins", nargs="+")
    return ap


def get_script_info(script_path):
    script_name = os.path.basename(script_path)
    result_json = {"name": script_name, "author": None, "title": script_name, "desc": None}
    return json.dumps(result_json)


def _make_export_dir(self):
    dirpath = self.script_root
    logpath = self.script_root
    # copy static files
    for subdir in ["css", "fonts", "image", "js"]:
        dist = os.path.join(dirpath, "static", subdir)
        shutil.rmtree(dist, ignore_errors=True)
        self.copy_tree(os.path.join(STATIC_DIR, subdir), dist)

    return dirpath, logpath


def report(self, template_name, output_file=None, record_list=None):
    """替换LogToHtml中的report方法"""
    self._load()
    steps = self._analyse()
    # 修改info获取方式
    info = json.loads(get_script_info(self.script_root))

    if self.export_dir:
        self.script_root, self.log_root = self._make_export_dir()
        output_file = os.path.join(self.script_root, HTML_FILE)
        self.static_root = "static/"

    if not record_list:
        record_list = [f for f in os.listdir(self.log_root) if f.endswith(".mp4")]
    records = [os.path.join(self.log_root, f) for f in record_list]

    if not self.static_root.endswith(os.path.sep):
        self.static_root = self.static_root.replace("\\", "/")
        self.static_root += "/"

    data = {}
    data['steps'] = steps
    data['name'] = os.path.basename(self.script_root)
    data['scale'] = self.scale
    data['test_result'] = self.test_result
    data['run_end'] = self.run_end
    data['run_start'] = self.run_start
    data['static_root'] = self.static_root
    data['lang'] = self.lang
    data['records'] = records
    data['info'] = info

    return self._render(template_name, output_file, **data)


def get_result(self):
    return self.test_result


def main(args):
    # script filepath
    path = decode_path(args.script)
    record_list = args.record or []
    log_root = decode_path(args.log_root) or path
    static_root = args.static_root or STATIC_DIR
    static_root = decode_path(static_root)
    export = decode_path(args.export) if args.export else None
    lang = args.lang if args.lang in ['zh', 'en'] else 'zh'
    plugins = args.plugins

    # gen html report
    rpt = R.LogToHtml(path, log_root, static_root, export_dir=export, lang=lang, plugins=plugins)
    # override methods
    rpt._make_export_dir = types.MethodType(_make_export_dir, rpt)
    rpt.report = types.MethodType(report, rpt)
    rpt.get_result = types.MethodType(get_result, rpt)

    rpt.report(HTML_TPL, output_file=args.outfile, record_list=record_list)

    return rpt.get_result()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    args = get_parger(ap).parse_args()
    basedir = os.path.dirname(os.path.realpath(__file__))
    logdir = os.path.realpath(args.script)

    # 聚合结果
    results = []

    # 遍历所有日志
    for subdir in os.listdir(logdir):
        if os.path.isfile(os.path.join(logdir, subdir)):
            continue
        args.script = os.path.join(logdir, subdir)
        args.outfile = os.path.join(args.script, HTML_FILE)
        result = {}
        result["name"] = subdir
        result["result"] = main(args)
        results.append(result)

    # 生成聚合报告
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(basedir),
        extensions=(),
        autoescape=True
    )
    template = env.get_template("summary_template.html")
    html = template.render({"results": results})

    output_file = os.path.join(logdir, "summary.html")
    with io.open(output_file, 'w', encoding="utf-8") as f:
        f.write(html)
    print(output_file)
