# AI 开源雷达

一个完全托管在 GitHub 上的中文 AI 工具发现页：定时搜索公开 GitHub 仓库、自动记录 Star 变化、用本地开源模型翻译项目简介，并通过 GitHub Pages 发布。

## 特点

- 不需要服务器
- 不需要付费 API Key
- 使用仓库自带的 `GITHUB_TOKEN`
- GitHub Actions 每 30 分钟尝试更新一次
- 新项目/简介变化时才重新翻译，避免重复计算
- 保存约 15 天 Star 快照，可计算 24h / 7d 增长
- GitHub Pages 中文网页，支持搜索、分类与排序

## 1. 创建仓库

1. 在 GitHub 新建一个 **Public** 仓库，例如 `ai-tools-radar`。
2. 把本项目全部文件上传到仓库根目录。
3. 确保默认分支名称是 `main`。

## 2. 打开 GitHub Pages

进入：

`Settings → Pages → Build and deployment → Source → GitHub Actions`

无需填写自定义域名。

## 3. 首次运行

进入：

`Actions → Update AI Radar and deploy Pages → Run workflow`

第一次运行需要下载免费翻译模型，因此会比后续运行更慢。成功后，Actions 页面中的 deploy 步骤会显示站点 URL，通常形如：

`https://你的用户名.github.io/ai-tools-radar/`

## 4. 修改抓取规则

编辑根目录的 `config.json`：

- `min_stars`：最低 Star 数
- `max_projects`：页面最多保留多少项目
- `new_repo_days`：额外扫描最近多少天新建的 AI 仓库
- `queries`：GitHub Search 查询词
- `translation_model`：本地翻译模型

## 5. 更新频率

`.github/workflows/update-and-deploy.yml` 当前使用：

```yaml
schedule:
  - cron: "7,37 * * * *"
```

也就是每小时第 7 分和第 37 分尝试运行，约每 30 分钟一次。

## 6. 本地调试（可选）

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 建议设置 GitHub Token，否则匿名 API 限额更低
export GITHUB_TOKEN=你的token
python scripts/update.py
python -m http.server 8000
```

然后打开 `http://localhost:8000`。

## 数据说明

`data/projects.json`：当前页面项目数据。  
`data/history.json`：Star 历史快照。  
`data/status.json`：最后更新时间等状态。

## 免费性的边界

本项目没有付费服务依赖。对于 GitHub Free 用户，公开仓库可以使用 GitHub Pages；公开仓库上的标准 GitHub-hosted Actions runner 也不按私有仓库分钟额度计费。GitHub 对 API 和 Actions 仍有公平使用、速率限制与平台规则，因此“免费”不等于无限资源。

另外，GitHub 可能对长期没有仓库活动的公开仓库自动停用 scheduled workflow；如果遇到这种情况，在 Actions 页面重新启用即可。
