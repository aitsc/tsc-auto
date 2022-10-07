import argparse
import os
import subprocess


def main():
    parser = argparse.ArgumentParser(description='代理工具, 默认使用的转发参数 -R 24943:127.0.0.1:7890',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--tp_port', type=str, default=None, help='访问服务器的转发代理端口')
    args, cmd_ = parser.parse_known_args()
    # 自动寻找 proxychains4 的位置
    pc4 = subprocess.getstatusoutput(
        'py=$(which python) && echo ${py%bin*}lib/python*/site-packages/tsc_auto/proxychains4')
    # 没有报错
    if pc4[0] == 0:
        pc4 = pc4[1]
        pc4_conf = os.path.join(os.path.dirname(pc4), 'proxychains.config')
    else:
        raise NameError(str(pc4) + ' 寻找proxychains4错误!')
    # 运行
    cmd = 'chmod 777 {} && {} -f {} '.format(pc4, pc4, pc4_conf) + ' '.join(cmd_)
    os.system(cmd)


if __name__ == "__main__":
    main()
