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
from quorum_fullnode_py import FullNode as NewFullNode
from rumpy import FullNode as OldFullNode

logger = logging.getLogger(__name__)


def save_to_file(bot, datadir, trxs):
    fname = f"group_{bot.group_id}_{int(time.time())}.json"
    fname = os.path.join(datadir, fname)
    with open(fname, "w", encoding="utf-8") as f:
        f.write(json.dumps(trxs, indent=1))
        logger.info("%s trxs save trxs to file: %s", len(trxs), fname)


def get_progress(datadir, group_id):
    """从 datadir 目录下的文件中读取进度信息"""
    jsonfiles = Dir(datadir).search_files_by_types("json")
    groupfiles = [f for f in jsonfiles if group_id in f]
    if not groupfiles:
        return None
    f = max(groupfiles)
    trxs = JsonFile(f).read(f)
    return trxs[-1]["TrxId"]


def get_all_trxs_from_new_chain(
    client, group_id, starttrx, timestamp="1679283276688999936"
):
    """从新链中读取所有 trxs"""
    client.group_id = group_id
    while True:
        trxs = client.api.get_content(starttrx=starttrx, num=200)
        if not trxs:
            break
        # 1679987917118919837
        for trx in trxs:
            starttrx = trxs[-1]["TrxId"]
            # 设定一个时间点，只读取这个时间点之后的 trxs
            if str(trx["TimeStamp"])[:16] <= str(timestamp)[:16]:
                continue
            yield trx


def SaveNodeTrxstoFile(
    url, jwt, datadir, group_id=None, progress: dict = None, client_type="old"
):
    """
    把旧链全节点的所有 groups trxs 内容数据写入到 datadir 目录下的文件
    progress = {group_id: trx_id}
    """
    if client_type == "old":
        bot = OldFullNode(api_base=url, jwt_token=jwt)
    else:
        bot = NewFullNode(api_base=url, jwt_token=jwt)
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
        if group_id not in bot.api.groups_id:
            logger.info("group %s not exist", group_id)
            continue
        starttrx = progress.get(group_id) or get_progress(datadir, group_id)
        progress[group_id] = starttrx
        bot.group_id = group_id
        info = bot.api.group_info()
        logger.info("group info: %s", info)
        n = 0
        max_trxs_num = 200
        itrxs = []
        if client_type == "old":
            all_trxs = bot.api.get_group_all_contents(trx_id=starttrx)
        else:
            all_trxs = get_all_trxs_from_new_chain(bot, group_id, starttrx)
        for trx in all_trxs:
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

    logger.info("progress: %s", progress)
    return progress
