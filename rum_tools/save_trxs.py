""" 
把旧链节点所存储的数据，通过 get content api 读取 trxs 并写入到本地 json 文件

旧链需要用旧版的 fullnode sdk 即 rumpy 来交互。
"""

import json
import logging
import os
import time
from urllib.parse import urlparse

from rumpy import FullNode

logger = logging.getLogger(__name__)


def SaveNodeTrxstoFile(url, jwt, datadir):
    """把旧链全节点的所有 groups trxs 内容数据写入到 datadir 目录下的文件"""

    bot = FullNode(api_base=url, jwt_token=jwt)
    # 检查文件夹是否存在，如果不存在则创建
    if not os.path.exists(datadir):
        os.makedirs(datadir)
    # save node groups info to file
    groups = bot.api.groups()
    parsed_url = urlparse(url)
    formatted_url = "{}_{}".format(parsed_url.hostname, parsed_url.port)
    fname = os.path.join(datadir, f"groups_info_{formatted_url}.json")
    with open(fname, "w", encoding="utf-8") as f:
        f.write(json.dumps(groups, indent=1))
        logger.info("save groups info to file: %s", fname)

    def save_to_file(_trxs):
        fname = f"group_{bot.group_id}_{int(time.time())}.json"
        fname = os.path.join(datadir, fname)
        with open(fname, "w", encoding="utf-8") as f:
            f.write(json.dumps(_trxs, indent=1))
            logger.info("%s trxs save trxs to file: %s", len(_trxs), fname)

    for group_id in bot.api.groups_id:
        bot.group_id = group_id
        info = bot.api.group_info()
        logger.info("group %s info: %s", group_id, info)
        n = 0
        max_trxs_num = 200
        itrxs = []
        for trx in bot.api.get_group_all_contents():
            n += 1
            if n >= max_trxs_num:
                save_to_file(itrxs)
                itrxs = []
                n = 0
            itrxs.append(trx)
        save_to_file(itrxs)
