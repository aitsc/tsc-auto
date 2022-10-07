import argparse
import os
import time


def main():
    parser = argparse.ArgumentParser(description='断线自动重连ssh, 格式: ressh [自带参数] ssh参数',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--tmux', action='store_true', help='是否自动进入tmux')
    parser.add_argument('--password', type=str, default=None, help='ssh连接的密码(先正常登录一次)')
    parser.add_argument('--try_interval', type=float, default=1, help='断线重连接的间隔时间,单位秒')
    args, cmd_ = parser.parse_known_args()
    # 构建命令
    cmd_ = ['-o ServerAliveInterval=5 -o ServerAliveCountMax=3'] + cmd_
    if args.tmux:
        if args.password:
            cmd_ = ['-t -o RemoteCommand=tmux\\ a||~/tmux\\ a||tmux||~/tmux'] + cmd_
        else:
            cmd_ = ['-t -o RemoteCommand="tmux a||~/tmux a||tmux||~/tmux"'] + cmd_
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
