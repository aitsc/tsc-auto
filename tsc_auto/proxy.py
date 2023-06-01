import argparse
import os
import subprocess


def main():
    parser = argparse.ArgumentParser(description='代理工具',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--tp__port', type=int, default=None, help='访问服务器的转发代理端口,默认24943')
    parser.add_argument('--tp__ip', type=str, default=None, help='访问服务器的转发代理ip,默认127.0.0.1')
    parser.add_argument('--tp__socks5', action='store_true', help='是否使用socks5协议,默认http')
    args, cmd_ = parser.parse_known_args()
    # cmd_ 空格处理
    for i, v in enumerate(cmd_):
        if ' ' in v and '"' not in v:
            cmd_[i] = '"{}"'.format(v)
    # 自动寻找 proxychains4 的位置
    pc4 = subprocess.getstatusoutput(
        'py=$(which python) && echo ${py%bin*}lib/python*/site-packages/tsc_auto/proxychains4')
    # 没有报错
    if pc4[0] == 0:
        pc4 = pc4[1]
        if '/site-packages/tsc_auto/proxychains4 ' in pc4:
            # 因为 conda 安装 python3.10 会出现名叫 python3.1 的文件夹
            pc4 = pc4.rsplit('/site-packages/tsc_auto/proxychains4 ', 1)[1]
        pc4_conf = os.path.join(os.path.dirname(pc4), 'proxychains.config')
        pc4_so = os.path.join(os.path.dirname(pc4), 'libproxychains4.so')
    else:
        raise NameError(str(pc4) + ' 寻找proxychains4错误!')
    # 运行
    cmd = 'chmod 777 {} {} ; {} -f {} '.format(pc4, pc4_so, pc4, pc4_conf) + ' '.join(cmd_)
    if args.tp__port and args.tp__port != 24943 or args.tp__ip and args.tp__ip != '127.0.0.1' or args.tp__socks5:
        cmd_add = 'cp {} ~/.proxychains.config && '.format(pc4_conf)
        if args.tp__port:
            cmd_add += 'sed -i "s/24943/{}/g" ~/.proxychains.config && '.format(args.tp__port)
        if args.tp__ip:
            cmd_add += 'sed -i "s/127.0.0.1/{}/g" ~/.proxychains.config && '.format(args.tp__ip)
        if args.tp__socks5:
            cmd_add += 'sed -i "s/http/socks5/g" ~/.proxychains.config && '
        cmd = cmd_add + cmd.replace(pc4_conf, '~/.proxychains.config')
        cmd += '; rm ~/.proxychains.config'
    os.system(cmd)


if __name__ == "__main__":
    main()
