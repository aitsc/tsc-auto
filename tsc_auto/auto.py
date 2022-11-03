import os
import sys
import subprocess
import re
import time
from datetime import datetime
from pprint import pprint
try:
    from set_gpu import set_gpu
    from kill import get_user_processes
    from nvidia_htop import nvidia_htop
except:
    from .set_gpu import set_gpu
    from .kill import get_user_processes
    from .nvidia_htop import nvidia_htop


def get_current_user_cmd():
    username = subprocess.getstatusoutput('whoami')[1]
    user_processes = get_user_processes()
    if username not in user_processes:
        print('没有相关用户进程', username)
        return
    processes = user_processes[username]['pro']
    processes = sorted(processes, key=lambda t: t['command'])
    all_cmd = set()
    print('PID\tCommand')
    for i, p in enumerate(processes):
        if p['command'] in all_cmd:
            continue
        print(p['pid'], p['command'], sep='\t')
        all_cmd.add(p['command'])
    print('总共 {} 个程序, {} 种程序'.format(len(processes), i))


def benchmark():
    print('显卡(cuda:0)性能测试: cuda 11.7 下 3090Ti=85(理论160), V100 16GB=86(理论125), A100 80GB=231(理论312); cuda 11.4 下 2080Ti=58')
    import torch
    from torch.utils import benchmark
    typ = torch.float16
    n = 1024 * 16
    a = torch.randn(n, n).type(typ).cuda()
    b = torch.randn(n, n).type(typ).cuda()
    t = benchmark.Timer(stmt='a @ b', globals={'a': a, 'b': b})
    x = t.timeit(50)
    print(2*n**3 / x.median / 1e12)


def wait_gpus(para_L):
    args = {
        '-c': 0.1,  # 至少剩余多少gpu使用率, 百分比
        '-m': 0.8,  # 至少剩余多少显存, 小于1是百分比, 大于1是MB
        '-t': 10,  # 这些显卡至少连续几秒钟满足这些条件
        '-g': '',  # 等待哪些显卡,例如: 0,2
    }
    i = 0
    for p in para_L:
        if '=' in p and p.split('=')[0] in args:
            if p.split('=')[0] in {'-g'}:
                args[p.split('=')[0]] = p.split('=')[1]
            else:
                args[p.split('=')[0]] = float(p.split('=')[1])
        else:
            break
        i += 1
    para_L = para_L[i:]
    cmd = ' ' + ' '.join(para_L) + ' '
    # 获取gpus
    gpus = [int(i) for i in args['-g'].split(',') if i]
    # gpus = []
    # gpus_re = [
    #     r'(?<= --include=localhost:)\d[\d,]*(?= )',  # deepspeed
    #     r'(?<= CUDA_VISIBLE_DEVICES=)\d[\d,]*(?= )',
    # ]
    # for r in gpus_re:
    #     ret = re.search(r, cmd)
    #     if ret:
    #         gpus = [int(i) for i in ret.group().strip(',').split(',')]
    #         break
    # 等待命令
    print(cmd.strip())
    print('等待GPU {} 满足条件:'.format(gpus), args, datetime.now())
    gpu_info = {i: None for i in gpus}  # {序号:满足要求的时间,..}
    start = time.time()
    while True:
        ret = set_gpu(return_more=True)
        for g in gpu_info.keys():
            gpu_usage = ret['gpu_usage'][g]
            ext_gpu_mem = ret['ext_gpu_mem'][g]
            all_gpu_mem = ret['all_gpu_mem'][g]
            mem_rate = args['-m'] / all_gpu_mem if args['-m'] > 1 else args['-m']
            if (100 - gpu_usage) / 100 >= args['-c'] and ext_gpu_mem / all_gpu_mem >= mem_rate:
                gpu_info[g] = time.time() if gpu_info[g] is None else gpu_info[g]
            else:
                gpu_info[g] = None
        bypass = False if gpu_info else True
        for t in gpu_info.values():
            if t is not None and time.time() - t > args['-t']:
                bypass = True
            else:
                bypass = False
                break
        if bypass:
            print('等待 {} 秒GPU满足条件开始运行'.format(round(time.time()-start, 2)), datetime.now())
            os.system(cmd.strip())
            break
        time.sleep(1)
        
        
def show_stat(width=100):
    ret = set_gpu(return_more=True, public_net=False)
    # 整合gpu信息
    gpu_info = ['gpu_usage', 'ext_gpu_mem', 'all_gpu_mem', 'gpu_power', 'gpu_type']
    if sum(g in ret for g in gpu_info) == len(gpu_info):
        ret['gpu_usage_mem_power_type'] = []
        for i, (u, m, am, p, t) in enumerate(zip(*[ret[g] for g in gpu_info])):
            ret['gpu_usage_mem_power_type'].append((i, u, '{}/{}M'.format(am-m, am), p, t))
        for g in gpu_info:
            del ret[g]
    # 整合cpu信息
    cpu_info = ['ext_cpu', 'ext_mem', 'all_mem', 'cpu_info']
    if sum(g in ret for g in cpu_info) == len(cpu_info):
        u, m, am, t = [ret[g] for g in cpu_info]
        ret['cpu_usage_mem_num'] = [round(100 - float(u), 1), '{}/{}M'.format(am-m, am), t]
        for g in cpu_info:
            del ret[g]
    # 整合网络信息
    net_info = ['hostname', 'ip']
    if sum(g in ret for g in net_info) == len(net_info):
        ret['hostname_ip'] = [ret[g] for g in net_info]
        for g in net_info:
            del ret[g]
    ret = sorted(ret.items(), key=lambda t: t[0])
    pprint(ret, width=width)
    try:
        nvidia_htop(l=width-62, c=False, p=None, show_gpu=False)
    except:
        ...


def main():
    para = sys.argv[1:]
    if para:
        if para[0] == '--wait':  # 一个等待gpu的功能
            wait_gpus(para[1:])
            return
        elif para[0] == '--benchmark':  # 测试显卡性能
            benchmark()
            return
        elif para[0] == '--showp':  # 显示当前用户正在运行的命令(去重复)
            get_current_user_cmd()
            return
        elif re.search(r'^--show($|[= ]+[0-9]+$)', para[0]):  # 显示当前系统资源信息
            width = re.split(r'[= ]+', para[0])
            if len(width) == 2:
                show_stat(int(width[1]))
            else:
                show_stat()
            return
    # 一些转义符号复原
    for i, p in enumerate(para):
        if '\\' in p:
            para[i] = para[i].replace('\\', '\\\\')
        if '"' in p:
            para[i] = '"' + para[i].replace('"', '\\"') + '"'
        if '$' in p:
            para[i] = para[i].replace('$', '\\\\\\$')  # 因为 shell eval 所以多加入转义
    # 自动寻找 auto.sh 的位置
    auto = subprocess.getstatusoutput('py=$(which python) && echo ${py%bin*}lib/python*/site-packages/tsc_auto/auto.sh')
    # 没有报错
    if auto[0] == 0:
        auto = auto[1]
    else:
        raise NameError(str(auto) + ' 寻找auto.sh错误!')
    # 运行
    cmd = f'chmod 777 {auto} ; {auto} ' + ' '.join(para)
    os.system(cmd)


if __name__ == '__main__':
    main()
