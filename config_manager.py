# -*- coding: utf-8 -*-
"""
配置管理模块
负责生成配置文件和加载配置
"""

import json
import sys
import requests

requests.packages.urllib3.disable_warnings()

QUERY_INDEX_TREE_URL = "https://data.stats.gov.cn/dg/website/publicrelease/web/external/new/queryIndexTreeAsync"

QUERY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://data.stats.gov.cn/dg/website/page.html",
    "Origin": "https://data.stats.gov.cn",
}

PROVINCE_PRESETS = {
    "长江经济带": {
        "310000000000": "上海市",
        "320000000000": "江苏省",
        "330000000000": "浙江省",
        "340000000000": "安徽省",
        "360000000000": "江西省",
        "420000000000": "湖北省",
        "430000000000": "湖南省",
        "500000000000": "重庆市",
        "510000000000": "四川省",
        "520000000000": "贵州省",
        "530000000000": "云南省",
    },
    "沿海经济带": {
        "120000000000": "天津市",
        "130000000000": "河北省",
        "210000000000": "辽宁省",
        "310000000000": "上海市",
        "320000000000": "江苏省",
        "330000000000": "浙江省",
        "350000000000": "福建省",
        "370000000000": "山东省",
        "440000000000": "广东省",
        "450000000000": "广西壮族自治区",
        "460000000000": "海南省",
    },
    "京津冀": {
        "110000000000": "北京市",
        "120000000000": "天津市",
        "130000000000": "河北省",
    },
    "长三角": {
        "310000000000": "上海市",
        "320000000000": "江苏省",
        "330000000000": "浙江省",
        "340000000000": "安徽省",
    },
    "全部省份": {
        "110000000000": "北京市",
        "120000000000": "天津市",
        "130000000000": "河北省",
        "140000000000": "山西省",
        "150000000000": "内蒙古自治区",
        "210000000000": "辽宁省",
        "220000000000": "吉林省",
        "230000000000": "黑龙江省",
        "310000000000": "上海市",
        "320000000000": "江苏省",
        "330000000000": "浙江省",
        "340000000000": "安徽省",
        "350000000000": "福建省",
        "360000000000": "江西省",
        "370000000000": "山东省",
        "410000000000": "河南省",
        "420000000000": "湖北省",
        "430000000000": "湖南省",
        "440000000000": "广东省",
        "450000000000": "广西壮族自治区",
        "460000000000": "海南省",
        "500000000000": "重庆市",
        "510000000000": "四川省",
        "520000000000": "贵州省",
        "530000000000": "云南省",
        "540000000000": "西藏自治区",
        "610000000000": "陕西省",
        "620000000000": "甘肃省",
        "630000000000": "青海省",
        "640000000000": "宁夏回族自治区",
        "650000000000": "新疆维吾尔自治区",
    },
}


def generate_default_config(config_path="config.json"):
    config = {
        "province_preset": "长江经济带",
        "custom_provinces": {},
        "time_range": "1995YY-2025YY",
        "delay": 3,
        "output": "长江经济带30年数据.xlsx",
        "indicators": {
            "地区生产总值": {
                "cid": "f401b4ba4e494f1e9e00629720f4408f",
                "indicatorIds": [
                    "bd561031e16b47ad854697ad9e8d96ee",
                    "3bb085e03ec04bbca3bb3aa807782d11",
                    "_TODO_补充完整ID列表"
                ],
                "rootId": "c4d82af16c3d4f0cb4f09d4af7d5888e"
            }
        },
    }

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

    print(f"已生成配置文件: {config_path}")
    print("请编辑配置文件，填入抓包获取的 indicatorIds 后运行脚本。")


