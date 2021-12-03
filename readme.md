## 安装
pip install tsc-auto

## 使用方式
- 查看帮助: ta --help
- 自动选择最低显存占用显卡跑 torch 的 cnn.py 程序: ta -p -a cnn.py
- 手动选择编号0和1的显卡跑 tensorflow 的 cnn.py 程序: ta -t -d 0,1 -a cnn.py

## cuda的位置必须在主目录 (可以使用 ln -s 软链接)
- ...
- ~/cuda/8.0
- ...
- ~/cuda/11.3
- ...

## cuda 和 cudnn 拷贝的例子
- cd ~/cuda
- mv /usr/local/cuda-11.0/ 11.0
- cp cudnn-v8.2.0.53/include/cudnn.h 11.0/include/
- cp cudnn-v8.2.0.53/lib64/libcudnn* 11.0/lib64
- chmod a+r 11.0/include/cudnn.h 11.0/lib64/libcudnn*

## 下载处理好的cuda
- 链接: https://pan.baidu.com/s/1tXzED_8GZjJzm_SFzMTbKA 提取码: 3edj

### 暂时无用的用于超算的文件
- info.py
- query.py
- srun.sh