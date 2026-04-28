# -*- coding: utf-8 -*-
"""
主入口文件
整合配置管理和爬虫模块

新流程：
1. 检查配置文件是否存在
2. 不存在则自动启动交互式配置生成
3. 配置生成完成后无缝切换到爬虫流程
"""

import os
import argparse

from config_manager import (
    PROVINCE_PRESETS,
    generate_default_config,
    load_config,
    generate_config_interactively
)
from nbs_scraper import NbsScraper


def main():
    parser = argparse.ArgumentParser(description="国家统计局分省年度数据爬虫 v4.0")
    parser.add_argument("--config", default="config.json", help="配置文件路径 (默认: config.json)")
    parser.add_argument("--init", action="store_true", help="生成默认配置文件")
    parser.add_argument("--list-provinces", action="store_true", help="列出预设省份组")
    parser.add_argument("--no-human-like", action="store_true", help="禁用人类行为模拟")
    parser.add_argument("--no-interactive", action="store_true", help="禁用交互式配置（配置文件不存在时直接退出）")
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

    config = None
    
    if not os.path.exists(args.config):
        if args.no_interactive:
            print(f"配置文件不存在: {args.config}")
            print("运行以下命令生成默认配置:")
            print(f"  python main.py --init")
            return
        else:
            print(f"\n{'='*60}")
            print(f"  配置文件不存在: {args.config}")
            print(f"  将启动交互式配置生成器...")
            print(f"{'='*60}")
            
            result, generated_config = generate_config_interactively(args.config)
            
            if not result or not generated_config:
                print("\n配置生成失败或已取消，程序退出。")
                return
            
            config = generated_config
            print(f"\n{'='*60}")
            print(f"  配置生成完成，即将开始数据抓取...")
            print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print(f"  找到配置文件: {args.config}")
        print(f"{'='*60}")
        config = load_config(args.config)
    
    if not config:
        print("[错误] 无法加载配置")
        return
    
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
