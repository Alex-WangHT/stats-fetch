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
QUERY_INDICATORS_BY_CID_URL = "https://data.stats.gov.cn/dg/website/publicrelease/web/external/new/queryIndicatorsByCid"

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


def get_indicator_ids(cid, dt="2015-2025", name=""):
    """
    获取第四级节点ID列表（indicatorIds）
    
    访问: https://data.stats.gov.cn/dg/website/publicrelease/web/external/new/queryIndicatorsByCid
    参数包含: cid={cid}, dt={dt}, name={name}
    
    参数:
        cid: 第二级节点的cid（指标分类ID）
        dt: 年份范围，格式为 "yyyy-yyyy"，例如 "2015-2025"，默认为 "2015-2025"
        name: 指标名称搜索关键词，默认为空字符串
    
    返回:
        list: 包含字典的列表，每个字典格式为:
              {'name': '指标名称', 'indicatorId': '指标ID'}
    """
    params = {
        "cid": cid,
        "dt": dt,
        "name": name
    }
    
    try:
        session = requests.Session()
        session.headers.update(QUERY_HEADERS)
        session.verify = False
        
        r = session.get(QUERY_INDICATORS_BY_CID_URL, params=params, timeout=30)
        r.raise_for_status()
        result = r.json()
        
        if not result.get("success") or result.get("state") != 20000:
            print(f"[警告] API返回错误: {result.get('message', '未知错误')}")
            return []
        
        data = result.get("data", {})
        item_list = data.get("list", [])
        
        indicator_ids = []
        for item in item_list:
            indicator_ids.append({
                "name": item.get("i_showname", ""),
                "indicatorId": item.get("_id", "")
            })
        
        return indicator_ids
    
    except requests.exceptions.Timeout:
        print("[错误] 请求超时")
        return []
    except requests.exceptions.ConnectionError:
        print("[错误] 连接失败")
        return []
    except Exception as e:
        print(f"[错误] {str(e)}")
        return []

def select_from_list(items, display_key="name", title="请选择"):
    """
    从列表中交互式选择一个项
    
    参数:
        items: 包含字典的列表
        display_key: 显示用的键名
        title: 选择提示标题
    
    返回:
        dict: 用户选择的字典项，或None（退出）
    """
    if not items:
        print("[错误] 列表为空")
        return None
    
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    
    for i, item in enumerate(items, 1):
        name = item.get(display_key, "未知")
        print(f"  [{i}] {name}")
    
    print(f"  [0] 退出/返回上一级")
    print(f"{'='*60}")
    
    while True:
        try:
            choice = input("\n请输入数字选择: ").strip()
            if choice == "0":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                return items[idx]
            else:
                print(f"请输入 0-{len(items)} 之间的数字")
        except ValueError:
            print("请输入有效的数字")


def select_multiple_from_list(items, display_key="name", title="请选择（可多选，用逗号分隔，如 1,3,5）"):
    """
    从列表中交互式选择多个项
    
    参数:
        items: 包含字典的列表
        display_key: 显示用的键名
        title: 选择提示标题
    
    返回:
        list: 用户选择的字典项列表，或空列表（退出）
    """
    if not items:
        print("[错误] 列表为空")
        return []
    
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    
    for i, item in enumerate(items, 1):
        name = item.get(display_key, "未知")
        print(f"  [{i}] {name}")
    
    print(f"  [0] 全选")
    print(f"  [输入 q] 退出/返回上一级")
    print(f"{'='*60}")
    
    while True:
        choice = input("\n请输入数字选择: ").strip().lower()
        if choice == "q":
            return []
        if choice == "0":
            return items
        
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            selected = []
            for idx in indices:
                if 0 <= idx < len(items):
                    selected.append(items[idx])
                else:
                    print(f"警告: 索引 {idx+1} 超出范围，已跳过")
            if selected:
                return selected
            else:
                print("未选择任何有效项")
        except ValueError:
            print("请输入有效的数字，多个选择用逗号分隔")


