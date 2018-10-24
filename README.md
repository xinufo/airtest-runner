# airtest-runner

## 功能

1. 脚本批量执行
2. 每个脚本执行日志分开存放
3. 每个脚本单独生成一个html报告并在父文件夹生成一个聚合报告

## 使用

- 用例文件夹需要以“用例集”结尾才能识别
- 脚本里的业务逻辑需要封装成runCase方法，签名如下

```python
def runCase(self, vars):
    # 业务逻辑代码
    pass
```

命令

```shell
# 执行测试
python runner.py YOUR_SCRIPT_DIR

# 生成报告
python report.py YOUR_LOG_DIR
```

## 目录结构

```shell
root
├─report.py                # 生成报告
├─runner.py                # 执行脚本
├─summary_template.html    # 报告模板
├─util.py                  # 工具类
├─交易用例集
│      ├──交易失败          #图片存放目录
│      ├──交易成功
│      ├──交易失败.py       #测试用例
│      └──交易成功.py
└─登录用例集
        ├──登录失败.py
        └──登录成功.py
```

图片可以与脚本同级，无需特殊处理；也可单独置于与脚本同名的文件夹中，此时需配合util.py中的img方法使用，例如`Template(img("登录"))`

> 注意：此启动器只针对airtest开发，poco并未测试，不能保证顺利执行
