const state = {
  projects: [],
  status: null,
  query: "",
  category: "全部",
  sort: "score",
};

const CATEGORY_ORDER = [
  "找论文 / 读论文",
  "写作 / 润色 / 翻译",
  "PPT / 汇报",
  "数据分析 / 可视化",
  "地图 / GIS / 遥感",
  "城市规划 / 建筑设计",
  "生成图片 / 效果图",
  "生成视频 / 动画",
  "AI 数字人 / 口播",
  "3D 建模",
  "语音 / 会议转写",
  "搜索 / 深度研究",
  "聊天 / 知识问答",
  "办公自动化",
  "编程 / 调试",
  "搭网站 / 应用",
  "求职 / 简历",
  "本地 AI / 模型运行",
  "其他实用 AI",
];

const CATEGORY_ICON = {
  "找论文 / 读论文": "📚",
  "写作 / 润色 / 翻译": "✍️",
  "PPT / 汇报": "🖥️",
  "数据分析 / 可视化": "📊",
  "地图 / GIS / 遥感": "🗺️",
  "城市规划 / 建筑设计": "🏙️",
  "生成图片 / 效果图": "🖼️",
  "生成视频 / 动画": "🎬",
  "AI 数字人 / 口播": "🧑‍💻",
  "3D 建模": "🧊",
  "语音 / 会议转写": "🎙️",
  "搜索 / 深度研究": "🔎",
  "聊天 / 知识问答": "💬",
  "办公自动化": "⚙️",
  "编程 / 调试": "💻",
  "搭网站 / 应用": "🧩",
  "求职 / 简历": "💼",
  "本地 AI / 模型运行": "🏠",
  "其他实用 AI": "✨",
};

const fmt = new Intl.NumberFormat("zh-CN", { notation: "compact", maximumFractionDigits: 1 });

