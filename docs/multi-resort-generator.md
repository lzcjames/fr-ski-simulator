# 多雪场生成器：第一阶段

以前的 build_preview.py / expand_preview.py 仍保留，用于复现 v0.1/v0.2。新入口 build_game.py 将适配和多路线构建合并为一步，不再要求名称 Les Deux Alpes 或固定八条路线。所有游戏仍是工程测试版。

## 新增雪场

1. 新建 resorts/<slug>/config.json，参考现有 Les Deux Alpes 配置。
2. 根据真实地理资料确认 bbox（西、南、东、北）及 origin（经度、纬度）；不要直接复制其他雪场坐标。
3. 配置数据来源、输出网格间距、Skill 的固定 commit、最大候选路线数量。preview.primaryCourse 为 null 时按数据中的候选顺序选择首个符合旧主轴要求的未标记路线；已知主轴可显式指定。includeGradeReview 默认 false。
4. 在 Actions 选择 Generate resort preview，输入已存在的 slug。只构建数据时开启 data_only；生成 HTML 时需要先提供授权的 Avoriaz 离线模板。
5. 对每个雪场审核路线、地形边界、地标、场景、语言与浏览器行为。生成器不会自动从名称推断真实范围，也不会制造不存在的雪道。

## 本地复现

    python scripts/prepare_resort.py --config resorts/les-deux-alpes/config.json --skill .work/skill --work .work/data
    python scripts/build_game.py --config resorts/les-deux-alpes/config.json --template engine/avoriaz-offline.html --data .work/data/resort-data.json --out .work/les-deux-alpes.html

使用固定版本 Skill 和 Python 3.11、Pillow、Node 22。模板只读。新生成器仍通过代码锚点适配旧版 HTML；尚未提取成完全独立的通用引擎。存在剩余旧雪场逻辑和地形覆盖限制。不同名称的合成测试数据只用于验证代码通用性，不代表新雪场已经接入。最终还需要真实第二雪场、IGN 分层地形、双 GPU 后端和手机测试。
