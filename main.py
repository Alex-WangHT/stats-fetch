# -*- coding: utf-8 -*-
"""
主入口文件
整合配置管理和爬虫模块
"""

import os
import argparse

from config_manager import (
    PROVINCE_PRESETS,
    generate_default_config,
    load_config
)
from nbs_scraper import NbsScraper


def main():
    parser = argparse.ArgumentParser(description="国家统计局分省年度数据爬虫 v2")
    parser.add_argument("--config", default="config.json", help="配置文件路径 (默认: config.json)")
    parser.add_argument("--init", action="store_true", help="生成默认配置文件")
    parser.add_argument("--list-provinces", action="store_true", help="列出预设省份组")
    parser.add_argument("--no-human-like", action="store_true", help="禁用人类行为模拟")
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
        print(f"  python main.py --init")
        return

    config = load_config(args.config)
    
    scraper = NbsScraper(
        delay=config.get("delay", 2),
        human_like=not args.no_human_like
    )
    
    try:
        scraper.scrape(config)
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
