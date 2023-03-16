# 自动杀死高资源占用进程
import subprocess
import re
import time
import sys
import os
import traceback
import copy
from datetime import datetime
from pprint import pprint
import argparse
import shutil


def get_nvidia_processes():
    (status, result) = subprocess.getstatusoutput('nvidia-smi')
    if status == 0:
        result = [re.split('[\s]+', i)[1:] for i in re.findall(r'[^\n\r]+(?=MiB)', result.split('Processes: ')[1])]
        result_L = []  # [{},..]
        for r in result:
            result_L.append({
                'gpu': r[0],  # 编号, 即 CUDA_VISIBLE_DEVICES
                'pid': r[-4],  # 进程PID
                'type': r[-3],  # 程序类型, 比如C
                'process': r[-2],  # 进程名
                'mem': float(r[-1]),  # 显存使用量(MiB)
            })
        return result_L
    return []


def get_ps_processes():
    means = [  # [(描述,处理函数),..]; 与返回结果每列依次对应
        ('user', str),  # 用户
        ('pid', str),  # 进程PID
        ('stat', str),  # 程序状态
        ('cpu', float),  # CPU使用率, 100相当于一个超线程占满
        ('mem', lambda x: int(x) / 1024),  # 内存(MB)
        ('vsz', lambda x: int(x) / 1024),  # 虚拟内存(MB)
        ('etime', lambda x: int(x) / 60),  # 进程运行时间(分钟)
        ('ctime', str),  # CPU累计时间([[DD-]hh:]mm:ss)
        ('command', str),  # 命令
    ]
    command = 'ps axo "user:100" -o " | %p | " -o "stat" -o " | %C | " -o "size" -o " | %z | " -o "etimes" -o " | %t | %a" --sort pid --width 10000'
    # 输出一行例如: root | 37170 | S |  0.0 |   152 |   1512 | 1210445 | 14-00:14:05 | tail -f /running
    (status, result) = subprocess.getstatusoutput(command)
    if status != 0:
        return []
    result_L = []  # [{},..]
    for line in result.split('\n')[1:]:
        line = [i.strip() for i in re.split(r' [|] ', line)]
        result_L.append({})
        for i, (j, k) in enumerate(means):
            result_L[-1][j] = k(line[i])
    return result_L


def get_user_processes():
    pid_gpu8mem_D = {}  # {pid:{gpu:memory,..},..}
    ps_processes = get_ps_processes()
    for result in get_nvidia_processes():
        pid = result['pid']
        gpu = result['gpu']
        memory = result['mem']
        if pid in pid_gpu8mem_D:
            if gpu in pid_gpu8mem_D[pid]:
                pid_gpu8mem_D[pid][gpu] += memory
            else:
                pid_gpu8mem_D[pid][gpu] = memory
        else:
            pid_gpu8mem_D[pid] = {gpu: memory}
    user_processes = {}
    for result in ps_processes:
        user_process = user_processes.setdefault(result['user'], {  # 每个用户记录内容
            'cpu': 0,  # 总cpu使用率
            'mem': 0,  # 总内存GB
            'vsz': 0,  # 总虚拟内存GB
            'gmem': 0,  # 总显存GB
            'gtime': 0,  # 总gpu运行小时
            'gcard': set(),  # 所有占用的显卡编号
            'gpid': set(),  # 所有占用显卡的pid
            'pro': [],  # [{},..]; 每个进程信息和{gpu:memory,..}, 参见 get_ps_processes()
        })
        user_process['cpu'] += result['cpu']
        user_process['mem'] += result['mem'] / 1024
        user_process['vsz'] += result['vsz'] / 1024
        del result['user']
        user_process['pro'].append(result)
        if result['pid'] in pid_gpu8mem_D:
            user_process['gmem'] += sum(pid_gpu8mem_D[result['pid']].values()) / 1024
            user_process['gtime'] += result['etime'] / 60
            user_process['gcard'] |= set(pid_gpu8mem_D[result['pid']])
            user_process['gpid'].add(result['pid'])
            user_process['pro'][-1]['gpu_mem'] = pid_gpu8mem_D[result['pid']]
    return user_processes


