# -*- coding: utf-8 -*-
"""
国家统计局新接口 - 分省年度数据爬虫 v2
适配 data.stats.gov.cn 2026年新版API

使用方式:
    1. python nbs_scraper.py --init              生成默认配置文件
    2. 编辑 config.json 填入抓包获取的指标参数
    3. python nbs_scraper.py                     运行爬虫
    4. python nbs_scraper.py --config xxx.json   指定配置文件
    5. python nbs_scraper.py --list-provinces    列出预设省份组
"""

import requests
import pandas as pd
import time
import json
import os
import sys
import argparse

requests.packages.urllib3.disable_warnings()


# ============================================================
# API 客户端
# ============================================================

class NbsClient:
    """国家统计局API客户端"""

    API_URL = "https://data.stats.gov.cn/dg/website/publicrelease/web/external/getEsDataByCidAndDt"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Referer": "https://data.stats.gov.cn/dg/website/page.html",
        "Origin": "https://data.stats.gov.cn",
    }

    def __init__(self, delay=2):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.session.verify = False

    def fetch(self, cid, indicator_ids, root_id, province_code, province_name, time_range):
        payload = {
            "cid": cid,
            "indicatorIds": indicator_ids,
            "daCatalogId": "",
            "das": [{"text": province_name, "value": province_code}],
            "dts": [time_range],
            "rootId": root_id,
            "showType": "1",
        }
        try:
            r = self.session.post(self.API_URL, json=payload, timeout=30)
            r.raise_for_status()
            result = r.json()
            if not result.get("success") or result.get("state") != 20000:
                return None, result.get("message", "未知错误")
            return result.get("data", []), None
        except requests.exceptions.Timeout:
            return None, "请求超时"
        except requests.exceptions.ConnectionError:
            return None, "连接失败"
        except Exception as e:
            return None, str(e)

    def wait(self):
        time.sleep(self.delay)


# ============================================================
# 数据解析
# ============================================================

def parse_response(raw_data, province_name):
    rows = []
    for year_block in raw_data:
        year = year_block.get("name", "")
        code = year_block.get("code", "")
        for item in year_block.get("values", []):
            value = item.get("value", "")
            if value == "" or value is None:
                continue
            rows.append({
                "省份": province_name,
                "年份": year,
                "年份代码": code,
                "指标": item.get("i_showname", "").strip(),
                "数值": value,
                "单位": item.get("du_name", ""),
            })
    return rows


# ============================================================
# 爬虫主逻辑
# ============================================================

def scrape(config):
    client = NbsClient(delay=config.get("delay", 2))
    provinces = config["provinces"]
    indicators = config["indicators"]
    time_range = config.get("time_range", "2015YY-2025YY")
    output_file = config.get("output", "统计局数据.xlsx")

    all_data = {}
    total_records = 0

    print(f"\n{'='*60}")
    print(f"  国家统计局分省年度数据爬虫 v2")
    print(f"  省份数量: {len(provinces)}")
    print(f"  指标组数: {len(indicators)}")
    print(f"  时间范围: {time_range}")
    print(f"  请求间隔: {client.delay}秒")
    print(f"  输出文件: {output_file}")
    print(f"{'='*60}\n")

    for ind_name, ind_config in indicators.items():
        print(f"[指标] {ind_name}")
        print(f"  {'─'*40}")
        rows = []

        for code, name in provinces.items():
            data, err = client.fetch(
                cid=ind_config["cid"],
                indicator_ids=ind_config["indicatorIds"],
                root_id=ind_config["rootId"],
                province_code=code,
                province_name=name,
                time_range=time_range,
            )
            if err:
                print(f"  ✗ {name}: {err}")
            elif data:
                parsed = parse_response(data, name)
                rows.extend(parsed)
                print(f"  ✓ {name}: {len(parsed)} 条")
            else:
                print(f"  - {name}: 无数据")

            client.wait()

        all_data[ind_name] = rows
        total_records += len(rows)
        print()

    print(f"共获取 {total_records} 条记录")

    if total_records > 0:
        save_excel(all_data, output_file)

    return all_data


# ============================================================
# 数据导出
# ============================================================

def save_excel(all_data, filepath):
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        for name, rows in all_data.items():
            if not rows:
                continue
            df = pd.DataFrame(rows)
            sheet = name[:20]
            df.to_excel(writer, sheet_name=f"{sheet}_明细", index=False)
            try:
                pivot = df.pivot_table(
                    index=["省份", "指标", "单位"],
                    columns="年份",
                    values="数值",
                    aggfunc="first"
                )
                pivot.to_excel(writer, sheet_name=f"{sheet}_透视")
            except Exception:
                pass

    print(f"已保存: {filepath}")


# ============================================================
# 预设省份组
# ============================================================

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


# ============================================================
# 配置管理
# ============================================================

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


# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="国家统计局分省年度数据爬虫 v2")
    parser.add_argument("--config", default="config.json", help="配置文件路径 (默认: config.json)")
    parser.add_argument("--init", action="store_true", help="生成默认配置文件")
    parser.add_argument("--list-provinces", action="store_true", help="列出预设省份组")
    args = parser.parse_args()

    if args.list_provinces:
        print("\n预设省份组:")
        for name, provinces in PROVINCE_PRESETS.items():
            print(f"\n  [{name}] ({len(provinces)}个省份)")
            for code, pname in provinces.items():
                print(f"    {code}: {pname}")
        return

    if args.init:
        generate_default_config(args.config)
        return

    if not os.path.exists(args.config):
        print(f"配置文件不存在: {args.config}")
        print("运行以下命令生成默认配置:")
        print(f"  python nbs_scraper.py --init")
        return

    config = load_config(args.config)
    scrape(config)


if __name__ == "__main__":
    main()
