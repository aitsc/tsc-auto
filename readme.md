## 介绍
- 可以自动检测 torch 和 tensorflow 版本, 并自动设置环境变量相应的 cuda, 同时自动选择占用显存最低的显卡运行.
- 可以实现自动后台运行运行并记录和查看日志/中止程序.
- 需要在 anaconda 环境下使用.

## 安装
pip install tsc-auto

## 使用方式
- 查看帮助: ta --help
- 自动选择最低显存占用显卡跑 torch 的 cnn.py 程序: ta -p -a cnn.py
- 手动选择编号0和1的显卡跑 tensorflow 的 cnn.py 程序: ta -t -d 0,1 -a cnn.py

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
