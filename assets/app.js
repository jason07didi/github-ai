const state = {
  projects: [],
  status: null,
  query: "",
  category: "全部",
  sort: "score",
};

const fmt = new Intl.NumberFormat("zh-CN", { notation: "compact", maximumFractionDigits: 1 });

function escapeHtml(value = "") {
  return String(value).replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
}

function safeUrl(value = "") {
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : "";
  } catch {
    return "";
  }
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

function renderCategories() {
  const select = document.querySelector("#category");
  const categories = [...new Set(state.projects.map(p => p.category).filter(Boolean))].sort();
  select.innerHTML = `<option value="全部">全部分类</option>` + categories.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
}

function renderStats() {
  document.querySelector("#projectCount").textContent = state.projects.length;
  document.querySelector("#lastUpdated").textContent = state.status?.last_updated
    ? new Date(state.status.last_updated).toLocaleString("zh-CN", { hour12: false })
    : "等待首次更新";
}

function filteredProjects() {
  const q = state.query.trim().toLowerCase();
  let items = state.projects.filter(p => {
    const inCategory = state.category === "全部" || p.category === state.category;
    const haystack = [p.name, p.repo, p.description_zh, p.description_en, ...(p.topics || [])].join(" ").toLowerCase();
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

function render() {
  const grid = document.querySelector("#grid");
  const items = filteredProjects();
  document.querySelector("#visibleCount").textContent = items.length;

  if (!items.length) {
    grid.innerHTML = `<div class="empty">没有符合条件的项目。可以修改关键词或分类。</div>`;
    return;
  }

  grid.innerHTML = items.map(p => {
    const tags = (p.topics || []).slice(0, 5).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join("");
    const zh = p.description_zh || p.description_en || "暂无简介";
    const sameAsEnglish = p.description_zh && p.description_en && p.description_zh === p.description_en;
    const repoUrl = safeUrl(p.url);
    const homepageUrl = safeUrl(p.homepage);
    return `
      <article class="card">
        <div class="card-top">
          <div>
            <div class="category">${escapeHtml(p.category || "其他 AI")}</div>
            <h2>${escapeHtml(p.name)}</h2>
            <div class="repo">${escapeHtml(p.repo)}</div>
          </div>
          <div class="score" title="综合热度评分"><strong>${Number(p.score || 0).toFixed(1)}</strong><span>热度</span></div>
        </div>

        <p class="desc">${escapeHtml(zh)}</p>
        ${sameAsEnglish ? `<p class="translation-note">本次免费翻译不可用，暂显示英文；下次更新会继续尝试。</p>` : ""}

        <div class="metrics">
          <span class="metric">★ ${fmt.format(p.stars)}</span>
          <span class="metric">⑂ ${fmt.format(p.forks)}</span>
          ${growthBadge(p.growth_24h, "24h")}
          ${growthBadge(p.growth_7d, "7d")}
        </div>

        <div class="tags">${tags || `<span class="tag">${escapeHtml(p.language || "Unknown")}</span>`}</div>

        <div class="meta">
          <span>${escapeHtml(p.language || "Unknown")}</span>
          <span>${escapeHtml(p.license || "Unknown")}</span>
          <span>代码 ${relativeTime(p.pushed_at)}更新</span>
        </div>

        <div class="actions">
          ${repoUrl ? `<a href="${escapeHtml(repoUrl)}" target="_blank" rel="noopener noreferrer">GitHub ↗</a>` : ""}
          ${homepageUrl ? `<a class="secondary" href="${escapeHtml(homepageUrl)}" target="_blank" rel="noopener noreferrer">项目主页 ↗</a>` : ""}
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
    renderCategories();
    renderStats();
    render();
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
