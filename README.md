# stats-fetch
自动抓取 [data.stats.gov.cn](https://data.stats.gov.cn) 分省统计数据，支持多时间，多指标、多省份批量下载，结果导出为 Excel（明细表 + 透视表）。

---

## 环境要求

```bash
pip install requests pandas openpyxl
```

---

## 第一步：初始化配置文件

在脚本所在目录运行：

```bash
python nbs_scraper.py --init
```

这会在当前目录生成一个 `config.json` 模板文件，内容包含省份预设、时间范围、请求间隔等默认参数。

---

## 第二步：从浏览器抓包获取指标参数

这是最关键的一步。每个指标（如地区生产总值、工业总产值等）在统计局后台都有唯一的 `cid`、`rootId` 和 `indicatorIds`，需要通过浏览器开发者工具手动抓取。

### 2.1 打开目标页面

在浏览器中访问：

```
https://data.stats.gov.cn/dg/website/page.html#/pc/national/fsYearData
```

### 2.2 打开开发者工具

按 `F12`（或右键页面 → 检查），打开开发者工具面板。

切换到 **Network（网络）** 标签页。

在过滤器输入框中输入：

```
getEsDataByCidAndDt
```

这样可以只显示我们需要的 API 请求，过滤掉其他无关流量。

### 2.3 触发目标指标的请求

在统计局页面的**左侧指标树**中，点击你想抓取的指标（例如「地区生产总值」）。

等待右侧表格数据加载完成。

此时 Network 面板中会出现一条名为 `getEsDataByCidAndDt` 的请求记录。

### 2.4 提取参数

点击该请求记录，切换到 **Payload（载荷）** 或 **Request Body** 子标签，你会看到类似如下的 JSON 内容：

```json
{
  "cid": "f401b4ba4e494f1e9e00629720f4408f",
  "indicatorIds": [
    "bd561031e16b47ad854697ad9e8d96ee",
    "3bb085e03ec04bbca3bb3aa807782d11",
    "a7c903f12d4e4b8d9e1234567890abcd",
    "..."
  ],
  "daCatalogId": "",
  "das": [...],
  "dts": [...],
  "rootId": "c4d82af16c3d4f0cb4f09d4af7d5888e",
  "showType": "1"
}
```

将以下三个字段的值**完整复制**出来：

| 字段 | 说明 |
|------|------|
| `cid` | 该指标分类的唯一ID |
| `rootId` | 指标树的根节点ID |
| `indicatorIds` | 所有子指标的ID列表（通常有多个，全部复制） |

> **注意：** `indicatorIds` 是一个数组，里面可能有十几个甚至更多的 ID，对应表格里的每一列（如「GDP总量」「第一产业」「第二产业」等）。务必完整复制整个数组，不要遗漏。

### 2.5 对每个需要的指标重复上述操作

每点击一个新指标，就会产生一条新的 `getEsDataByCidAndDt` 请求，重复 2.3 → 2.4 的步骤，分别记录各指标的参数。

---

## 第三步：填写 config.json

用文本编辑器打开生成的 `config.json`，按实际需求修改以下字段：

```jsonc
{
  "province_preset": "长江经济带",   // 省份预设，可选：长江经济带 / 沿海经济带 / 京津冀 / 长三角 / 全部省份
  "custom_provinces": {},            // 自定义省份（填写后会覆盖 province_preset）
  "time_range": "1995YY-2025YY",    // 数据时间范围
  "delay": 3,                        // 每次请求间隔秒数，建议 2~3 秒，避免被封
  "output": "长江经济带30年数据.xlsx",

  "indicators": {
    "地区生产总值": {                  // 指标名称（自定义，用作 Excel Sheet 名）
      "cid": "从抓包中复制",
      "rootId": "从抓包中复制",
      "indicatorIds": [
        "从抓包中复制（完整数组）"
      ]
    },
    "固定资产投资": {                  // 第二个指标，格式相同
      "cid": "...",
      "rootId": "...",
      "indicatorIds": ["...", "..."]
    }
  }
}
```

如需自定义省份，在 `custom_provinces` 中按如下格式填写（会覆盖 `province_preset`）：

```json
"custom_provinces": {
  "110000000000": "北京市",
  "440000000000": "广东省"
}
```

查看所有预设省份及其代码：

```bash
python nbs_scraper.py --list-provinces
```

---

## 第四步：运行爬虫

配置填写完毕后，直接运行：

```bash
python nbs_scraper.py
```

程序会按省份逐一请求，控制台实时显示进度：

```
============================================================
  国家统计局分省年度数据爬虫 v2
  省份数量: 11
  指标组数: 2
  时间范围: 1995YY-2025YY
  请求间隔: 3秒
  输出文件: 长江经济带30年数据.xlsx
============================================================

[指标] 地区生产总值
  ────────────────────────────────────────
  ✓ 上海市: 48 条
  ✓ 江苏省: 48 条
  ...

共获取 1056 条记录
已保存: 长江经济带30年数据.xlsx
```

完成后，Excel 文件会保存在当前目录，每个指标对应两个 Sheet：
- `指标名_明细`：原始记录，每行一条数据
- `指标名_透视`：以年份为列的透视表，便于直接分析

---

## 命令一览

| 命令 | 说明 |
|------|------|
| `python nbs_scraper.py --init` | 生成默认配置文件 `config.json` |
| `python nbs_scraper.py` | 使用默认配置文件运行爬虫 |
| `python nbs_scraper.py --config my.json` | 指定自定义配置文件 |
| `python nbs_scraper.py --list-provinces` | 列出所有预设省份组及代码 |

---

## 常见问题

**请求超时 / 连接失败**
适当增大 `config.json` 中的 `delay` 值（建议不低于 2 秒），并检查网络是否正常。

**返回「无数据」**
确认 `time_range` 中的年份范围该省份确实有数据；部分指标在早年份可能缺失属正常现象。

**Excel 中没有透视表 Sheet**
当同一省份 + 指标组合存在重复行时透视会失败，明细 Sheet 仍会正常保存。
