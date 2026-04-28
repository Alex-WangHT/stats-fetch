# -*- coding: utf-8 -*-
"""
国家统计局新接口 - 分省年度数据爬虫 v2
适配 data.stats.gov.cn 2026年新版API
"""

import requests
import pandas as pd
import time
import random

requests.packages.urllib3.disable_warnings()


class NbsScraper:
    """国家统计局数据爬虫类"""

    API_URL = "https://data.stats.gov.cn/dg/website/publicrelease/web/external/getEsDataByCidAndDt"

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    ]

    BASE_HEADERS = {
        "Content-Type": "application/json",
        "Referer": "https://data.stats.gov.cn/dg/website/page.html",
        "Origin": "https://data.stats.gov.cn",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    def __init__(self, delay=2, human_like=True):
        self.delay = delay
        self.human_like = human_like
        self.session = requests.Session()
        self._init_session()

    def _init_session(self):
        """初始化会话，模拟人类浏览器环境"""
        if self.human_like:
            user_agent = random.choice(self.USER_AGENTS)
            headers = {**self.BASE_HEADERS, "User-Agent": user_agent}
        else:
            headers = {
                **self.BASE_HEADERS,
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
            }
        
        self.session.headers.update(headers)
        self.session.verify = False

    def _random_delay(self):
        """模拟人类的随机延迟"""
        if self.human_like:
            base_delay = self.delay
            jitter = random.uniform(-0.5, 1.0)
            actual_delay = max(0.5, base_delay + jitter)
            time.sleep(actual_delay)
        else:
            time.sleep(self.delay)

    def _rotate_user_agent(self):
        """随机轮换 User-Agent"""
        if self.human_like and random.random() < 0.3:
            new_ua = random.choice(self.USER_AGENTS)
            self.session.headers.update({"User-Agent": new_ua})

    def fetch(self, cid, indicator_ids, root_id, province_code, province_name, time_range):
        """执行单个数据请求"""
        payload = {
            "cid": cid,
            "indicatorIds": indicator_ids,
            "daCatalogId": "",
            "das": [{"text": province_name, "value": province_code}],
            "dts": [time_range],
            "rootId": root_id,
            "showType": "1",
        }
        
        if self.human_like:
            self._rotate_user_agent()
        
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

    def parse_response(self, raw_data, province_name):
        """解析 API 响应数据"""
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

    def scrape(self, config):
        """执行完整的爬虫流程"""
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
        print(f"  基础请求间隔: {self.delay}秒")
        print(f"  人类行为模拟: {'已启用' if self.human_like else '已禁用'}")
        print(f"  输出文件: {output_file}")
        print(f"{'='*60}\n")

        for ind_name, ind_config in indicators.items():
            print(f"[指标] {ind_name}")
            print(f"  {'─'*40}")
            rows = []

            for code, name in provinces.items():
                data, err = self.fetch(
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
                    parsed = self.parse_response(data, name)
                    rows.extend(parsed)
                    print(f"  ✓ {name}: {len(parsed)} 条")
                else:
                    print(f"  - {name}: 无数据")

                self._random_delay()

            all_data[ind_name] = rows
            total_records += len(rows)
            print()

        print(f"共获取 {total_records} 条记录")

        if total_records > 0:
            self.save_excel(all_data, output_file)

        return all_data

    def save_excel(self, all_data, filepath):
        """保存数据到 Excel 文件"""
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

    def close(self):
        """关闭会话"""
        self.session.close()


if __name__ == "__main__":
    print("本模块只包含爬虫相关功能，请通过 main.py 运行程序。")
    print("使用方式:")
    print("  python main.py --init      生成默认配置文件")
    print("  python main.py              运行爬虫")