def kill_processes(config_, test=False):
    user_processes = get_user_processes()
    for i in set(config_['ignore_u']) - set(config_['include_u']):
        if i in user_processes:
            del user_processes[i]
    if test:
        print('user_processes:')
        pprint(user_processes)
    for user, v in user_processes.items():
        config = config_.copy()
        # 特殊配置的用户
        for conf in config_['conf']:
            if user in conf['conf_u']:
                config.update(conf)
        # 用户的特殊设置
        if user in config_['user']:
            config.update(config_['user'][user])
        config['user'] = None
        config['conf'] = None
        config['conf_u'] = None
        if test:
            print('使用的 config ：')
            pprint(config)
        #
        del_pids = {}  # {pid:{},..}; 需要杀死的pid和进程
        error_pids = {}  # {'错误信息':{要删除的pid,..}}
        processes = sorted(v['pro'], key=lambda t: t['etime'])  # 运行时间顺序, 优先杀死最新运行的程序
        processes_gpu = [i for i in processes if i['pid'] in v['gpid']]  # gpu 程序
        #
        x, n = v['cpu'], 0
        error = '用户占用的cpu百分比 = ' + str(x) + ' > ' + str(config['cpu_core_u'])
        while x > config['cpu_core_u']:
            p = processes[n]  # 取出一个进程
            del_pids[p['pid']] = p  # 加入删除
            x -= p['cpu']
            n += 1
            error_pids.setdefault(error, set())  # 错误信息
            error_pids[error].add(p['pid'])  # 加入错误pid
        #
        x, n = v['mem'], 0
        error = '用户占用的内存(GB) = ' + str(x) + ' > ' + str(config['cpu_mem_u'])
        while x > config['cpu_mem_u']:
            p = processes[n]  # 取出一个进程
            del_pids[p['pid']] = p  # 加入删除
            x -= p['mem'] / 1024
            n += 1
            error_pids.setdefault(error, set())  # 错误信息
            error_pids[error].add(p['pid'])  # 加入错误pid
        #
        x, n = len(v['gcard']), 0
        error = '用户占用的显卡数量 = ' + str(x) + ' > ' + str(config['gpu_card_u'])
        while x > config['gpu_card_u']:
            p = processes_gpu[n]  # 取出一个进程
            del_pids[p['pid']] = p  # 加入删除
            x = len(set(j for i in processes_gpu[n + 1:] for j in i['gpu_mem'].keys()))
            n += 1
            error_pids.setdefault(error, set())  # 错误信息
            error_pids[error].add(p['pid'])  # 加入错误pid
        #
        x, n = v['gmem'], 0
        error = '用户占用的显存(GB) = ' + str(x) + ' > ' + str(config['gpu_mem_u'])
        while x > config['gpu_mem_u']:
            p = processes_gpu[n]  # 取出一个进程
            del_pids[p['pid']] = p  # 加入删除
            x -= sum(p['gpu_mem'].values()) / 1024
            n += 1
            error_pids.setdefault(error, set())  # 错误信息
            error_pids[error].add(p['pid'])  # 加入错误pid
        # 单进程
        for p in processes_gpu:
            # 最多显卡(张)
            if len(p['gpu_mem']) > config['gpu_card']:
                del_pids[p['pid']] = p  # 加入删除
                error = '单进程占用的显卡数量 > ' + str(config['gpu_card'])
                error_pids.setdefault(error, set())  # 错误信息
                error_pids[error].add(p['pid'])  # 加入错误pid
            # 最大显存(MB)
            if sum(p['gpu_mem'].values()) > config['gpu_mem']:
                del_pids[p['pid']] = p  # 加入删除
                error = '单进程占用的显存(MB) > ' + str(config['gpu_mem'])
                error_pids.setdefault(error, set())  # 错误信息
                error_pids[error].add(p['pid'])  # 加入错误pid
            # 最长gpu时间(天)
            if p['etime'] / 60 / 24 > config['gpu_day']:
                del_pids[p['pid']] = p  # 加入删除
                error = '单进程占用显卡的时间(天) > ' + str(config['gpu_day'])
                error_pids.setdefault(error, set())  # 错误信息
                error_pids[error].add(p['pid'])  # 加入错误pid
        for p in processes:
            # 最长cpu时间(天)
            if p['etime'] / 60 / 24 > config['cpu_day'] and p['cpu'] > config['cpu_day_core_limit']:
                del_pids[p['pid']] = p  # 加入删除
                error = '单进程占用cpu(%%>%d)的时间(天) > ' % config['cpu_day_core_limit'] + str(config['cpu_day'])
                error_pids.setdefault(error, set())  # 错误信息
                error_pids[error].add(p['pid'])  # 加入错误pid
        # 删除
        if del_pids:
            print(str(datetime.now()), '用户', user, '超出的资源限制/即将杀死的进程PID:')
            pprint(error_pids)
            print('kill-processes:')
            for i, (pid, pro) in enumerate(del_pids.items()):
                print(i + 1, '-', pro)
                if not test:
                    subprocess.getstatusoutput('kill -9 ' + pid)
            print()


