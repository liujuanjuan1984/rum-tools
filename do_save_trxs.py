"""
连接运行中的旧链节点，读取 trxs 并写入到本地 json 文件
旧链需提供 chain jwt token 并用 rumpy 来建立连接。
"""

from rum_tools import SaveTrxs

jwt = "eyJhbGciOiJIUzI...r2L04"

url = "http://123.45.123.13:60123"
datadir = "/tmp/groups_trxs_data"

SaveTrxs(url, jwt, datadir)
