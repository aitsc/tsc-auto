import os
import sys
import subprocess


def main():
    para = sys.argv[1:]
    # 自动寻找 auto.sh 的位置
    auto = subprocess.getstatusoutput('py=$(which python) && echo ${py%bin*}lib/python*/site-packages/tsc_auto/auto.sh')
    # 没有报错
    if auto[0] == 0:
        auto = auto[1]
    else:
        raise NameError(str(auto) + ' 寻找auto.sh错误!')
    # 运行
    os.system(f'chmod 777 {auto} && {auto} ' + ' '.join(para))


if __name__ == '__main__':
    main()
