"""
从目标文件夹中搜寻密钥文件，并用提供的密码列表来还原出私钥，
生成 group_id 到 密钥 的映射，写入文件保存
"""

import os

from rum_tools import SearchKeys

target_folder = "./rum"

rltfile = "./m1_keys.json"
pwds = ["123456", "helloworld"]

SearchKeys(target_folder, pwds, rltfile)
