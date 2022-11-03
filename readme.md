# 安装
pip install tsc-auto

# 功能1: ta
## 介绍
- 可以自动检测 torch 和 tensorflow 版本, 并自动设置环境变量相应的 cuda, 同时自动选择占用显存最低的显卡运行.
- 可以实现自动后台运行运行并记录和查看日志/中止程序.
- 需要在 anaconda 环境下使用.
- 在程序终止时可以自动发送微信通知.

## 使用方式
- 查看帮助: ta --help
- 自动选择最低显存占用显卡跑 torch 的 cnn.py 程序: ta -p -a cnn.py
- 手动选择编号0和1的显卡跑 tensorflow 的 cnn.py 程序: ta -t -d 0,1 -a cnn.py
- 发送通知步骤（借助 [pushplus](https://pushplus.plus) 实现)
  1. 微信登录: https://pushplus.plus/login.html
  2. 激活微信公众号, 接收文章推送, 关闭消息免打扰
  3. 获取token: https://pushplus.plus/push1.html
  4. 测试: ta -x 你的token -o echo 成功
  5. 注意: 运行机需要联网; 不能使用ta自带的后台运行方式(可以手动nohup); 频率太高可能[封号](https://www.pushplus.plus/doc/help/limit.html#接口限制)/[封ip](https://www.pushplus.plus/doc/help/ip.html)
- ta --benchmark 可测试显卡性能
- ta --wait -c=0.1 -m=0.8 -t=10 -g=1,2 python test.py 可等待显卡1,2满足空闲条件(至少剩余10%gpu使用率+至少剩余80%显存+持续10秒钟)后再执行后面的命令
- ta --showp 可显示当前用户的所有运行程序(去重复)命令
- ta --show 显示当前系统资源信息, 例如:
```python
[('all_mem', 96413),
 ('cpu_info', '16:1-8-2'),
 ('cpu_type', ['16  Intel(R) Core(TM) i9-9900K CPU @ 3.60GHz']),
 ('ext_cpu', '97.5'),
 ('ext_mem', 69614),
 ('gpu_usage_mem_power_type', [(0, 0, '5093/11019', '1W/260W', 'NVIDIA GeForce RTX 2080 Ti')]),
 ('hostname', 'test'),
 ('ip', '192.168.2.2'),
 ('platform', 'Linux-5.11.0-40-generic-x86_64-with-glibc2.31')]
```

## cuda的位置默认在用户主目录 (可以使用 ln -s 软链接)
- ...
- ~/cuda/8.0
- ...
- ~/cuda/11.3
- ...

## 下载处理好的cuda
- 链接: https://pan.baidu.com/s/1tXzED_8GZjJzm_SFzMTbKA 提取码: 3edj

## 如果自行安装 cuda 和 cudnn, 需要处理的方式
- cd ~/cuda
- mv /usr/local/cuda-11.0/ 11.0
- cp cudnn-v8.2.0.53/include/cudnn.h 11.0/include/
- cp cudnn-v8.2.0.53/lib64/libcudnn* 11.0/lib64
- chmod a+r 11.0/include/cudnn.h 11.0/lib64/libcudnn*

# 功能2: tkill
## 介绍
- 用于限制linux系统的cpu/gpu资源使用, 例如可以针对以下内容进行限制:
```python
{
    's': 10,  # 多少秒检测一次
    'cpu_core_u': 2147483647,  # 一个用户-最多CPU占用(百分比,如100表示占满1个超线程)
    'gpu_card_u': 2,  # 一个用户-最多显卡(张)
    'gpu_mem_u': 24,  # 一个用户-最大显存(GB)
    'gpu_card': 2,  # 单进程-最多显卡(张)
    'gpu_mem': 21000,  # 单进程-最大显存(MB)
    'gpu_day': 15,  # 单进程-最长显卡占用时间(天)
    'cpu_day': 15,  # 单进程-最长cpu占用时间(天)
    'cpu_day_core_limit': 80,  # CPU占用百分比超过此值的进程才会使 cpu_day 配置生效
    'ignore_u': {'999',},  # 忽略的用户, 默认会包含 /etc/passwd 中路径不含有 /home/ 的用户
    'include_u': {'example_user',},  # 不可忽略的用户, 优先级高于 ignore_u
    # 针对每个特殊配置设置用户，没写的默认使用上述设置，越靠list后面的优先级越高会覆盖前面一样的用户配置
    'conf': [
        {  # 一组配置和对应的用户
            'gpu_mem': 24000,
            'conf_u': {'tsc'},  # 使用这组配置的用户
        },
    ],
    # 针对每个用户的额外配置, 没写的默认使用上述设置, 优先级最高
    'user': {
        'example_user': {
            'gpu_mem_u': 41,
            'gpu_card_u': 3,
        },
    },
}
```
- 退出某用户在显卡中的进程, 防止程序结束而显存没有释放: tkill --knp username

## 使用方式
- 查看帮助: tkill -h
- 首先, 运行 tkill -c 'kill.config' -t 再终止程序(ctrl+c), 用于生成默认配置文件
- 然后, 修改配置文件的内容
- 最后, 运行 tkill -c 'kill.config' 开启限制程序

# 功能3: ressh
## 介绍
- 用于在断网后自动重新连接ssh,也可以在一行命令行中直接输入密码登录

## 使用方式
- 查看帮助: ressh -h
- 登录: ressh user@ip -p port
- 登录后自动输入密码并自动进入tmux: ressh user@ip -p port --tmux --password=你的密码


# 功能4: tp
## 介绍
- 服务器代理

## 使用方式
- 服务器和客户端都需要安装包: pip install tsc-auto
- 本地打开http代理开放到端口 7890, 可借助 [clash](https://github.com/Fndroid/clash_for_windows_pkg/releases)
- 登录服务器: ressh ssh参数 --tp
- 登录后使用代理: tp curl google.com
