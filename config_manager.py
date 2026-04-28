# -*- coding: utf-8 -*-
"""
配置管理模块
负责生成配置文件和加载配置
"""

import json
import os
import sys

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
        "_使用说明": {
            "1_province_preset": "可选: 长江经济带 / 沿海经济带 / 京津冀 / 长三角 / 全部省份",
            "2_custom_provinces": "如需自定义省份，填在 custom_provinces 里，会覆盖预设",
            "3_time_range": "格式: 起始年YY-结束年YY，如 1995YY-2025YY",
            "4_delay": "每次请求间隔秒数，建议2-3秒",
            "5_如何获取指标参数": [
                "打开 data.stats.gov.cn/dg/website/page.html#/pc/national/fsYearData",
                "F12 → Network → Fetch/XHR",
                "点击左侧指标，等表格加载",
                "找到 getEsDataByCidAndDt 请求",
                "从 Payload 中复制 cid, rootId, indicatorIds",
            ],
        },
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
