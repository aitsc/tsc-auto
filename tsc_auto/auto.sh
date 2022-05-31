#!/bin/bash
# 自动配置深度学习环境变量/自动挑选显卡/自动后台日志
py=$(which python)
spy=${py%bin*}lib/python*/site-packages/tsc_auto/set_gpu.py  # set_gpu.py脚本所在目录绝对路径
npy=${py%bin*}lib/python*/site-packages/tsc_auto/notice.py  # notice.py脚本所在目录绝对路径
cudamp=~  # cuda 主目录
# function 与mac不兼容
function version_gt() { test "$(echo "$@" | tr " " "\n" | sort -V | head -n 1)" != "$1"; }
function version_le() { test "$(echo "$@" | tr " " "\n" | sort -V | head -n 1)" == "$1"; }
function version_lt() { test "$(echo "$@" | tr " " "\n" | sort -rV | head -n 1)" != "$1"; }
function version_ge() { test "$(echo "$@" | tr " " "\n" | sort -rV | head -n 1)" == "$1"; }
function isexist()  # 判断一个字符串是否在另一个字符串中
{
    source_str=$1
    test_str=$2
    strings=$(echo $source_str | sed 's/:/ /g')
    for str in $strings
    do
        if [ $test_str = $str ]; then
            return 0
        fi
    done
    return 1
}
pytorch='torch'
tensorflow='tf'

while [[ $# -gt 0 ]]; do
  key="$1"
  have_para=true
  case $key in
      -m)
      cudamp="$2"
      shift # past argument
      shift # past value
      ;;
      -c)
      deep="$2"  # 自定义cuda版本号
      shift # past argument
      shift # past value
      ;;
      -d)
      device="$2"
      shift # past argument
      shift # past value
      ;;
      -t)
      deep=$tensorflow
      shift # past argument
      ;;
      -p)
      deep=$pytorch
      shift # past argument
      ;;
      -a)
      P="$2"  # python执行文件
      if [[ ! -f $P ]]; then
        echo '-a 参数错误, 文件不存在!'
        exit 1
      fi
      shift # past argument
      shift # past value
      ;;
      -o)
      shift
      O="$*"  # 执行后面的操作
      if [[ $O =~ ^\-[a-z-](help)? ]]; then
        echo '-o 参数错误, 不能以-开头!'
        exit 1
      fi
      shift $#
      ;;
      -l)
      log="$2"
      if [[ $log =~ ^\-[a-z-](help)? ]]; then
        echo '-l 参数错误, 不能以-开头!'
        exit 1
      fi
      shift # past argument
      shift # past value
      ;;
      -x)
      notice_token="$2"
      shift # past argument
      shift # past value
      ;;
      -s)
      S=true
      shift # past argument
      ;;
      -n)
      N=true
      shift # past argument
      ;;
      -h)
      help=true
      shift # past argument
      ;;
      --help)
      help=true
      shift # past argument
      ;;
      --stat)
      python3 $spy
      exit 0
      ;;
      *)  # 其他情况
      shift # past argument
      ;;
  esac
done

if [ $help ]||[ ! $have_para ]; then
  echo -e '注意: 使用gpu必须在对应conda环境下执行, 深度学习框架要安装在默认路径, 注意cuda目录'
  echo -e '-c VERSION\t自定义cuda版本号, 比如参数为 11.1, 可选'
  echo -e '-t\t\t配置tensorflow环境变量, 可选'
  echo -e '-p\t\t配置pytorch环境变量, 可选'
  echo -e '-a PY_FILE\t执行python的运行文件路径, 文件后不能增加参数, 要参数可以使用 -o python ...'
  echo -e '-o COMMAND\t执行操作, 这个参数如果有必须是最后一个参数'
  echo -e '-l LOG_FILE\t日志路径, 使用日志则后台运行, 只有该参数则是查看日志'
  echo -e '-s\t\t停止日志对应的进程, 只有-l存在的时候配合使用'
  echo -e '-n\t\t不自动指定gpu编号设备, 防止和其他指定调度程序冲突'
  echo -e '-d DEVICES\t指定gpu编号设备, 即设置CUDA_VISIBLE_DEVICES,优先级在-n之上,不能有空格'
  echo -e '-m CUDA_PATH\t指定cuda整体所在目录, 默认是用户主目录~, 从而形成 ~/cuda/11.1 等'
  echo -e '-x token\t运行结束通过 https://pushplus.plus 发微信通知(-l不支持), 运行机需联网'
  echo -e '--stat\t\t不运行程序, 只显示资源统计结果'
  echo -e '-h, --help\t查看帮助'
  echo -e '\t详细说明: https://github.com/aitsc/tsc-auto'
  echo -e '\tAuthor by tanshicheng 2022.05.29'
  exit 0
fi

if [ ! $P ]&&[ ! "$O" ]&&[ ! $log ]; then
  echo '至少需要python文件路径(-a)或执行操作(-o)或日志路径(-l)!'
  echo -e '--help\t查看帮助'
  exit 1
