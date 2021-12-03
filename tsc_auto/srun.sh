#!/bin/bash
# 超算srun调度脚本/自动配置深度学习环境变量/自动挑选CPU或显卡/自动后台日志
py=$(which python)
spy=${py%bin*}lib/python*/site-packages/tsc_auto  # 脚本所在目录绝对路径
pytorch='torch'
tensorflow='tf'

U="cpu"
G=""
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
      -c)
      U="cpu"
      shift # past argument
      ;;
      -g)
      G='--gres=gpu:1'
      shift # past argument
      ;;
      -t)
      U="gpu"
      deep=$tensorflow
      shift # past argument
      ;;
      -p)
      U="gpu"
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
      -s)
      S=true
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
  esac
done

if [ $help ]; then
  echo -e '-c\t使用cpu服务器运行, 默认'
  echo -e '-g\t加入申请GPU参数--gres=gpu:1, 如果使用cpu这项不能输入. 加入可能gpu排队, 不加入容易被中断'
  echo -e '-t\t使用gpu服务器运行, 同时配置tensorflow环境变量'
  echo -e '-p\t使用gpu服务器运行, 同时配置pytorch环境变量'
  echo -e '-a\t执行python的运行文件路径'
  echo -e '-o\t执行操作, 这个参数如果有必须是最后一个参数'
  echo -e '-l\t日志路径, 使用日志则后台运行, 只有日志则是回顾日志'
  echo -e '-s\t停止日志对应的任务, 只有-l的时候配合使用'
  echo -e '-h, --help\t查看帮助'
  echo -e '说明: 使用gpu必须在对应conda环境下执行, 深度学习框架要安装在默认路径, py和sh脚本路径和cuda路径需要适配'
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
  jobid=$(cat $log|grep '(?<=srun: job )[0-9]+(?= )' -Po|head -n1)
  echo '正在停止任务: '$jobid
  scancel $jobid
  tail -f $log
  exit 0
fi

if [ ! $P ]&&[ ! "$O" ]&&[ $log ]; then
  if [ $S ]; then
    jobid=$(cat $log|grep '(?<=srun: job )[0-9]+(?= )' -Po|head -n1)
    echo '正在停止任务: '$jobid
    scancel $jobid
  fi
  tail -f $log
  exit 0
fi

sr='srun -J xxx -u -t 12000 '$G' '$(python3 $spy/query.py ${U} 2>&1)' sh '$spy/auto.sh' -n'

if [ $deep ]; then
  if [ $deep = $tensorflow ]; then
    sr=$sr' -t'
  else
    sr=$sr' -p'
  fi
fi
if [ $P ]; then
  sr=$sr' -a '$P
fi
if [ "$O" ]; then
  sr=$sr' -o '$O
fi

#echo $sr

if [ $log ]; then
  echo '日志路径: '$(readlink -f $log)
  nohup $sr >$log 2>&1 &
else
  eval $sr
fi