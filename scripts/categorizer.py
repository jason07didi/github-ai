from __future__ import annotations

CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("MCP", ("model context protocol", "mcp server", "mcp-server", " mcp ", "mcp-")),
    ("AI 编程", ("coding agent", "code assistant", "copilot", "developer agent", "ai coding", "code generation", "ide")),
    ("AI Agent", ("agentic", "multi-agent", "multi agent", "ai agent", "agents", "autonomous agent")),
    ("RAG / 知识库", ("retrieval augmented", "retrieval-augmented", " rag ", "vector database", "knowledge base")),
    ("科研 AI", ("research agent", "deep research", "scientific", "paper", "literature", "academic")),
    ("图像", ("image generation", "text-to-image", "diffusion", "computer vision", "image editing")),
    ("视频", ("video generation", "text-to-video", "video editing", "video ai")),
    ("语音 / 音频", ("speech", "voice", "audio", "text-to-speech", "tts", "asr")),
    ("多模态", ("multimodal", "multi-modal", "vision-language", "vlm")),
    ("LLM 工具", ("large language model", " llm ", "llms", "language model", "chatbot")),
]


def categorize(name: str, description: str, topics: list[str] | None = None) -> str:
    haystack = " " + " ".join([name, description or "", " ".join(topics or [])]).lower() + " "
    for category, needles in CATEGORY_RULES:
        if any(needle in haystack for needle in needles):
            return category
    return "其他 AI"
