# rum-tools

把旧链的由自己所发布的 trxs 重新签名，发送到新链

1、search_keys: 从旧链数据目录还原出密钥

2、save_trxs: 把旧链数据保存为本地 trxs

3、post_trxs: 把旧链 trxs 转换为新链的数据结构，采用私钥签名后发送到新链

