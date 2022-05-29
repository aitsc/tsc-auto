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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='输入参数')
    parser.add_argument('-t', default='', help='token')
    parser.add_argument('-c', default='', help='执行指令')
    parser.add_argument('-d', default='', help='命令执行的退出状态')
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
        '结束时间': str(datetime.now()),
        '执行指令': args.c,
        '命令退出状态': args.d,
        '运行机信息': set_gpu(showAllGpu=False, return_more=True),
    }
    ret = send_wechat('ta-{}: '.format(args.d) + args.c[:50], json.dumps(content, ensure_ascii=False, indent=4), args.t)
    print('notification:', ret)
