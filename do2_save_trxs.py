"""
连接运行中的旧链节点，读取 trxs 并写入到本地 json 文件
旧链需提供 chain jwt token 并用 rumpy 来建立连接。
"""

import logging

from rum_tools import SaveTrxs

logging.basicConfig(level=logging.DEBUG)

jwt = "eyJhbGciOiJIUzI...r2L04"

url = "http://123.45.123.13:60123"
datadir = "/tmp/groups_trxs_data"

# 指定 group_id 就只处理单个 group，否则处理全节点的所有 groups
# 建议按 group 逐个处理
group_id = None

SaveTrxs(url, jwt, datadir, group_id)
