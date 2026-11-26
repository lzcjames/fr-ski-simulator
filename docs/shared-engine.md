# 在线共享引擎（大厅 v0.2）

基于通过测试的独立 HTML，不改变原有游戏的渲染、物理、数据或离线文件。构建器把完全相同的 CSS（内嵌字体）、启动辅助 JavaScript 和主引擎 JavaScript 提取为内容寻址文件，保留雪场独立的 FR_RESORT 和 AVZ_DATA。每个资源名包含完整 SHA-256。重新构建可精确还原原始 HTML，并核对离线游戏哈希。

大厅保留开始滑雪、离线下载、桌面轻量实验入口；额外增加在线共享引擎版。在线版应从 HTTP(S) 静态服务打开，独立 HTML 仍可离线使用。不会在大厅一次性加载所有游戏；玩家选择后才加载该雪场。新雪场如果使用相同引擎则自动复用资源，若引擎版本改变则自动获得不同哈希文件名。

本地：`python scripts/build_shared_site.py --input extracted-lobby --out .work/online-site`。以静态 HTTP 服务访问生成目录。建议对 assets/ 下的内容哈希资源设置 Cache-Control: public, max-age=31536000, immutable；HTML 和 catalog 应短缓存或重新验证。GitHub Pages 的实际缓存策略取决于托管服务，不保证一年缓存头。

验证：Shared online engine cache 工作流只接受成功的大厅构建，检查精确拆分、静态链接、资源哈希和 JS 语法。通过真实 HTTP 服务在同一 Chromium profile 中依次打开两座雪场，检测 WebGL2 就绪、基础控制以及第二座雪场是否重新请求共享资源；未通过时不上传可部署站点。报告区分服务端响应体字节与浏览器 Resource Timing，不宣称节省同等数量的压缩网络流量。没有修改已验证的手动 Pages 发布流程；共享版仍为待验证实验，未发布到公网。

仍需要实机 GPU、WebGPU、完整路线滑行与实际托管缓存测试。原版离线文件以及实验轻量版仍保留，因此整个下载 ZIP 不一定更小，收益在于在线切换雪场。