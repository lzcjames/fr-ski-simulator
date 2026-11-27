# Vercel 发布

用户指定 Vercel 为在线发布目标。Stage verified Vercel website 工作流仅接收已经成功的三雪场 v2 大厅或四雪场完整集成产物，检查静态资源、文件哈希及引擎版本，再提交到独立 vercel-release 分支的 vercel-site 目录。不会将未通过测试的开发分支直接发布。Vercel 使用静态网站（无后端、无运行时密钥），内容哈希 assets 缓存一年，游戏页面及目录重新验证。首版仍为工程预览：v2.0 第一人称专项测试存在已知问题，Galibier-Thabor 和修复版本尚未全部验证，不纳入此次初始线上版。

后续更新需成功构建新的大厅，再手动触发 Stage verified Vercel website，传入成功 run ID。保留旧发布提交以便回退。Vercel 项目应使用 vercel-site 作为根目录，只部署 vercel-release 分支。实际公网地址和状态须以 Vercel 部署记录为准。