def input_year_range():
    """
    交互式输入年份范围
    
    返回:
        tuple: (dt格式, time_range格式)
               例如: ("2015-2025", "2015YY-2025YY")
    """
    print(f"\n{'='*60}")
    print(f"  请输入年份范围")
    print(f"{'='*60}")
    print("格式示例: 2015-2025")
    print("直接回车使用默认值: 2015-2025")
    
    while True:
        user_input = input("\n请输入年份范围: ").strip()
        if not user_input:
            user_input = "2015-2025"
        
        if "-" in user_input:
            parts = user_input.split("-")
            if len(parts) == 2:
                try:
                    start = int(parts[0].strip())
                    end = int(parts[1].strip())
                    if start <= end and 1949 <= start <= 2050 and 1949 <= end <= 2050:
                        dt_format = f"{start}-{end}"
                        time_range_format = f"{start}YY-{end}YY"
                        return dt_format, time_range_format
                except ValueError:
                    pass
        print("格式错误，请重新输入，例如: 2015-2025")


def select_province_preset():
    """
    交互式选择省份预设
    
    返回:
        tuple: (preset_name, provinces_dict) 或 (None, None)
    """
    print(f"\n{'='*60}")
    print(f"  请选择省份预设")
    print(f"{'='*60}")
    
    presets = list(PROVINCE_PRESETS.keys())
    
    for i, name in enumerate(presets, 1):
        count = len(PROVINCE_PRESETS[name])
        print(f"  [{i}] {name} ({count}个省份)")
    
    print(f"  [0] 退出")
    print(f"{'='*60}")
    
    while True:
        try:
            choice = input("\n请输入数字选择: ").strip()
            if choice == "0":
                return None, None
            idx = int(choice) - 1
            if 0 <= idx < len(presets):
                preset_name = presets[idx]
                return preset_name, PROVINCE_PRESETS[preset_name]
            else:
                print(f"请输入 0-{len(presets)} 之间的数字")
        except ValueError:
            print("请输入有效的数字")


def select_custom_provinces():
    """
    交互式从全部省份中选择多个省份
    
    返回:
        dict: 选择的省份字典 {code: name}
    """
    all_provinces = PROVINCE_PRESETS["全部省份"]
    province_list = [{"code": code, "name": name} for code, name in all_provinces.items()]
    
    print(f"\n{'='*60}")
    print(f"  请从全部省份中选择（可多选）")
    print(f"{'='*60}")
    
    for i, item in enumerate(province_list, 1):
        print(f"  [{i}] {item['name']}")
    
    print(f"  [0] 全选")
    print(f"  [输入 q] 退出/返回上一级")
    print(f"{'='*60}")
    
    while True:
        choice = input("\n请输入数字选择: ").strip().lower()
        if choice == "q":
            return {}
        if choice == "0":
            return all_provinces
        
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            selected = {}
            for idx in indices:
                if 0 <= idx < len(province_list):
                    item = province_list[idx]
                    selected[item["code"]] = item["name"]
                else:
                    print(f"警告: 索引 {idx+1} 超出范围，已跳过")
            if selected:
                return selected
            else:
                print("未选择任何有效项")
        except ValueError:
            print("请输入有效的数字，多个选择用逗号分隔")


def filter_cids_with_indicators(cids, dt_format):
    """
    筛选有指标的二级目录
    
    参数:
        cids: 二级目录列表
        dt_format: 年份范围格式
    
    返回:
        list: 有指标的二级目录列表，每个元素包含额外信息
    """
    valid_cids = []
    
    print(f"\n  正在检查各目录是否有可用指标（可能需要一些时间）...")
    
    for cid_item in cids:
        cid_name = cid_item["name"]
        cid = cid_item["cid"]
        
        print(f"  检查 [{cid_name}] ...", end="", flush=True)
        
        fids = get_fids(cid)
        
        if fids:
            valid_fids = []
            for fid_item in fids:
                fid_name = fid_item["name"]
                fid = fid_item["fid"]
                
                indicator_ids = get_indicator_ids(fid, dt=dt_format)
                if indicator_ids:
                    valid_fids.append({
                        "name": fid_name,
                        "fid": fid,
                        "indicators": indicator_ids
                    })
            
            if valid_fids:
                valid_cids.append({
                    "name": cid_name,
                    "cid": cid,
                    "has_fids": True,
                    "valid_fids": valid_fids
                })
                print(f" ✓ ({len(valid_fids)} 个有效子目录)")
            else:
                print(f" ✗ (无可用指标)")
        else:
            indicator_ids = get_indicator_ids(cid, dt=dt_format)
            if indicator_ids:
                valid_cids.append({
                    "name": cid_name,
                    "cid": cid,
                    "has_fids": False,
                    "indicators": indicator_ids
                })
                print(f" ✓ ({len(indicator_ids)} 个指标)")
            else:
                print(f" ✗ (无可用指标)")
    
    return valid_cids


