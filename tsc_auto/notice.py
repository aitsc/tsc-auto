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
import time
import collections


def send_wechat(title: str, content: str, token: str, template='txt', channel='wechat'):
    """发送消息接口: http://www.pushplus.plus/doc/guide/api.html

    Args:
        title (str): 消息标题
        content (str): 具体消息内容，根据不同template支持不同格式
        token (str): 用户令牌
        template (str, optional): 发送模板, 例如 txt html json markdown
        channel (str, optional): 发送渠道

    Returns:
        ret (dict)
    """
    data = {
        'token': token,
        'title': title,
        'content': content,
        'template': template,
        'channel': channel,
    }
    ret = {"msg": "无法联网, 通知失败!"}
    for i in range(3):  # 失败后再尝试
        try:
            r = requests.post(url='https://www.pushplus.plus/send', data=json.dumps(data))
            ret = json.loads(r.text)
            break
        except:
            print('notification failed {} ...'.format(i+1))
            time.sleep(5)
    return ret


def get_time_diff(s: str, e: str):
    """自动计算两个时间的差, 自动赋予单位, 秒/分钟/小时/天

    Args:
        s (str): 开始时间, 格式: date "+%Y-%m-%d %H:%M:%S.%N|cut -c 1-26" = 2022-05-24 18:18:59.574227
        e (str): 结束时间, 格式和s一样

    Returns:
        str: 例如 3.1 秒
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


def explain_exit_code(code):
    """返回linux错误代码的一般含义和提示
    参考: 
        https://tldp.org/LDP/abs/html/exitcodes.html
        https://www.computerhope.com/unix/signals.htm
        https://blog.csdn.net/weixin_34261739/article/details/91785562

    Args:
        code (int, float, str): 错误代码

    Returns:
        dict: {'code':code,'meaning':'含义','comment':'提示'}; 没有一般含义的代码和可靠信号SIGRTMIN/SIGRTMAX等只有code
    """
    code_status = {
        0: {'meaning': '正常退出', 'comment': '程序执行完成'},
        1: {'meaning': '一般错误', 'comment': '例如“除以零”和其他禁止操作: let "var1 = 1/0"'},
        2: {'meaning': '错误使用 shell 内置程序(根据 Bash 文档)', 'comment': '缺少关键字或命令，或权限问题（如diff在二进制文件比较失败时的返回代码）'},
        126: {'meaning': '调用的命令无法执行', 'comment': '权限问题或命令不是可执行文件'},
        127: {'meaning': '“找不到相关命令”', 'comment': '例如 $PATH 或命令拼写错误'},
        128: {'meaning': '退出代码无效', 'comment': 'exit 不接受[0,255]整数以外的数: exit 3.14159'},
        128+1: {'meaning': '收到中断信号(1)SIGHUP', 'comment': '该信号通常表示控制终端或虚拟终端已关闭'},
        128+2: {'meaning': '收到中断信号(2)SIGINT', 'comment': '程序终止(interrupt)信号, 在用户键入INTR字符(通常是Ctrl-C)时发出，用于通知前台进程组终止进程'},
        128+3: {'meaning': '收到中断信号(3)SIGQUIT', 'comment': '和SIGINT类似, 但由QUIT字符(通常是Ctrl-\)来控制. 进程在因收到SIGQUIT退出时会产生core文件, 在这个意义上类似于一个程序错误信号'},
        128+4: {'meaning': '收到中断信号(4)SIGILL', 'comment': '执行了非法指令. 通常是因为可执行文件本身出现错误, 或者试图执行数据段. 堆栈溢出时也有可能产生这个信号'},
        128+5: {'meaning': '收到中断信号(5)SIGTRAP', 'comment': '由断点指令或其它trap指令产生. 由debugger使用'},
        128+6: {'meaning': '收到中断信号(6)SIGABRT', 'comment': '调用abort函数生成的信号'},
        128+7: {'meaning': '收到中断信号(7)SIGBUS', 'comment': '非法地址, 包括内存地址对齐(alignment)出错。比如访问一个四个字长的整数, 但其地址不是4的倍数'},
        128+8: {'meaning': '收到中断信号(8)SIGFPE', 'comment': '在发生致命的算术运算错误时发出. 不仅包括浮点运算错误, 还包括溢出及除数为0等其它所有的算术的错误'},
        128+9: {'meaning': '收到中断信号(9)SIGKILL', 'comment': '用来立即结束程序的运行, 例如内存不足被系统终止'},
        128+10: {'meaning': '收到中断信号(10)SIGUSR1', 'comment': '留给用户使用'},
        128+11: {'meaning': '收到中断信号(11)SIGSEGV', 'comment': '试图访问未分配给自己的内存, 或试图往没有写权限的内存地址写数据'},
        128+12: {'meaning': '收到中断信号(12)SIGUSR2', 'comment': '留给用户使用'},
        128+13: {'meaning': '收到中断信号(13)SIGPIPE', 'comment': '管道破裂。这个信号通常在进程间通信产生，比如采用FIFO(管道)通信的两个进程，读管道没打开或者意外终止就往管道写，写进程会收到SIGPIPE信号。此外用Socket通信的两个进程，写进程在写Socket的时候，读进程已经终止'},
        128+14: {'meaning': '收到中断信号(14)SIGALRM', 'comment': '时钟定时信号, 计算的是实际的时间或时钟时间. alarm函数使用该信号'},
        128+15: {'meaning': '收到中断信号(15)SIGTERM', 'comment': '程序结束(terminate)信号, 与SIGKILL不同的是该信号可以被阻塞和处理。通常用来要求程序自己正常退出'},
        128+16: {'meaning': '收到中断信号(16)SIGSTKFLT', 'comment': '堆栈故障。映射到Linux中的SIGUNUSED'},
        128+17: {'meaning': '收到中断信号(17)SIGCHLD', 'comment': '子进程结束时, 父进程会收到这个信号'},
        128+18: {'meaning': '收到中断信号(18)SIGCONT', 'comment': '让一个停止(stopped)的进程继续执行'},
        128+19: {'meaning': '收到中断信号(19)SIGSTOP', 'comment': '停止(stopped)进程的执行'},
        128+20: {'meaning': '收到中断信号(20)SIGTSTP', 'comment': '停止进程的运行, 但该信号可以被处理和忽略. 用户键入SUSP字符时(通常是Ctrl-Z)发出这个信号'},
        128+21: {'meaning': '收到中断信号(21)SIGTTIN', 'comment': '当后台作业要从用户终端读数据时, 该作业中的所有进程会收到SIGTTIN信号. 缺省时这些进程会停止执行'},
        128+22: {'meaning': '收到中断信号(22)SIGTTOU', 'comment': '类似于SIGTTIN, 但在写终端(或修改终端模式)时收到'},
        128+23: {'meaning': '收到中断信号(23)SIGURG', 'comment': '有"紧急"数据或out-of-band数据到达socket时产生'},
        128+24: {'meaning': '收到中断信号(24)SIGXCPU', 'comment': '超过CPU时间资源限制. 这个限制可以由getrlimit/setrlimit来读取/改变'},
        128+25: {'meaning': '收到中断信号(25)SIGXFSZ', 'comment': '当进程企图扩大文件以至于超过文件大小资源限制'},
        128+26: {'meaning': '收到中断信号(26)SIGVTALRM', 'comment': '虚拟时钟信号. 类似于SIGALRM, 但是计算的是该进程占用的CPU时间'},
        128+27: {'meaning': '收到中断信号(27)SIGPROF', 'comment': '类似于SIGALRM/SIGVTALRM, 但包括该进程用的CPU时间以及系统调用的时间'},
        128+28: {'meaning': '收到中断信号(28)SIGWINCH', 'comment': '窗口大小改变时发出'},
        128+29: {'meaning': '收到中断信号(29)SIGIO,SIGPOLL', 'comment': '文件描述符准备就绪, 可以开始进行输入/输出操作'},
        128+30: {'meaning': '收到中断信号(30)SIGPWR,SIGLOST', 'comment': '系统检测到停电时'},
        128+31: {'meaning': '收到中断信号(31)SIGUNUSED,SIGSYS', 'comment': '非法的系统调用. 此信号是出于兼容性原因提供的，例如在Linux中从具有不同或不支持信号的操作系统移植软件时'},
        255: {'meaning': '退出状态超出范围', 'comment': 'exit 不接受[0,255]整数以外的数: exit -1'},
    }
    try:
        code = int(code)
        status = {'code': code}
        if code in code_status:
            status.update(code_status[code])
    except:
        status = {'code': code}
    return status


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='输入参数')
    parser.add_argument('-t', default='', help='token')
    parser.add_argument('-c', default='', help='执行指令')
    parser.add_argument('-d', default='', help='命令执行的退出代码')
    parser.add_argument('-s', default='', help='程序开始执行时间, 格式参考 get_time_diff')
    parser.add_argument('-e', default='', help='程序结束执行时间, 格式参考 get_time_diff')
    args, unknown = parser.parse_known_args()  # 忽略未知参数
    # print(args, unknown)
    if args.c == '':
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, os.O_NONBLOCK)
        try:
            cc = sys.stdin.read()
            args.c = cc.strip()
        except:
            ...
    if args.c == '' or args.t == '':
        sys.exit(0)
    print('结束执行时间:', args.e, ', 总耗时:', get_time_diff(args.s, args.e), ', 退出代码:', args.d)
    machine = set_gpu(return_more=True, public_net=True)
    content = {
        '总耗时': get_time_diff(args.s, args.e),
        '执行目录': os.getcwd(),
        '开始执行时间': args.s,
        '结束执行时间': args.e,
        '执行指令': args.c,
        '命令退出状态(UNIX信号解释)': explain_exit_code(args.d),
        '执行结束后的机器状态(mem单位为MB)': {k: '; '.join([str(i) for i in v]) if isinstance(v, list) else v for k, v in machine.items()},
        '当前环境变量': collections.OrderedDict(sorted(os.environ.items(), key=lambda t: t[0])),
    }
    title = '{} {}: {}'.format(machine['hostname'], args.d, args.c)[:100]
    ret = send_wechat(title, json.dumps(content, ensure_ascii=False, indent=4)[:10000], args.t)
    print('notification:', ret)
