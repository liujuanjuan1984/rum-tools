import base64
import json
import logging
import os

from pyrage import passphrase
from quorum_mininode_py.crypto.account import (
    keystore_to_private_key,
    private_key_to_pubkey,
)

logger = logging.getLogger(__name__)


def search_files_starts_with(folder: str, *seps: str):
    """从文件夹中搜索 keystore 文件"""
    for root, paths, names in os.walk(folder):
        for name in names:
            if name.startswith(seps):
                ifile = os.path.join(root, name)
                logger.debug("search file %s", ifile)
                yield ifile


def read_file(ifile: str):
    """读取文件，包括 eth keystore 和 age pubkey"""
    logger.debug("read file %s", ifile)
    idata = None
    if not os.path.exists(ifile):
        logger.warning("file %s not exists", ifile)
    elif "sign_" in ifile:
        with open(ifile, "r", encoding="utf-8") as f:
            idata = f.read()
    elif "encrypt_" in ifile:
        with open(ifile, "rb") as f:
            idata = f.read()
    return idata


def get_keys(files, pwds: list) -> dict:
    """生成 group_id 到 keys 的映射"""
    keys_map = {}
    for ifile in files:
        ifile_name = os.path.basename(ifile)
        if ifile_name.startswith("sign_"):
            # read file
            keystore = read_file(ifile)
            jfile = ifile.replace("sign_", "encrypt_")
            agebytes = read_file(jfile)
            # guess keys
            pvtkey = guess_pvtkey(keystore, pwds)
            agekey = guess_agekey(agebytes, pwds)
            if isinstance(pvtkey, str):
                pubkey = private_key_to_pubkey(pvtkey)
            else:
                pubkey = None
            ikeys = {"pvtkey": pvtkey, "agekey": agekey, "pubkey": pubkey}
            logger.debug("get keys %s", ikeys)
            # add to map
            group_id = ifile_name.strip("sign_")
            if group_id not in keys_map:
                keys_map[group_id] = [ikeys]
            elif ikeys not in keys_map[group_id]:
                keys_map[group_id].append(ikeys)
    return keys_map


def _guess(func, data, pwds: list):
    """尝试用密码还原私钥，能还原就返回私钥，否则返回原始数据"""
    rlt = None
    if data:
        for pwd in pwds:
            try:
                rlt = func(data, pwd)
                break
            except:
                pass
    return rlt or data


def guess_pvtkey(keystore, pwds: list):
    """还原 eth 私钥"""
    if isinstance(keystore, str):
        keystore = json.loads(keystore)
    return _guess(keystore_to_private_key, keystore, pwds)


def guess_agekey(agebytes: bytes, pwds: list) -> str:
    """还原 age 私钥"""
    agekey = _guess(passphrase.decrypt, agebytes, pwds)
    if isinstance(agekey, bytes):
        try:
            agekey = agekey.decode()  # age-pvtkey
        except:
            agekey = base64.b64encode(agekey).decode()  # age-pubkey-bytes
            pass
    return agekey


def SearchKeys(
    target_folder: str,
    passwd_list: list,
    result_data_file: str = None,
    sep: str = "sign_",
) -> dict:
    """从目标文件夹中搜寻密钥文件，并用提供的密码列表来还原出私钥，生成 group_id 到 密钥 的映射"""
    keyfiles = search_files_starts_with(target_folder, sep)
    keydata = get_keys(keyfiles, passwd_list)
    # write the keys to file
    if result_data_file:
        # 如果目标文件已存在，就合并数据
        if os.path.exists(result_data_file):
            with open(result_data_file, "r", encoding="utf-8") as f:
                idata = json.load(f)
            for gid, keys in idata.items():
                if gid not in keydata:
                    keydata[gid] = keys
                else:
                    for key in keys:
                        if key not in keydata[gid]:
                            keydata[gid].append(key)
            # keydata.update(idata)
        # 写入文件
        with open(result_data_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(keydata, indent=1))
    return keydata
