'''
### 暂时无用的用于超算的文件
- info.py
- query.py
- srun.sh
'''
from .set_gpu import set_gpu, get_public_net
from .kill import get_nvidia_processes, get_ps_processes, get_user_processes, kill_processes
from .notice import send_wechat, get_time_diff, explain_exit_code