def get_dev_nvidia():
    (status, output) = subprocess.getstatusoutput('nvidia-smi --query-compute-apps=pid --format=csv,noheader')
    used_pids = set([i for i in output.strip().split('\n') if i.isdigit()])
    (status, output) = subprocess.getstatusoutput('lsof /dev/nvidia*')
    processes = {}
    pattern = re.compile(r'(\S+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S*)\s+(\S+)\s+(.*)')
    for line in output.strip().split('\n'):
        match = pattern.match(line.strip())
        if match:
            command, pid, user, fd, file_type, device, size_off, node, name = match.groups()
            processes.setdefault(pid, {
                'command': command, 
                'user': user, 
                'used': pid in used_pids,  # 是否可以在 nvidia-smi 命令中看到
                'files': [],
            })['files'].append({
                'fd': fd,  # 文件描述符。可能的值包括：数字、字母（如 cwd，rtd，txt，mem 等）或数字加字母（如 0r，1w 等）
                'file_type': file_type,  # 文件类型。可能的值包括：REG（普通文件）、DIR（目录）、CHR（字符设备）、BLK（块设备）、FIFO（命名管道）等。
                'device': device,  # 设备号。格式为 主设备号,次设备号
                'size_off': size_off,  # 文件大小或偏移量
                'node': node,  # 节点号
                'name': name  # 文件名或设备名
            })
    return processes