fi

if [ $P ]&&[ "$O" ]; then
  echo 'python文件路径(-a)和执行操作(-o)不能同时使用!'
  echo -e '--help\t查看帮助'
  exit 1
fi

if [ $log ]&&[ $S ]; then  # 输出日志
  jobid=$(cat $log|grep '(?<=进程ID: )[0-9]+(?=;;)' -Po|head -n1)
  kill -9 $jobid
  tail -f $log
  exit 0
fi

if [ ! $P ]&&[ ! "$O" ]&&[ $log ]; then  # 输出日志
  if [ $S ]; then
    jobid=$(cat $log|grep '(?<=进程ID: )[0-9]+(?=;;)' -Po|head -n1)
    kill -9 $jobid
  fi
  tail -f $log
  exit 0
fi

if [ $P ]; then  # python
  run='python -u '$P
fi
if [ "$O" ]; then  # 其他操作
  run="$O"
fi
if [ $log ]; then  # 后台运行
  echo ''>$log
  run='nohup '$run' >>'$log' 2>&1 &'
fi

if [ $deep ]; then  # 配置环境变量
  # ls ${$(which python)%bin*}lib/python*/site-packages | grep '(tensorflow|torch)(_gpu)?-' -P | head -n1
  if [ $deep = $tensorflow ]; then
    tf=$(ls ${py%bin*}lib/python*/site-packages | grep '(?<=tensorflow)(_gpu)?-[0-9.]+[0-9]' -Po | head -n1)
    tf=${tf#*-}
    if [ ! "$tf" ]; then  # ""是怕空格
      echo '未发现tensorflow!'
    fi
    if version_ge $tf '2.5'; then
      cuda='11.2'
    elif version_ge $tf '2.4'; then
      cuda='11.0'
    elif version_ge $tf '2.1'; then
      cuda='10.1'
    elif version_ge $tf '1.13'; then
      cuda='10.0'
    elif version_ge $tf '1.5'; then
      cuda='9.0'
    else
      cuda='8.0'
    fi
  elif [ $deep = $pytorch ]; then
    torch=$(ls ${py%bin*}lib/python*/site-packages | grep '(?<=torch)-[0-9.]+[0-9]' -Po | head -n1)
    torch=${torch#*-}
    torch=${torch#+*}
    if [ ! "$torch" ]; then  # ""是怕空格
      echo '未发现pytorch!'
    fi
    if version_ge $torch '1.8'; then
      cuda='11.1'
    elif version_ge $torch '1.5'; then
      cuda='10.1'
    elif version_ge $torch '1.2'; then
      cuda='10.0'
    else
      cuda='9.0'
    fi
  else
    cuda=$deep
  fi

  cudap=$cudamp/cuda/$cuda/lib64:$cudamp/cuda/$cuda/extras/CUPTI/lib64  # cuda 路径根据需要修改
  export LD_LIBRARY_PATH=${py%bin*}lib:$cudap  # cuda 路径根据需要修改
  if !(isexist $PATH $cudamp/cuda/$cuda/bin); then
    export PATH=$cudamp/cuda/$cuda/bin:$PATH  # >=tf2.3 ptxas 所需
  fi
  export XLA_FLAGS=--xla_gpu_cuda_data_dir=$cudamp/cuda/$cuda  # XLA libdevice.10.bc 所需, 路径不能有~, 可以是$HOME

#  if [ $cuda == '10.2' ]; then
#      echo $cudap
#  elif [ $cuda == '10.1' ]; then
#  	echo $cudap
#  elif [ $cuda == '10.0' ]; then
#  	echo $cudap
#  elif [ $cuda == '9.0' ]; then
#  	echo $cudap
#  else
#  	echo $cudap
#  fi
fi

if [ $device ]; then
  python3 $spy -o 2>&1
  export CUDA_VISIBLE_DEVICES=$device
elif [ ! $N ]; then  # 指定GPU
  python3 $spy -o 2>&1
  export CUDA_VISIBLE_DEVICES=$[$?-1]
else
  python3 $spy -o 2>&1
fi

echo run=$run
echo LD_LIBRARY_PATH=$LD_LIBRARY_PATH
echo CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES
echo PATH=$PATH
echo XLA_FLAGS=$XLA_FLAGS
echo

start_time=`date '+%Y-%m-%d %H:%M:%S.%N'|cut -c 1-26`
eval $run
exit_state=$?
end_time=`date '+%Y-%m-%d %H:%M:%S.%N'|cut -c 1-26`

if [ $log ]; then  # 输出日志
  echo '进程ID: '$!';;' >> $log
  echo '日志路径: '$(readlink -f $log)
  tail -f $log
  exit 0
else
  if [ "$notice_token" ]; then  # 结束通知
    echo
    echo send notification ...
    # npy="./notice.py"  # 调试
    echo $run | python3 $npy -t "$notice_token" -d "$exit_state" -s "$start_time" -e "$end_time"
  fi
fi
