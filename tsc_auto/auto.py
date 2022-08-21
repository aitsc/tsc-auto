import os
import sys
import subprocess
import re
import time
from datetime import datetime
try:
    from set_gpu import set_gpu
except:
    from .set_gpu import set_gpu


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
    }
    i = 0
    for p in para_L:
        if '=' in p and p.split('=')[0] in args:
            args[p.split('=')[0]] = float(p.split('=')[1])
        else:
            break
        i += 1
    para_L = para_L[i:]
    # 获取gpus
    gpus = []
    cmd = ' ' + ' '.join(para_L) + ' '
    gpus_re = [
        r'(?<= --include=localhost:)\d[\d,]*(?= )',  # deepspeed
        r'(?<= CUDA_VISIBLE_DEVICES=)\d[\d,]*(?= )',
    ]
    for r in gpus_re:
        ret = re.search(r, cmd)
        if ret:
            gpus = [int(i) for i in ret.group().strip(',').split(',')]
            break
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
            print('等待 {} 秒GPU满足条件开始运行'.format(round(time.time()-start,2)), datetime.now())
            os.system(cmd.strip())
            break
        time.sleep(1)


def main():
    para = sys.argv[1:]
    if para:
        if para[0] == '--wait':  # 一个等待gpu的功能
            wait_gpus(para[1:])
            return
        elif para[0] == '--benchmark':  # 测试显卡性能
            benchmark()
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
    cmd = f'chmod 777 {auto} && {auto} ' + ' '.join(para)
    os.system(cmd)


if __name__ == '__main__':
    main()
