# V2 升级说明

本升级解决两个问题：

1. **主分类改成普通用户能理解的“任务/用途分类”**，例如“地图 / GIS / 遥感”“找论文 / 读论文”“AI 数字人 / 口播”。Agent、MCP、RAG 等只作为二级技术标签。
2. **项目卡片加入核心图片**：优先从项目 README 中挑选截图、Banner、Demo、Preview 等图片；自动过滤 shields/badge；没有合适图片时使用项目头像或用途图标兜底。

同时扩大搜索池并对分类做数量平衡，避免首页被 AI 编程项目占满。

## 上传

把本压缩包中的内容覆盖到仓库根目录对应路径。`scripts/covers.py` 是新增文件，其余为替换文件。提交后在 Actions 中手动运行一次 `Update AI Radar and deploy Pages`。

第一次 V2 运行会为已收录项目读取 README 图片，因此 API 请求会比后续多，但仍在正常公开仓库使用范围内。图片 URL 会缓存到 `data/projects.json`，不会每 30 分钟重复读取 README。
