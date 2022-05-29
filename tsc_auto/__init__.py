'''
### 暂时无用的用于超算的文件
- info.py
- query.py
- srun.sh
'''
from .set_gpu import set_gpu
from .kill import get_nvidia_processes, get_ps_processes, get_user_processes, kill_processes
from .notice import send_wechat