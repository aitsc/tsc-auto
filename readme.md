## 安装
pip install tsc-auto

## 使用方式
ta --help

## cuda的位置必须在主目录 (可以使用 ln -s 软链接)
- ...
- ~/cuda/8.0
- ...
- ~/cuda/11.3
- ...

# cuda 和 cudnn 拷贝的例子
- cd ~/cuda
- mv /usr/local/cuda-11.0/ 11.0
- cp cudnn-v8.2.0.53/include/cudnn.h 11.0/include/
- cp cudnn-v8.2.0.53/lib64/libcudnn* 11.0/lib64
- chmod a+r 11.0/include/cudnn.h 11.0/lib64/libcudnn*

# 暂时无用的用于超算的文件
- info.py
- query.py
- srun.sh