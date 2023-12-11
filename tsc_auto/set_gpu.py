import subprocess
import os
import re
import sys
import socket
import platform
from pprint import pprint
import json
import traceback


# 适用于linux
# 简单导入 set_gpu 的一种方式:
# with open(os.environ['HOME']+'/git/mycode/tanshicheng/ad_set_gpu.py', 'r', encoding='utf-8') as r:
#     exec(r.read())
# 原文中设置显卡的地方可以避免冲突:
# if not 'CUDA_VISIBLE_DEVICES' in os.environ:
#     os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

def get_public_net(analysis=True):
    """
    从不同网站获取公网ip等信息
    :param analysis: bool; 是否深入解析不同网站返回的结果, 可能网站返回形式变化导致解析错误
    :return: dict
    """
    re_ip = re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')  # 匹配ip的正则
    def have_ip_f(url):  # 传入可以 curl 的域名
        s = subprocess.getstatusoutput('curl -s --connect-timeout 3 -m 3 ' + url)[1]
        s = s if re_ip.search(s) else '{}'
        s = re.sub(r'[\r\n]+', r'\n', s).strip()
        try:
            s = json.loads(s)
        except:
            ...
        if analysis:  # 深度分析
            try:
                if url == 'myip.ipip.net':
                    s = {
                        'ip': re_ip.search(s).group(), 
                        'from': re.sub(r'[\s:：|]+', ' ', re.search('(?<=来自于).+', s).group()).strip(),
                    }
                elif url == 'ipinfo.io':
                    del s['readme']
                elif url == 'cip.cc':
                    s = {
                        'ip': re_ip.search(s).group(), 
                        'from': re.sub(r'[\s:：|]+', ' ', re.search('(?<=地址).+', s.replace('\n运营商', '')).group()).strip(),
                        'from2': re.sub(r'[\s:：|]+', ' ', re.search('(?<=数据二).+', s).group()).strip(),
                        'from3': re.sub(r'[\s:：|]+', ' ', re.search('(?<=数据三).+', s).group()).strip(),
                    }
            except:
                # traceback.print_exc()
                ...
        return s
    public_net = {  # 通过 curl 获取
        'ipip': have_ip_f('myip.ipip.net'),
        'cip': have_ip_f('cip.cc'),
        'ipinfo': have_ip_f('ipinfo.io'),
    }
    return public_net


