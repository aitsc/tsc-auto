# 查询空闲节点
import subprocess
import re
import sys
import random


def random_pick(weather_list, probabilities_list):
    probabilities_list = [i / sum(probabilities_list) for i in probabilities_list]
    if len(weather_list) != len(probabilities_list):
        raise ValueError("The length of two input lists are not match!")
    random_normalized_num = random.random()  # random() -> x in the interval [0, 1).
    accumulated_probability = 0.
    for item in zip(weather_list, probabilities_list):
        accumulated_probability += item[1]
        if random_normalized_num < accumulated_probability:
            return item[0]


def get(u='cpu', output=True):
    squeue = subprocess.getstatusoutput('squeue')[1].split('\n')
    sinfo = subprocess.getstatusoutput('sinfo')[1].split('\n')

    partitions = {'COMPUTE': 1, 'GPU8': 8, 'GPU2': 2, 'GPU1': 1}
    defaultCPU = 'COMPUTE'
    defaultGPU = 'GPU8'
    queue_task = 0
    task_num = 0
    otherTask_num = 0
    users = set()
    names = set()
    gpu_tasknum = {}
    cpu_tasknum = {}
    gpu_state = {}
    cpu_state = {}
    gpu_partition = {}
    cpu_partition = {}
    for line in squeue[1:]:
        line = re.split(r'\s+', line.strip())
        if len(line) <= 7:
            continue
        node = line[7]
        partition = line[1].strip('*')
        user = line[3]
        name = line[2]
        users.add(user)
        names.add(name)
        if partition == 'COMPUTE':
            u_tasknum = cpu_tasknum
            digit = '4'
        else:
            u_tasknum = gpu_tasknum
            digit = '2'
        if node == '(Priority)':
            queue_task += 1
            continue
        if partition not in partitions or node[0] == '(':
            otherTask_num += 1
            continue
        if '[' in node:
            x, y = node.split('[')
            y = y[:-1].split(',')
            n = []
            for i in y:
                if '-' in i:
                    a, b = i.split('-')
                    for j in range(int(a), int(b) + 1):
                        k = '%' + digit + 'd'
                        n.append(str(k % j).replace(' ', '0'))
                else:
                    n.append(i)
            nodes = [x + str(i) for i in n]
        else:
            nodes = [node]
        for i in nodes:
            if i in u_tasknum:
                u_tasknum[i] += 1
            else:
                u_tasknum[i] = 1
        task_num += 1
    for line in sinfo:
        line = re.split(r'\s+', line.strip())
        if len(line) <= 5:
            continue
        node = line[5]
        partition = line[0].strip('*')
        state = line[4]
        if partition == 'COMPUTE':
            u_state = cpu_state
            u_partition = cpu_partition
            digit = '4'
        else:
            u_state = gpu_state
            u_partition = gpu_partition
            digit = '2'
        if partition not in partitions:
            continue
        if '[' in node:
            x, y = node.split('[')
            y = y[:-1].split(',')
            n = []
            for i in y:
                if '-' in i:
                    a, b = i.split('-')
                    for j in range(int(a), int(b) + 1):
                        k = '%' + digit + 'd'
                        n.append(str(k % j).replace(' ', '0'))
                else:
                    n.append(i)
            nodes = [x + str(i) for i in n]
        else:
            nodes = [node]
        for i in nodes:
            u_state[i] = state
            u_partition[i] = partition

    gpuUsable_tasknum = {}
    cpuUsable_tasknum = {}
    gpuUsable_rate = {}
    cpuUsable_rate = {}
    for n, s in cpu_state.items():
        if s != 'mix' and s != 'idle':
            continue
        if n in cpu_tasknum:
            cpuUsable_tasknum[n] = cpu_tasknum[n]
            cpuUsable_rate[n] = partitions[cpu_partition[n]] / (cpu_tasknum[n] + 1)  # 用后得分
        else:
            cpuUsable_tasknum[n] = 0
            cpuUsable_rate[n] = 0
    for n, s in gpu_state.items():
        if s != 'mix' and s != 'idle':
            continue
        if n in gpu_tasknum:
            gpuUsable_tasknum[n] = gpu_tasknum[n]
            gpuUsable_rate[n] = partitions[gpu_partition[n]] / (gpu_tasknum[n] + 1)  # 用后得分
        else:
            gpuUsable_tasknum[n] = 0
            gpuUsable_rate[n] = 0
    cpuUsable_tasknum_L = sorted(cpuUsable_tasknum.items(), key=lambda t: t[1])
    gpuUsable_tasknum_L = sorted(gpuUsable_tasknum.items(), key=lambda t: t[1])
    gpuUsable_rate = sorted(gpuUsable_rate.items(), key=lambda t: t[1], reverse=True)
    cpuUsable_rate = sorted(cpuUsable_rate.items(), key=lambda t: t[1], reverse=True)
    gpus = [i for i, j in gpuUsable_rate if j > 0.5][:2]  # 任务数不能超过gpu显卡数量
    if not gpus and gpuUsable_rate:
        gpus = [gpuUsable_rate[0][0]]
    if gpuUsable_tasknum_L and gpuUsable_tasknum_L[0][1] == 0:
        gpus = [gpuUsable_tasknum_L[0][0]]
    cpus = [i for i, j in cpuUsable_rate if j > partitions['COMPUTE'] / 5][:3]  # 不超过5个任务在cpu上
    if not cpus and cpuUsable_rate:
        cpus = [cpuUsable_rate[0][0]]
    if cpuUsable_tasknum_L and cpuUsable_tasknum_L[0][1] == 0:
        cpus = [cpuUsable_tasknum_L[0][0]]
    cpu = random_pick(cpus, [i for _, i in cpuUsable_rate[:len(cpus)]])
    gpu = random_pick(gpus, [i for _, i in gpuUsable_rate[:len(gpus)]])

    if cpu:
        cpu_out = '-p %s -w %s' % (cpu_partition[cpu], cpu)
    else:
        cpu_out = '-p ' + defaultCPU
    if gpu:
        gpu_out = '-p %s -w %s' % (gpu_partition[gpu], gpu)
    else:
        gpu_out = '-p ' + defaultGPU
    if u == 'cpu':
        u = cpu
        out = cpu_out
        related = [(i, cpuUsable_tasknum[i]) for i in cpus]
    else:
        u = gpu
        out = gpu_out
        related = [(i, gpuUsable_tasknum[i]) for i in gpus]
    if output:
        print('=' * 50)
        print('排队任务数量: %d, 运行中任务数量: %d, 其他任务数量: %d, 账号总数(至少): %d, 任务名称数(至少): %d' %
              (queue_task, task_num, otherTask_num, len(users), len(names)))
        print('-' * 50)
        print('可用cpu及任务数：', cpuUsable_tasknum_L)
        print('建议cpu：', cpu_out)
        print('-' * 50)
        print('可用gpu及任务数：', gpuUsable_tasknum_L)
        print('建议gpu：', gpu_out)
        print('=' * 50)
    # else:  # 输出导致shell调用错误
    #     print('选择机器: %s, 相关机器及其作业数: %s' % (u, str(related)))
    return out


if __name__ == '__main__':
    if len(sys.argv) > 1:
        exit(get(sys.argv[1], output=False))
    else:
        get()
