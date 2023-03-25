"""
把旧链的 trx 转换成新链的 trx 并发送到指令 group
"""

import datetime
import time

from officy import Dir, JsonFile
from quorum_mininode_py import MiniNode, RumAccount
from quorum_mininode_py.api import LightNodeAPI
from quorum_mininode_py.client._http import HttpRequest
from quorum_mininode_py.crypto.account import public_key_to_address


def old_trx_to_new(trx):
    """把旧版的 trx 转换成新版的 trx data 和 timestamp，用于发送"""
    typeurl = trx.get("TypeUrl")
    pubkey = trx.get("Publisher")
    timestamp = trx.get("TimeStamp")

    if typeurl == "quorum.pb.Person":
        address = public_key_to_address(pubkey)
        obj = {
            "type": "Create",
            "object": {
                "type": "Profile",
                "describes": {"type": "Person", "id": address},
            },
        }
        name = trx.get("Content", {}).get("name", "")
        if name:
            obj["object"]["name"] = name

        image = trx.get("Content", {}).get("image")
        if image:
            obj["object"]["image"] = [
                {
                    "mediaType": image["mediaType"],
                    "content": image["content"],
                    "type": "Image",
                }
            ]
        return obj, timestamp

    if typeurl == "quorum.pb.Object":
        content = trx.get("Content", {})
        content_type = content.get("type")
        if content_type in ["Like", "Dislike"]:
            obj = {
                "type": content_type,
                "object": {"type": "Note", "id": content.get("id")},
            }
        else:
            if content.get("content") == "OBJECT_STATUS_DELETED":
                return None, None
            content["id"] = trx.get("TrxId")
            if "inreplyto" in content:
                content["inreplyto"] = {
                    "type": "Note",
                    "id": content["inreplyto"]["trxid"],
                }
            obj = {"type": "Create", "object": content}
        return obj, timestamp
    return None, None


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


def SendToGroup(keysfile, datadir, group_id, seed, progressfile):
    """
    datadir: 旧链的数据目录
    group_id: 待迁移的 group_id，即只迁移这个 group 的相关数据
    seed: 新链的种子
    """

    keys = get_pvtkeys(keysfile, group_id)
    rum = MiniNode(seed)
    progress = JsonFile(progressfile).read({})

    for pubkey, pvtkey in keys.items():
        rum.account = RumAccount(pvtkey)
        http = HttpRequest(rum.group.chainapi, rum.group.jwt)
        rum.api = LightNodeAPI(http, rum.group, rum.account)
        sent_trxs = progress.get(pubkey, {})
        for trx in get_trxs_from_local_files(datadir, group_id, pubkey):
            if trx["TrxId"] in sent_trxs:
                continue
            obj, timestamp = old_trx_to_new(trx)
            if obj:
                resp = rum.api.post_content(obj, timestamp)
                print(datetime.datetime.now(), resp)
                time.sleep(0.2)
                sent_trxs[trx["TrxId"]] = (rum.api.group_id, resp["trx_id"])
            else:
                print("unknown trx", trx["TrxId"])
        progress[pubkey] = sent_trxs
        JsonFile(progressfile).write(progress)