def set_gpu(showAllGpu=False, return_more=False, public_net=False):
    """
    指定最小显存占用GPU
    :param showAllGpu: bool; 是否显示所有gpu的状态
    :param return_more: bool; 是否返回更多信息, 将以dict形式返回, 选择这个将不输出信息和设置显卡
    :param public_net: bool; 是否读取返回公网ip等信息, 需要 return_more=True
    :return:
    """
    gpu, ext_gpu_mem = -1, -1
    try:
        ext_mem = subprocess.check_output('free -m', shell=True) \
            .decode(encoding='utf8', errors='ignore') \
            .split('\n')[1].strip()
        all_mem = int(re.split(r'\s+', ext_mem)[1])
        ext_mem = int(re.split(r'\s+', ext_mem)[6])  # 不是free而是available
    except:
        ext_mem, all_mem = -1, -1
    try:
        # check_output 防止 UnicodeDecodeError
        ext_cpu = subprocess.check_output('top -bn 1 | head -n 10', shell=True) \
            .decode(encoding='utf8', errors='ignore')
        ext_cpu = re.findall(r'(?<=,)[ \d.]+?(?=id,)', ext_cpu)[0].strip()
    except:
        ext_cpu = ''
    try:
        cpu_type = subprocess.getstatusoutput('cat /proc/cpuinfo | grep name | cut -f2 -d: |uniq -c')[1].split('\n')
        cpu_type = [i.strip() for i in cpu_type]
        cpu_num = int(subprocess.getstatusoutput('cat /proc/cpuinfo |grep "physical id"|sort|uniq|wc -l')[1])
        cpu_cores = int(
            subprocess.getstatusoutput('cat /proc/cpuinfo |grep "cpu cores"|uniq')[1].split('\n')[0].split(':')[1])
        core_pro = int(subprocess.getstatusoutput('cat /proc/cpuinfo |grep "processor"|wc -l')[1])
        core_pro = int(core_pro / cpu_num / cpu_cores)
    except:
        cpu_num, cpu_cores, core_pro, cpu_type = 0, 0, 0, []
    (status, result) = subprocess.getstatusoutput('nvidia-smi')
    i_m = []
    all_gpu_mem = []
    power = 'W'
    w = []
    w_re = r'(?<=\s)[\s\d]+?W\s+?/[\s\d]+?W(?=\s)'  # 提取功率
    gpu_usage = []
    gpu_type = []
    if status == 0:
        if showAllGpu:
            print(result)
        r = re.findall(r'(?<=[|/])[\s\d]+?(?=MiB)', result)
        all_gpu_mem = [int(r[i + 1]) for i in range(0, len(r), 2)]
        r = [int(r[i + 1]) - int(r[i]) for i in range(0, len(r), 2)]
        w = [i.replace(' ', '') for i in re.findall(w_re, result)]
        gpu_usage = [int(re.search(r'(?<= )[0-9.]+?(?=%)', i.split('MiB', 1)[1]).group())
                     for i in result.split('\n') if re.search(w_re, i)]
        i_m = [(i, j) for i, j in enumerate(r)]
        if i_m:
            i_m_1 = sorted(i_m, key=lambda t: t[1])[-1]
            gpu = i_m_1[0]
            ext_gpu_mem = i_m_1[1]
        if w:
            power = w[gpu]
        # 每个gpu型号获取
        # result_L = result.split('\n')  # 这种方式获取不全
        # for i in range(1, len(result_L)):
        #     if re.search(r'\|\s*?\d+?MiB / \d+?MiB \|', result_L[i]):
        #         gpu_type.append(re.split(r' [ ]+', result_L[i - 1])[2])
        gpu_type = subprocess.getstatusoutput('nvidia-smi -L')[1].split('\n')
        gpu_type = [re.search(r'(?<=: )[^(\r\n]+', i).group().strip() for i in gpu_type]
    hostname = subprocess.getstatusoutput('hostname')[1]
    try:
        ip = socket.gethostbyname(hostname)
    except:
        # hostname -I | awk '{print $1}'
        ip = subprocess.getstatusoutput('hostname -I')[1].split(' ')[0]
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        ...
    if return_more:
        n = int(cpu_num * cpu_cores * core_pro)
        ret = {
            'hostname': hostname,  # str, 主机名
            'ip': ip,  # str; 主机局域网ip
            'gpu_power': w,  # list; 每张gpu的使用功率和上限功率
            'gpu_usage': gpu_usage,  # list; 每张gpu的使用率
            'ext_gpu_mem': [i[1] for i in i_m],  # list; 每张gpu的剩余显存数量, 单位MB
            'all_gpu_mem': all_gpu_mem,  # list; 每张gpu的总显存数量, 单位MB
            'ext_cpu': ext_cpu,  # str; 剩余的cpu使用率, 单位百分比
            'ext_mem': ext_mem,  # int; 剩余内存数量, 单位MB
            'all_mem': all_mem,  # int; 总计内存数量, 单位MB
            'cpu_info': f"{n}:{cpu_num}-{cpu_cores}-{core_pro}",  # str; 总线程数:cpu数-每个cpu的核心数-每个核心的超线程数
            'platform': platform.platform(),  # str; 平台架构, 比如 Darwin-20.4.0-arm64-arm-64bit
            'gpu_type': gpu_type,  # list; 每个gpu的型号, 比如 NVIDIA GeForce RTX 2080 Ti
            'cpu_type': cpu_type,  # list; 每个cpu的型号, 比如 16  Intel(R) Core(TM) i9-9900K CPU @ 3.60GHz
        }
        if public_net:
            ret['public_net'] = get_public_net()
        return ret
    # 例如: tsc@192.168.6.6, 设置显卡:0(28W/260W)-0, 剩余CPU:%(1-8-2), 剩余内存:57.7GB, 剩余显存:10.8GB
    print('%s@%s, 设置显卡:%d(%s)-%d, 剩余CPU:%s%%(%d-%d-%d), 剩余内存:%.1fGB, 剩余显存:%.1fGB' %
          (hostname, ip, gpu, power, len(i_m) - 1, ext_cpu, cpu_num, cpu_cores, core_pro, ext_mem / 1024,
           ext_gpu_mem / 1024))
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu)
    return gpu  # 选择的显存最大的gpu编号


if __name__ == '__main__':
    gpu = set_gpu()
    if len(sys.argv) > 1:
        sys.exit(gpu + 1)
    else:
        ret = set_gpu(return_more=True, public_net=True)
        # pprint(ret)
        print(json.dumps(ret, ensure_ascii=False, indent=2))