def load_config(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    preset = raw.get("province_preset", "")
    custom = raw.get("custom_provinces", {})

    if custom:
        provinces = custom
    elif preset in PROVINCE_PRESETS:
        provinces = PROVINCE_PRESETS[preset]
    else:
        print(f"[错误] 未知的省份预设: {preset}")
        print(f"可选: {', '.join(PROVINCE_PRESETS.keys())}")
        sys.exit(1)

    return {
        "provinces": provinces,
        "indicators": {k: v for k, v in raw.get("indicators", {}).items() if not k.startswith("_")},
        "time_range": raw.get("time_range", "2015YY-2025YY"),
        "delay": raw.get("delay", 2),
        "output": raw.get("output", "统计局数据.xlsx"),
    }


def query_index_tree(pid, code="6"):
    """
    访问指标树API的通用函数
    
    参数:
        pid: 父级ID，首次访问时为空字符串
        code: 指标类型代码，默认为6（年度数据）
    
    返回:
        list: response['data'] 列表，每个元素包含 '_id', 'name' 等字段
              若请求失败返回空列表
    """
    params = {
        "pid": pid,
        "code": code
    }
    
    try:
        session = requests.Session()
        session.headers.update(QUERY_HEADERS)
        session.verify = False
        
        r = session.get(QUERY_INDEX_TREE_URL, params=params, timeout=30)
        r.raise_for_status()
        result = r.json()
        
        if not result.get("success") or result.get("state") != 20000:
            print(f"[警告] API返回错误: {result.get('message', '未知错误')}")
            return []
        
        return result.get("data", [])
    
    except requests.exceptions.Timeout:
        print("[错误] 请求超时")
        return []
    except requests.exceptions.ConnectionError:
        print("[错误] 连接失败")
        return []
    except Exception as e:
        print(f"[错误] {str(e)}")
        return []


def get_root_ids():
    """
    获取第一级节点ID列表（rootIds）
    
    访问: https://data.stats.gov.cn/dg/website/publicrelease/web/external/new/queryIndexTreeAsync?pid=&code=6
    
    返回:
        list: 包含字典的列表，每个字典格式为:
              {'name': '节点名称', 'rootId': '节点ID'}
    """
    data = query_index_tree(pid="", code="6")
    
    root_ids = []
    for item in data:
        root_ids.append({
            "name": item.get("name", ""),
            "rootId": item.get("_id", "")
        })
    
    return root_ids


def get_cids(root_id):
    """
    获取第二级节点ID列表（cids）
    
    访问: https://data.stats.gov.cn/dg/website/publicrelease/web/external/new/queryIndexTreeAsync?pid={rootId}&code=6
    
    参数:
        root_id: 第一级节点的rootId
    
    返回:
        list: 包含字典的列表，每个字典格式为:
              {'name': '节点名称', 'cid': '节点ID'}
    """
    data = query_index_tree(pid=root_id, code="6")
    
    cids = []
    for item in data:
        cids.append({
            "name": item.get("name", ""),
            "cid": item.get("_id", "")
        })
    
    return cids


def get_fids(cid):
    """
    获取第三级节点ID列表（fids）
    
    访问: https://data.stats.gov.cn/dg/website/publicrelease/web/external/new/queryIndexTreeAsync?pid={cid}&code=6
    
    参数:
        cid: 第二级节点的cid
    
    返回:
        list: 包含字典的列表，每个字典格式为:
              {'name': '节点名称', 'fid': '节点ID'}
    """
    data = query_index_tree(pid=cid, code="6")
    
    fids = []
    for item in data:
        fids.append({
            "name": item.get("name", ""),
            "fid": item.get("_id", "")
        })
    
    return fids


def get_indicator_ids(fid):
    """
    获取第四级节点ID列表（indicatorIds）
    
    访问: https://data.stats.gov.cn/dg/website/publicrelease/web/external/new/queryIndexTreeAsync?pid={fid}&code=6
    
    参数:
        fid: 第三级节点的fid
    
    返回:
        list: 包含字典的列表，每个字典格式为:
              {'name': '节点名称', 'indicatorId': '节点ID'}
    """
    data = query_index_tree(pid=fid, code="6")
    
    indicator_ids = []
    for item in data:
        indicator_ids.append({
            "name": item.get("name", ""),
            "indicatorId": item.get("_id", "")
        })
    
    return indicator_ids
