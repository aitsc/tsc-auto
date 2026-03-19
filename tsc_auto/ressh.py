import argparse
import os
import time


def main():
    parser = argparse.ArgumentParser(description='断线自动重连ssh, 格式: ressh [自带参数] ssh参数',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--tmux', action='store_true', help='是否自动进入tmux')
    group.add_argument('--tmu', type=str, default=None, help='是否自动进入或新建指定名称的tmux会话')
    parser.add_argument('--password', type=str, default=None, help='ssh连接的密码(先正常登录一次)')
    parser.add_argument('--try_interval', type=float, default=3, help='断线重连接的间隔时间,单位秒')
    parser.add_argument('--tp', action='store_true', help='用于协助默认端口参数下的tp代理命令')
    parser.add_argument('--tp_r', type=str, default='24943:127.0.0.1:7890', help='tp远程端口转发信息')
    args, cmd_ = parser.parse_known_args()
    tmux_remote_command = 'tmux a||~/tmux a||tmux||~/tmux'
    tmu_remote_command = None if not args.tmu else 'tmux a -t {0}||~/tmux a -t {0}||tmux new -s {0}||~/tmux new -s {0}'.format(args.tmu)
    # 构建命令
    cmd_ = ['-o ServerAliveInterval=5 -o ServerAliveCountMax=3'] + cmd_
    if args.tp and args.tp_r:
        cmd_ = ['-R {}'.format(args.tp_r)] + cmd_
    if args.tmux:
        if args.password:
            cmd_ = ['-t -o RemoteCommand={}'.format(tmux_remote_command.replace(' ', '\\ '))] + cmd_  # 或者加双引号放在最后并去除 -o RemoteCommand
        else:
            cmd_ = ['-t -o RemoteCommand="{}"'.format(tmux_remote_command)] + cmd_
    if args.tmu:
        if args.password:
            cmd_ = ['-t -o RemoteCommand={}'.format(tmu_remote_command.replace(' ', '\\ '))] + cmd_  # 或者加双引号放在最后并去除 -o RemoteCommand
        else:
            cmd_ = ['-t -o RemoteCommand="{}"'.format(tmu_remote_command)] + cmd_
    cmd = 'ssh ' + ' '.join(cmd_)
    if args.password:
        cmd = """expect -c 'spawn {}; expect "*password:"; send "{}\\r"; interact'""".format(cmd, args.password)
    print(cmd)
    # 循环运行
    i_try = 0
    while True:
        i_try += 1
        if os.system(cmd):
            print('第 {} 次中断, {} 秒后重新连接...'.format(i_try, args.try_interval))
            time.sleep(args.try_interval)
        else:
            break


if __name__ == "__main__":
    main()
