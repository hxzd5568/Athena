import os
import os.path
import random
import sys
from subprocess import run, CalledProcessError, TimeoutExpired
import time
import hashlib
import string
from pathlib import Path

log_root = "/work/Paddle/Athena/"

def get_latest_subdirectory(directory):
    paths = [path for path in Path(directory).iterdir() if path.is_dir()]
    if not paths:
        return None
    latest_subdir = max(paths, key=lambda x: x.stat().st_mtime)
    return str(latest_subdir)

def cal_successful_rate(log_dir):
    ap_num = 0
    names = []
    files = os.listdir(log_dir)
    sum_num = len(files) - 1 # there is a total log in the dir
    for file_name in files:
        if file_name.endswith('.txt') and file_name.startswith('log'):
            fd = os.popen(f"cat {log_dir}/{file_name} |  grep '\"pd_op.ap' | wc -l")
            output = fd.read()
            output = output.strip()
            file_name_short = file_name.split('_')[-2]
            fusion_num = int(output[0])
            if fusion_num >= 1:
                ap_num += 1
                names.append(file_name_short)
                print(f'{fusion_num} AP fusion found in {file_name_short}')
            else:
                # cmd = ["mv", f"{log_dir}/{file_name}", f"{log_dir}/y{file_name}"]
                print(f'No AP fusion found in {file_name_short}')
                pass
            fd = os.popen(f"cat {log_dir}/{file_name} |  grep '\"pd_op.matmul' | wc -l")
            output = fd.read()
            output = output.strip()
            file_name_short = file_name.split('_')[-2]
            fusion_num = int(output[0])
            if fusion_num >= 1:
                pass
            else:
                sum_num -= 1
    print('total: ', sum_num, 'containing ap fusion: ', ap_num, 'ap coverage rate: ', ap_num / float(sum_num))
    print('ap files name: ', names)

if __name__ == "__main__":
    if not os.path.exists(log_root):
        print("<Path Error> : Please Initialize the `log_root` variable with\
            a existed log directory.")
        exit(0)
    latest_subdir = get_latest_subdirectory(log_root + "tests/ap/ap_matmul_graphs/")
    print("latest_subdir: ", latest_subdir)
    cal_successful_rate(latest_subdir)