function escapeHtml(value = "") {
  return String(value).replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
}
function safeUrl(value = "") {
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : "";
  } catch { return ""; }
}
function relativeTime(iso) {
  if (!iso) return "未知";
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 3600) return `${Math.max(1, Math.floor(seconds / 60))} 分钟前`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`;
  const days = Math.floor(seconds / 86400);
  if (days < 30) return `${days} 天前`;
  return new Date(iso).toLocaleDateString("zh-CN");
}
function growthBadge(value, label) {
  if (value === null || value === undefined) return `<span class="metric muted">${label} 积累中</span>`;
  return `<span class="metric hot">${label} +${fmt.format(value)}</span>`;
}
function categoryLabel(category) {
  return `${CATEGORY_ICON[category] || "✨"} ${category || "其他实用 AI"}`;
}
function renderCategories() {
  const select = document.querySelector("#category");
  const present = new Set(state.projects.map(p => p.category).filter(Boolean));
  const ordered = CATEGORY_ORDER.filter(c => present.has(c));
  for (const c of [...present].sort()) if (!ordered.includes(c)) ordered.push(c);
  select.innerHTML = `<option value="全部">全部用途</option>` + ordered.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(categoryLabel(c))}</option>`).join("");
}
function renderStats() {
  document.querySelector("#projectCount").textContent = state.projects.length;
  document.querySelector("#lastUpdated").textContent = state.status?.last_updated
    ? new Date(state.status.last_updated).toLocaleString("zh-CN", { hour12: false })
    : "等待首次更新";
}
function filteredProjects() {
  const q = state.query.trim().toLowerCase();
  const items = state.projects.filter(p => {
    const inCategory = state.category === "全部" || p.category === state.category;
    const haystack = [p.name, p.repo, p.category, p.description_zh, p.description_en, ...(p.tech_tags || []), ...(p.topics || [])].join(" ").toLowerCase();
    return inCategory && (!q || haystack.includes(q));
  });
  const sorters = {
    score: (a,b) => b.score - a.score,
    stars: (a,b) => b.stars - a.stars,
    growth24: (a,b) => (b.growth_24h ?? -1) - (a.growth_24h ?? -1),
    growth7: (a,b) => (b.growth_7d ?? -1) - (a.growth_7d ?? -1),
    updated: (a,b) => new Date(b.pushed_at) - new Date(a.pushed_at),
    new: (a,b) => new Date(b.discovered_at) - new Date(a.discovered_at),
  };
  return items.sort(sorters[state.sort] || sorters.score);
}
function renderCover(p) {
  const cover = safeUrl(p.cover_image);
  const fallback = safeUrl(p.owner_avatar);
  const icon = CATEGORY_ICON[p.category] || "✨";
  if (cover) {
    return `<div class="cover"><img src="${escapeHtml(cover)}" alt="${escapeHtml(p.name)} 项目预览" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentElement.classList.add('broken');this.remove()"><div class="cover-fallback">${icon}</div></div>`;
  }
  if (fallback) {
    return `<div class="cover cover-avatar"><img src="${escapeHtml(fallback)}" alt="${escapeHtml(p.name)}" loading="lazy"><div class="cover-fallback">${icon}</div></div>`;
  }
  return `<div class="cover broken"><div class="cover-fallback">${icon}</div></div>`;
}
function render() {
  const grid = document.querySelector("#grid");
  const items = filteredProjects();
  document.querySelector("#visibleCount").textContent = items.length;
  if (!items.length) {
    grid.innerHTML = `<div class="empty">没有符合条件的项目。可以修改关键词或用途分类。</div>`;
    return;
  }
  grid.innerHTML = items.map(p => {
    const techTags = (p.tech_tags || []).slice(0, 4).map(t => `<span class="tag tech">${escapeHtml(t)}</span>`).join("");
    const topicTags = (p.topics || []).slice(0, Math.max(0, 4 - (p.tech_tags || []).length)).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join("");
    const zh = p.description_zh || p.description_en || "暂无简介";
    const sameAsEnglish = p.description_zh && p.description_en && p.description_zh === p.description_en;
    const repoUrl = safeUrl(p.url);
    const homepageUrl = safeUrl(p.homepage);
    return `
      <article class="card">
        ${renderCover(p)}
        <div class="card-body">
          <div class="card-top">
            <div class="title-area">
              <div class="category">${escapeHtml(categoryLabel(p.category))}</div>
              <h2>${escapeHtml(p.name)}</h2>
              <div class="repo">${escapeHtml(p.repo)}</div>
            </div>
            <div class="score" title="综合热度评分"><strong>${Number(p.score || 0).toFixed(1)}</strong><span>热度</span></div>
          </div>
          <p class="desc">${escapeHtml(zh)}</p>
          ${sameAsEnglish ? `<p class="translation-note">本次免费翻译不可用，暂显示英文；后续更新会继续尝试。</p>` : ""}
          <div class="metrics">
            <span class="metric">★ ${fmt.format(p.stars)}</span>
            <span class="metric">⑂ ${fmt.format(p.forks)}</span>
            ${growthBadge(p.growth_24h, "24h")}
            ${growthBadge(p.growth_7d, "7d")}
          </div>
          <div class="tags">${techTags}${topicTags || (!techTags ? `<span class="tag">${escapeHtml(p.language || "Unknown")}</span>` : "")}</div>
          <div class="meta"><span>${escapeHtml(p.language || "Unknown")}</span><span>${escapeHtml(p.license || "Unknown")}</span><span>代码 ${relativeTime(p.pushed_at)}更新</span></div>
          <div class="actions">
            ${repoUrl ? `<a href="${escapeHtml(repoUrl)}" target="_blank" rel="noopener noreferrer">GitHub ↗</a>` : ""}
            ${homepageUrl ? `<a class="secondary" href="${escapeHtml(homepageUrl)}" target="_blank" rel="noopener noreferrer">项目主页 ↗</a>` : ""}
          </div>
        </div>
      </article>`;
  }).join("");
}
async function load() {
  const nonce = Date.now();
  try {
    const [projectsResponse, statusResponse] = await Promise.all([
      fetch(`./data/projects.json?v=${nonce}`),
      fetch(`./data/status.json?v=${nonce}`),
    ]);
    if (!projectsResponse.ok) throw new Error(`projects.json: ${projectsResponse.status}`);
    state.projects = await projectsResponse.json();
    state.status = statusResponse.ok ? await statusResponse.json() : null;
    renderCategories(); renderStats(); render();
  } catch (error) {
    console.error(error);
    document.querySelector("#grid").innerHTML = `<div class="empty">数据加载失败，请稍后刷新页面。</div>`;
  }
}
document.querySelector("#search").addEventListener("input", e => { state.query = e.target.value; render(); });
document.querySelector("#category").addEventListener("change", e => { state.category = e.target.value; render(); });
document.querySelector("#sort").addEventListener("change", e => { state.sort = e.target.value; render(); });
load();
setInterval(load, 5 * 60 * 1000);
