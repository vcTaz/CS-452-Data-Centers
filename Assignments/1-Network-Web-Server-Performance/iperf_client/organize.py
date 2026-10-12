import re
import os
import shutil

src = "./"

dirs = {}
for i in range(100, 1000 + 1, 100):
    os.makedirs(f"iperf_{i}", exist_ok=True)
    dirs[i] = f"iperf_{i}"

for file in os.listdir():
    src_path = os.path.join(src, file)
    if not os.path.isfile(src_path):
        continue

    dest = "./"
    match = re.search(r'\d+', file)
    if match:
        dest = dest + str(dirs[int(match.group())])
        
    dest_path = os.path.join(dest, file)
    shutil.move(src_path, dest_path)