def generate_config_interactively(config_path="config.json"):
    """
    交互式生成配置文件
    
    新流程（带预筛选）:
    1. 选择一级目录（root_id）- 单选
    2. 输入年份范围
    3. 预筛选：只保留有指标的二级目录和三级目录
    4. 选择二级目录（cid）- 多选（只显示有指标的）
    5. 对每个选中的cid：
       a. 如果有fid层级，选择fid（多选，只显示有指标的）
       b. 选择指标（多选）
    6. 选择省份
    7. 配置其他选项
    8. 生成配置文件
    """
    print(f"\n{'='*60}")
    print(f"  国家统计局数据爬虫 - 交互式配置生成器 v3")
    print(f"{'='*60}")
    
    print(f"\n{'='*60}")
    print(f"  步骤 1/8: 选择一级目录")
    print(f"{'='*60}")
    
    root_ids = get_root_ids()
    if not root_ids:
        print("[错误] 无法获取一级目录，请检查网络连接")
        return False
    
    selected_root = select_from_list(root_ids, display_key="name", title="请选择一级目录")
    if not selected_root:
        print("已退出")
        return False
    
    root_name = selected_root["name"]
    root_id = selected_root["rootId"]
    
    print(f"\n已选择: {root_name}")
    
    print(f"\n{'='*60}")
    print(f"  步骤 2/8: 输入年份范围")
    print(f"{'='*60}")
    
    dt_format, time_range_format = input_year_range()
    print(f"\n已选择年份范围: {dt_format}")
    
    print(f"\n{'='*60}")
    print(f"  步骤 3/8: 预筛选有指标的目录")
    print(f"{'='*60}")
    
    cids = get_cids(root_id)
    if not cids:
        print("[错误] 无法获取二级目录")
        return False
    
    print(f"\n  共发现 {len(cids)} 个二级目录")
    
    valid_cids = filter_cids_with_indicators(cids, dt_format)
    
    if not valid_cids:
        print("[错误] 没有找到有可用指标的目录")
        return False
    
    print(f"\n  筛选出 {len(valid_cids)} 个有可用指标的二级目录")
    
    print(f"\n{'='*60}")
    print(f"  步骤 4/8: 选择二级目录（可多选）")
    print(f"{'='*60}")
    print("  提示: 只显示有可用指标的目录")
    
    cid_options = [{"name": item["name"], "cid": item["cid"]} for item in valid_cids]
    
    selected_cid_items = select_multiple_from_list(
        cid_options, 
        display_key="name", 
        title="请选择二级目录（可多选，如 1,3,5）"
    )
    if not selected_cid_items:
        print("未选择任何二级目录，已退出")
        return False
    
    print(f"\n已选择 {len(selected_cid_items)} 个二级目录")
    
    selected_cids = []
    for selected_item in selected_cid_items:
        for valid_item in valid_cids:
            if valid_item["cid"] == selected_item["cid"]:
                selected_cids.append(valid_item)
                break
    
    indicators_config = {}
    
    print(f"\n{'='*60}")
    print(f"  步骤 5/8: 为每个二级目录选择指标")
    print(f"{'='*60}")
    
    for cid_item in selected_cids:
        cid_name = cid_item["name"]
        cid = cid_item["cid"]
        has_fids = cid_item["has_fids"]
        
        print(f"\n{'-'*60}")
        print(f"  处理二级目录: {cid_name}")
        print(f"{'-'*60}")
        
        if has_fids:
            valid_fids = cid_item["valid_fids"]
            print(f"\n  发现 {len(valid_fids)} 个有指标的三级目录")
            
            fid_options = [{"name": item["name"], "fid": item["fid"]} for item in valid_fids]
            
            selected_fid_items = select_multiple_from_list(
                fid_options, 
                display_key="name", 
                title=f"请为 [{cid_name}] 选择三级目录（可多选）"
            )
            if not selected_fid_items:
                print(f"  跳过 [{cid_name}]")
                continue
            
            print(f"\n  已选择 {len(selected_fid_items)} 个三级目录")
            
            for selected_fid_item in selected_fid_items:
                fid_name = selected_fid_item["name"]
                fid = selected_fid_item["fid"]
                
                indicator_ids = None
                for valid_fid in valid_fids:
                    if valid_fid["fid"] == fid:
                        indicator_ids = valid_fid["indicators"]
                        break
                
                if not indicator_ids:
                    print(f"  [警告] 未获取到 [{fid_name}] 的指标列表")
                    continue
                
                selected_indicators = select_multiple_from_list(
                    indicator_ids, 
                    display_key="name", 
                    title=f"请为 [{fid_name}] 选择指标（可多选）"
                )
                
                if not selected_indicators:
                    print(f"  跳过 [{fid_name}]")
                    continue
                
                indicator_name = f"{cid_name} - {fid_name}"
                indicator_id_list = [item["indicatorId"] for item in selected_indicators]
                
                print(f"\n  已选择 {len(indicator_id_list)} 个指标")
                
                indicators_config[indicator_name] = {
                    "cid": cid,
                    "indicatorIds": indicator_id_list,
                    "rootId": root_id,
                    "fid": fid
                }
        else:
            indicator_ids = cid_item["indicators"]
            print(f"\n  该目录有 {len(indicator_ids)} 个指标")
            
            selected_indicators = select_multiple_from_list(
                indicator_ids, 
                display_key="name", 
                title=f"请为 [{cid_name}] 选择指标（可多选）"
            )
            
            if not selected_indicators:
                print(f"  跳过 [{cid_name}]")
                continue
            
            indicator_name = cid_name
            indicator_id_list = [item["indicatorId"] for item in selected_indicators]
            
            print(f"\n  已选择 {len(indicator_id_list)} 个指标")
            
            indicators_config[indicator_name] = {
                "cid": cid,
                "indicatorIds": indicator_id_list,
                "rootId": root_id
            }
    
    if not indicators_config:
        print("[错误] 未选择任何指标，无法生成配置文件")
        return False
    
    print(f"\n{'='*60}")
    print(f"  步骤 6/8: 选择省份")
    print(f"{'='*60}")
    print("  [1] 使用预设省份组")
    print("  [2] 自定义选择省份")
    print("  [0] 退出")
    
    province_preset = ""
    custom_provinces = {}
    
    while True:
        choice = input("\n请选择: ").strip()
        if choice == "1":
            preset_name, provinces = select_province_preset()
            if preset_name:
                province_preset = preset_name
                custom_provinces = {}
                print(f"\n已选择省份预设: {preset_name}")
                break
            else:
                print("已退出")
                return False
        elif choice == "2":
            custom_provinces = select_custom_provinces()
            if custom_provinces:
                province_preset = ""
                print(f"\n已选择 {len(custom_provinces)} 个省份")
                break
            else:
                print("已退出")
                return False
        elif choice == "0":
            print("已退出")
            return False
        else:
            print("请输入 1, 2 或 0")
    
    print(f"\n{'='*60}")
    print(f"  步骤 7/8: 配置其他选项")
    print(f"{'='*60}")
    
    delay_input = input("\n请求间隔（秒，默认2）: ").strip()
    delay = int(delay_input) if delay_input.isdigit() else 2
    
    default_output = "统计局数据.xlsx"
    output = input(f"输出文件名（默认: {default_output}）: ").strip()
    if not output:
        output = default_output
    if not output.endswith(".xlsx"):
        output += ".xlsx"
    
    print(f"\n{'='*60}")
    print(f"  步骤 8/8: 生成配置文件")
    print(f"{'='*60}")
    
    config = {
        "province_preset": province_preset,
        "custom_provinces": custom_provinces,
        "time_range": time_range_format,
        "delay": delay,
        "output": output,
        "indicators": indicators_config,
    }
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
    
    print(f"\n{'='*60}")
    print(f"  配置生成完成！")
    print(f"{'='*60}")
    print(f"  配置文件: {config_path}")
    print(f"  省份预设: {province_preset if province_preset else '自定义'}")
    print(f"  年份范围: {time_range_format}")
    print(f"  指标组数: {len(indicators_config)}")
    print(f"  输出文件: {output}")
    print(f"\n  现在可以运行 python main.py 开始抓取数据")
    print(f"{'='*60}")
    
    return True


if __name__ == "__main__":
    generate_config_interactively()