def main():
    parser = argparse.ArgumentParser(description='用于限制linux系统的cpu/gpu资源使用')
    parser.add_argument('-c', default='kill.config', help='配置文件路径, 文件不存在会自动创建一个默认配置')  # 配置文件路径
    parser.add_argument('-t', action="store_true", help='是否进行测试, 测试不会杀死进程, 并修改为容易触发kill的参数')
    parser.add_argument('--knp', default='', help='kill nvidia python user, 退出某用户在显卡中的python进程, 会忽略其他功能')
    parser.add_argument('--knp2', default='', help='和knp类似,但是是删除这些用户以外的没有在nvidia-smi命令中显示的占用nvidia设备的python进程,可以填任意用户或非用户,英文逗号分隔.有可能因为删除相关进程而误影响到显卡进程,可以排除不想动的用户')
    args, unknown = parser.parse_known_args()  # 忽略未知参数
    if args.knp != '':
        os.system(
            '''up1kEK9m=$(lsof /dev/nvidia* | grep -E python.+%s); echo -e "$up1kEK9m\\nStart killing in 5 seconds"; sleep 5; echo "$up1kEK9m" | awk '{print $2}' | xargs -I {} kill -9 {}''' % args.knp)
        sys.exit(0)
    if args.knp2 != '':
        no_kill_users = set(args.knp2.split(','))
        user_pids = {}  # {user:{pid,..},..}
        processes = get_dev_nvidia()
        for k, v in processes.items():
            if not v['used'] and 'python' in v['command'] and v['user'] not in no_kill_users:
                user_pids.setdefault(v['user'], set()).add(k)
        if user_pids:
            print('10秒后将kill的进程:')
            kill_pids = set()  # {pid,..}
            for k, v in user_pids.items():
                print(k, sorted(v))
                kill_pids |= v
            time.sleep(10)
            print('开始kill...')
            for i in kill_pids:
                os.system('kill -9 ' + i)
            print('完成{}个进程的kill'.format(len(kill_pids)))
        else:
            print('没有需要kill的进程')
        sys.exit(0)

    args.c = os.path.expanduser(args.c)  # 可以使用 ~ 表示用户目录
    if not os.path.exists(args.c):
        # 自动寻找默认 kill.config 的位置
        default_config_path = subprocess.getstatusoutput(
            'py=$(which python) && echo ${py%bin*}lib/python*/site-packages/tsc_auto/kill.config')
        # 没有报错
        if default_config_path[0] == 0:
            default_config_path = default_config_path[1]
        else:
            raise NameError(str(default_config_path) + ' 寻找 ...lib/python*/site-packages/tsc_auto/kill.config 错误!')
        shutil.copyfile(default_config_path, args.c)
        print('创建了一个默认配置:', args.c)
    else:
        print('使用配置:', args.c)
    # 默认配置
    config = {
        's': 10,  # 多少秒检测一次
        'cpu_core_u': 2147483647,  # 一个用户-最多CPU占用(百分比,如100表示占满1个超线程)
        'cpu_mem_u': 2147483647,  # 一个用户-最大内存(GB), 也许是因为进程共享内存, 这个累计内存参数计算不准
        'gpu_card_u': 2,  # 一个用户-最多显卡(张)
        'gpu_mem_u': 30,  # 一个用户-最大显存(GB)
        'gpu_card': 1,  # 单进程-最多显卡(张)
        'gpu_mem': 23000,  # 单进程-最大显存(MB)
        'gpu_day': 20,  # 单进程-最长显卡占用时间(天)
        'cpu_day': 20,  # 单进程-最长cpu占用时间(天)
        'cpu_day_core_limit': 80,  # CPU占用百分比超过此值的进程才会使 cpu_day 配置生效
        'include_u': set(),  # 不可忽略的用户, 优先级高于 ignore_u
        # 忽略的用户, 默认会包含 /etc/passwd 中路径不含有 /home/ 的用户
        'ignore_u': {i.split(':')[0] for i in open('/etc/passwd').readlines() if '/home/' not in i},
        # 'ignore_u': os.popen("cat /etc/passwd | grep -v '/home/' | awk -F ':' '{print $1}'").read().splitlines(),
        # 针对每个特殊配置设置用户，没写的默认使用上述设置，越靠list后面的优先级越高会覆盖前面一样的用户配置
        'conf': [
            {  # 一组配置和对应的用户
                'gpu_mem_u': 45,
                'gpu_card_u': 3,
                'gpu_card': 2,
                'gpu_mem': 25000,
                'conf_u': {'tanshicheng'},  # 使用这组配置的用户
            },
        ],
        # 针对每个用户的额外配置, 没写的默认使用上述设置，优先级最高
        'user': {
            'tanshicheng': {
                'gpu_mem_u': 45,
                'gpu_card_u': 3,
                'gpu_card': 2,
                'gpu_mem': 25000,
            },
        },
    }
    # 加参数测试, 测试的时候使用容易出发kill的参数
    if args.t:
        print('测试...不杀死进程\n')
        config.update({
            'cpu_core_u': 50,
            'cpu_mem_u': 1,
            'gpu_card_u': 0,
            'gpu_mem_u': 0,
            'gpu_card': 0,
            'gpu_mem': 1,
            'gpu_day': 1,
            'cpu_day': 1,
            'cpu_day_core_limit': 0,
        })
        # config['include_u'].add('root')  # 加入 root 进行测试
    # 防止进程重复运行
    if not args.t:
        std = subprocess.Popen(["pgrep", "-f", __file__], stdout=subprocess.PIPE).communicate()
        if len(std[0].decode().split()) > 1:
            exit('Already running')
    # 开始不断检测
    while True:
        if args.t:
            print('\n测试 - ', str(datetime.now()))
        if os.path.isfile(args.c):
            try:
                config_new = copy.deepcopy(config)
                with open(args.c, 'r', encoding='utf8') as r:
                    for k, v in eval(r.read().strip()).items():  # 小心eval恶意插入代码
                        config_new.setdefault(k, v)
                        if isinstance(v, dict):
                            config_new[k].update(v)
                        elif isinstance(v, set):
                            config_new[k] |= v
                        else:
                            config_new[k] = v
                if config != config_new:
                    print(str(datetime.now()), '重新加载约束条件!')  # 没有输出这行注意可能是config路径不对
                    if args.t:
                        pprint(config_new)
                        print()
                    config = config_new
            except:
                traceback.print_exc()
                print()
        kill_processes(config, args.t)
        time.sleep(config['s'])


if __name__ == '__main__':
    main()
