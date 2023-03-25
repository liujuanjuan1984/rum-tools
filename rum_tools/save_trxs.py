""" 
把旧链节点所存储的数据，通过 get content api 读取 trxs 并写入到本地 json 文件

旧链需要用旧版的 fullnode sdk 即 rumpy 来交互。
"""

import json
import logging
import os
import time
from urllib.parse import urlparse

from officy import Dir, JsonFile
from rumpy import FullNode

logger = logging.getLogger(__name__)


def save_to_file(bot, datadir, trxs):
    fname = f"group_{bot.group_id}_{int(time.time())}.json"
    fname = os.path.join(datadir, fname)
    with open(fname, "w", encoding="utf-8") as f:
        f.write(json.dumps(trxs, indent=1))
        logger.info("%s trxs save trxs to file: %s", len(trxs), fname)


def get_progress(bot, datadir, group_id):
    """从 datadir 目录下的文件中读取进度信息"""
    jsonfiles = Dir(datadir).search_files_by_types("json")
    groupfiles = [f for f in jsonfiles if group_id in f]
    if not groupfiles:
        return None
    f = max(groupfiles)
    trxs = JsonFile(f).read(f)
    return trxs[-1]["TrxId"]


def SaveNodeTrxstoFile(url, jwt, datadir, group_id=None, progress: dict = None):
    """
    把旧链全节点的所有 groups trxs 内容数据写入到 datadir 目录下的文件
    progress = {group_id: trx_id}
    """

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

    if group_id:
        groups = [group_id]
    else:
        groups = bot.api.groups_id

    progress = progress or {}

    for group_id in groups:
        starttrx = progress.get(group_id) or get_progress(bot, datadir, group_id)
        progress[group_id] = starttrx
        bot.group_id = group_id
        info = bot.api.group_info()
        logger.info("group %s info: %s", group_id, info)
        n = 0
        max_trxs_num = 200
        itrxs = []
        for trx in bot.api.get_group_all_contents(trx_id=starttrx):
            n += 1
            if n >= max_trxs_num:
                save_to_file(bot, datadir, itrxs)
                progress[group_id] = itrxs[-1]["TrxId"]
                itrxs = []
                n = 0
            itrxs.append(trx)

        if len(itrxs) > 0:
            save_to_file(bot, datadir, itrxs)
            progress[group_id] = itrxs[-1]["TrxId"]

    print(progress)
    return progress
