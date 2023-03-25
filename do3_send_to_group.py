"""
把指定目录下的旧共识的 group trxs 发送到指定的 rum group
"""

import logging

from rum_tools import SendToGroup

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# 旧链自己用到的密钥，从 search_keys 产生
keysfile = "./RUM-DATA-KEYS.json"

# 本地保存旧链 trxs 的目录，从 save_trxs 产生
datadir = "./groups_trxs_data"

# 新链的 seed
seed = "rum://seed?v=1&e=0&n=0&c=...cCmgKgwvD7n0e9NCjM4"


basefile = "./sent_progress.json"

groups_id = [
    "bd119dd3-081b-4db6-9d9b-e19e3d6b387e",  # 去中心推特
    "3bb7a3be-d145-44af-94cf-e64b992ff8f0",  # 去中心微博
]

for group_id in groups_id:
    if group_id not in basefile:
        progressfile = basefile.replace(".json", "_" + group_id + ".json")
    else:
        progressfile = basefile
    SendToGroup(keysfile, datadir, group_id, seed, progressfile)
