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

requests.packages.urllib3.disable_warnings()


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


if __name__ == "__main__":
    print("本模块只包含爬虫相关功能，请通过 main.py 运行程序。")
    print("使用方式:")
    print("  python main.py --init      生成默认配置文件")
    print("  python main.py              运行爬虫")
