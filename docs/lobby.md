# 统一游戏平台（第一阶段）

静态大厅由已通过浏览器测试的游戏构建产物生成，而不是下载未验证的最新文件。入口 index.html 提供原画质游戏、离线下载及独立的桌面轻量实验版链接。catalog.json 记录雪场、路线数、地形网格、文件大小、SHA-256 和测试状态。保留完整独立 HTML，因此不依赖 CDN，也不需要账号或后台。

当前默认来源为通过四项 IGN 手机模拟测试的 45505895867，以及通过双模式桌面测试的 45506525645。构建时核对横竖屏对应的游戏哈希、QA 报告、雪场配置及轻量版的数据一致性；未通过的文件不得进入目录。桌面轻量版不会替代已通过手机测试的原版。新增雪场需要配置及匹配的测试产物，不需要重写大厅。

在 GitHub Actions 运行 Build multi-resort lobby，下载 fr-ski-simulator-lobby ZIP，解压后打开 index.html。也可将整个目录发布到静态服务器。当前只生成并验证可部署产物，尚未验证 GitHub Pages 设置或部署公网网站。若需上线，在仓库 Settings → Pages → Source 选择 GitHub Actions，再手动运行 Publish validated lobby to GitHub Pages，输入成功的大厅构建 run ID。发布流程会检查来源工作流成功、master 分支和文件哈希，不会自动部署开发提交。在线共享引擎缓存仍是下一阶段，当前每个独立 HTML 保留引擎副本。

完整路线通关、物理设备、真实 GPU 性能及 WebGPU 仍未验证。测试产物有 14 天保留期，过期后须重新构建并传入新 run ID。
