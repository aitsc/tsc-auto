import requests
import json
try:
    from set_gpu import set_gpu
except:
    from .set_gpu import set_gpu
from datetime import datetime
import argparse
import sys
import os
import fcntl


def send_wechat(title: str, content: str, token: str, template='txt', channel='wechat'):
    """发送消息接口: http://www.pushplus.plus/doc/guide/api.html

    Args:
        title (str): 消息标题
        content (str): 具体消息内容，根据不同template支持不同格式
        token (str): 用户令牌
        template (str, optional): 发送模板, 例如 txt html json markdown
        channel (str, optional): 发送渠道
    """
    data = {
        'token': token,
        'title': title,
        'content': content,
        'template': template,
        'channel': channel,
    }
    r = requests.post(url='https://www.pushplus.plus/send', data=json.dumps(data))
    return r.text


def get_time_diff(s: str, e: str):
    """自动计算两个时间的差, 自动赋予单位, 秒/分钟/小时/天

    Args:
        s (str): 开始时间, 格式: date "+%Y-%m-%d %H:%M:%S.%N|cut -c 1-26" = 2022-05-24 18:18:59.574227
        e (str): 结束时间, 格式和s一样
    """
    try:
        s = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")
        e = datetime.strptime(e, "%Y-%m-%d %H:%M:%S.%f")
    except:
        return ''
    diff = datetime.timestamp(e) - datetime.timestamp(s)
    unit = '秒'
    if diff > 120:
        diff = diff / 60
        unit = '分钟'
        if diff > 120:
            diff = diff / 60
            unit = '小时'
            if diff > 48:
                diff = diff / 24
                unit = '天'
    return '{} {}'.format(round(diff, 2), unit)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='输入参数')
    parser.add_argument('-t', default='', help='token')
    parser.add_argument('-c', default='', help='执行指令')
    parser.add_argument('-d', default='', help='命令执行的退出状态')
    parser.add_argument('-s', default='', help='程序开始执行时间, 格式参考 get_time_diff')
    parser.add_argument('-e', default='', help='程序结束执行时间, 格式参考 get_time_diff')
    args = parser.parse_args()
    # print(args.c, args.t)
    if args.c == '':
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, os.O_NONBLOCK)
        try:
            cc = sys.stdin.read()
            args.c = cc.strip()
        except:
            ...
    if args.c == '' or args.t == '':
        sys.exit(0)
    content = {
        '结束执行时间': args.e,
        '开始执行时间': args.s,
        '总耗时': get_time_diff(args.s, args.e),
        '执行指令': args.c,
        '命令退出状态': args.d,
        '执行结束后的机器状态': {k: '; '.join([str(i) for i in v]) if isinstance(v, list) else v for k, v in set_gpu(return_more=True, public_net=True).items()},
    }
    ret = send_wechat('ta-{}: '.format(args.d) + args.c[:90], json.dumps(content, ensure_ascii=False, indent=4), args.t)
    print('notification:', ret)
