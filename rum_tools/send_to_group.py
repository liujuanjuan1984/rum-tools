"""
把旧链的 trx 转换成新链的 trx 并发送到指令 group
"""

import logging
import time

from officy import Dir, JsonFile
from quorum_data_py import converter
from quorum_mininode_py import MiniNode

logger = logging.getLogger(__name__)


def get_pvtkeys(keysfile, group_id):
    """从 keysfile 中提取 group_id 对应的私钥"""
    data = JsonFile(keysfile).read()
    pvtkeys = {}
    for key in data[group_id]:
        if key["pubkey"]:
            pvtkeys[key["pubkey"]] = key["pvtkey"]
    return pvtkeys


def get_trxs_from_local_files(datadir, group_id, pubkey):
    """从本地文件中读取 group_id 对应的 trxs"""
    for afile in Dir(datadir).search_files_by_types(".json"):
        if group_id in afile:
            trxs = JsonFile(afile).read()
            for trx in trxs:
                if pubkey == trx["Publisher"]:
                    yield trx


def get_trxs_from_old_chain(oldchain_client, group_id, trx_id, pubkey):
    """从旧链中读取 trxs"""
    return oldchain_client.api.get_group_all_contents(
        group_id=group_id, trx_id=trx_id, senders=[pubkey]
    )


def SendToGroup(keysfile, datadir, group_id, seed, progressfile, client_type="old"):
    """
    datadir: 旧链的数据目录
    group_id: 待迁移的 group_id，即只迁移这个 group 的相关数据
    seed: 新链的种子
    """

    keys = get_pvtkeys(keysfile, group_id)
    rum = MiniNode(seed)
    progress = JsonFile(progressfile).read({})

    for pubkey, pvtkey in keys.items():
        logger.info("send from group %s, pubkey %s", group_id, pubkey)
        rum.change_account(pvtkey)

        sent_trxs = progress.get(pubkey, {})
        for trx in get_trxs_from_local_files(datadir, group_id, pubkey):
            if trx["TrxId"] in sent_trxs:
                continue
            if client_type == "old":
                new = converter.from_old_chain(trx)
            else:
                new = converter.from_new_chain(trx)
            # 标记删除的 trx 不重发 #TODO:converter 修改结构
            if (
                new.get("data", {}).get("object", {}).get("content")
                == "OBJECT_STATUS_DELETED"
            ):
                continue
            if new["data"]:
                resp = rum.api.post_content(**new)
                logger.info(
                    "trx new %s from old %s",
                    resp["trx_id"],
                    trx["TrxId"],
                )
                time.sleep(0.2)
                sent_trxs[trx["TrxId"]] = (rum.api.group_id, resp["trx_id"])
            else:
                logger.warning("unknown trx %s", trx["TrxId"])
        progress[pubkey] = sent_trxs
        JsonFile(progressfile).write(progress)

    logger.info("send from group %s done", group_id)
