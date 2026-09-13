from __future__ import annotations

from collections import defaultdict

# Primary categories answer a user's question: "What can this tool help me do?"
# Technical concepts such as Agent / MCP / RAG are deliberately kept as secondary tags.
CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("找论文 / 读论文", (
        "literature review", "paper search", "research paper", "academic paper", "scientific paper",
        "arxiv", "citation", "bibliography", "reference manager", "paper reading", "pdf reader",
        "semantic scholar", "scholar", "research assistant", "literature",
    )),
    ("写作 / 润色 / 翻译", (
        "writing assistant", "ai writer", "copywriting", "proofread", "proofreading", "grammar",
        "rewrite", "rewriting", "translation", "translator", "translate", "paraphrase", "markdown editor",
    )),
    ("PPT / 汇报", (
        "presentation", "powerpoint", "ppt", "slides", "slide deck", "keynote", "pitch deck",
    )),
    ("数据分析 / 可视化", (
        "data analysis", "data analyst", "data visualization", "visualisation", "visualization",
        "chart", "dashboard", "spreadsheet", "excel", "csv", "pandas", "business intelligence",
        "statistics", "statistical analysis",
    )),
    ("地图 / GIS / 遥感", (
        "geospatial", "gis", "geographic information", "remote sensing", "satellite imagery",
        "earth observation", "spatial analysis", "geography", "geopandas", "raster", "vector tile",
        "map generation", "mapping", "openstreetmap", "qgis", "arcgis",
    )),
    ("城市规划 / 建筑设计", (
        "urban planning", "city planning", "urban design", "architecture design", "architectural design",
        "building design", "floor plan", "site plan", "land use", "urban morphology", "smart city",
        "building energy", "city model", "urban analytics",
    )),
    ("生成图片 / 效果图", (
        "image generation", "text-to-image", "text to image", "image editing", "image editor",
        "diffusion", "stable diffusion", "flux", "inpainting", "outpainting", "photo generation",
        "rendering", "render image", "concept art", "comfyui",
    )),
    ("生成视频 / 动画", (
        "video generation", "text-to-video", "text to video", "image-to-video", "image to video",
        "video editing", "video editor", "animation generation", "ai video", "motion generation",
    )),
    ("AI 数字人 / 口播", (
        "digital human", "virtual human", "talking avatar", "talking head", "ai avatar", "video avatar",
        "lip sync", "lip-sync", "lipsync", "face animation", "portrait animation", "virtual presenter",
    )),
    ("3D 建模", (
        "3d generation", "text-to-3d", "text to 3d", "image-to-3d", "image to 3d", "3d model",
        "3d modeling", "3d reconstruction", "point cloud", "mesh generation", "blender", "cad", "bim",
    )),
    ("语音 / 会议转写", (
        "speech recognition", "speech-to-text", "speech to text", "transcription", "transcribe",
        "meeting assistant", "meeting notes", "whisper", "asr", "voice recognition", "audio transcription",
        "text-to-speech", "text to speech", "tts", "voice cloning",
    )),
    ("搜索 / 深度研究", (
        "deep research", "web research", "research agent", "web search", "ai search", "search engine",
        "answer engine", "internet research", "browser agent", "browse the web", "web browsing",
    )),
    ("聊天 / 知识问答", (
        "knowledge base", "question answering", "q&a", "chatbot", "chat assistant", "personal assistant",
        "document chat", "chat with pdf", "knowledge graph", "retrieval augmented", "retrieval-augmented",
        "vector database", " rag ",
    )),
    ("办公自动化", (
        "workflow automation", "office automation", "automation platform", "automate tasks", "productivity",
        "email assistant", "calendar assistant", "document automation", "no-code automation", "low-code automation",
        "n8n", "zapier", "browser automation", "desktop automation",
    )),
    ("编程 / 调试", (
        "coding agent", "code assistant", "ai coding", "code generation", "developer agent", "developer tools",
        "programming assistant", "code review", "codebase", "debugging", "debugger", "copilot", "ide",
        "claude code", "cursor", "codex",
    )),
    ("搭网站 / 应用", (
        "app builder", "website builder", "web app builder", "ui generator", "frontend generator",
        "full-stack app", "full stack app", "no-code app", "low-code app", "vibe coding", "prototype app",
    )),
    ("求职 / 简历", (
        "job search", "job hunting", "resume", "cv", "career", "interview prep", "interview preparation",
        "job application", "ats", "cover letter",
    )),
    ("本地 AI / 模型运行", (
        "local llm", "local-llm", "self hosted", "self-hosted", "run llm", "model serving", "inference server",
        "ollama", "llama.cpp", "vllm", "openai compatible", "openai-compatible", "local ai",
    )),
]

TECH_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Agent", ("agentic", "ai agent", "ai-agent", "multi-agent", "multi agent", "agent framework")),
    ("MCP", ("model context protocol", "mcp server", "mcp-server", " mcp ", "mcp-")),
    ("RAG", ("retrieval augmented", "retrieval-augmented", " rag ", "vector database")),
    ("LLM", ("large language model", " llm ", "llms", "language model")),
    ("多模态", ("multimodal", "multi-modal", "vision-language", "vlm")),
    ("本地运行", ("self-hosted", "self hosted", "local llm", "local-llm", "offline")),
]


def _score_rule(name: str, description: str, topics: list[str] | None, needles: tuple[str, ...]) -> int:
    name_l = f" {name.lower()} "
    desc_l = f" {(description or '').lower()} "
    topic_l = f" {' '.join(topics or []).lower()} "
    score = 0
    for needle in needles:
        n = needle.lower()
        # Name/topics are stronger evidence than a casual mention in the description.
        if n in name_l:
            score += 5
        if n in topic_l:
            score += 4
        if n in desc_l:
            score += 2
    return score


def categorize(name: str, description: str, topics: list[str] | None = None) -> str:
    scores: dict[str, int] = defaultdict(int)
    for category, needles in CATEGORY_RULES:
        scores[category] = _score_rule(name, description, topics, needles)
    best = max(scores.items(), key=lambda kv: kv[1], default=("其他实用 AI", 0))
    return best[0] if best[1] > 0 else "其他实用 AI"


def technical_tags(name: str, description: str, topics: list[str] | None = None) -> list[str]:
    haystack = " " + " ".join([name, description or "", " ".join(topics or [])]).lower() + " "
    result: list[str] = []
    for tag, needles in TECH_RULES:
        if any(needle.lower() in haystack for needle in needles):
            result.append(tag)
    return result[:4]
