# -*- coding: utf-8 -*-
"""GitHub 热门项目数据抓取 + 翻译模块。"""

import os
import time
from datetime import datetime, timedelta, timezone

import requests

GITHUB_API = "https://api.github.com/search/repositories"

# 主题关键词 → 中文分类名映射
TOPIC_CATEGORY_MAP = {
    "ai": "AI / 机器学习",
    "machine-learning": "AI / 机器学习",
    "deep-learning": "AI / 机器学习",
    "llm": "AI / 机器学习",
    "chatgpt": "AI / 机器学习",
    "gpt": "AI / 机器学习",
    "neural-network": "AI / 机器学习",
    "transformer": "AI / 机器学习",
    "rag": "AI / 机器学习",
    "agent": "AI / 机器学习",
    "llama": "AI / 机器学习",
    "stable-diffusion": "AI / 机器学习",
    "web": "Web 开发",
    "frontend": "Web 开发",
    "backend": "Web 开发",
    "react": "Web 开发",
    "vue": "Web 开发",
    "nextjs": "Web 开发",
    "api": "Web 开发",
    "database": "Web 开发",
    "cli": "工具 / CLI",
    "command-line": "工具 / CLI",
    "terminal": "工具 / CLI",
    "automation": "工具 / CLI",
    "devops": "工具 / CLI",
    "docker": "工具 / CLI",
    "kubernetes": "工具 / CLI",
    "game": "游戏 / 图形",
    "graphics": "游戏 / 图形",
    "shader": "游戏 / 图形",
    "webgl": "游戏 / 图形",
    "unity": "游戏 / 图形",
    "security": "安全 / 区块链",
    "crypto": "安全 / 区块链",
    "blockchain": "安全 / 区块链",
    "cryptography": "安全 / 区块链",
    "data": "数据 / 分析",
    "data-science": "数据 / 分析",
    "data-visualization": "数据 / 分析",
    "analytics": "数据 / 分析",
    "pandas": "数据 / 分析",
    "jupyter": "数据 / 分析",
    "education": "学习 / 文档",
    "tutorial": "学习 / 文档",
    "documentation": "学习 / 文档",
    "course": "学习 / 文档",
}


def fetch_trending_repos(days=7, language=None, per_page=30, token=None):
    """抓取最近 `days` 天内新建、按 star 数降序的仓库。"""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    query = f"created:>{since}"
    if language:
        query += f" language:{language}"

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": per_page,
    }
    resp = requests.get(GITHUB_API, headers=headers, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json().get("items", [])


def categorize_by_topic(topics):
    """根据仓库的 topics 列表推断中文分类名。"""
    for topic in topics:
        t = topic.lower()
        if t in TOPIC_CATEGORY_MAP:
            return TOPIC_CATEGORY_MAP[t]
    return "其他"


def repo_to_row(repo):
    """把 API 返回的原始仓库 dict 精简成展示用的一行。"""
    topics = repo.get("topics", []) or []
    return {
        "name": repo["full_name"],
        "stars": repo["stargazers_count"],
        "forks": repo["forks_count"],
        "language": repo.get("language") or "-",
        "created": repo["created_at"][:10],
        "description": (repo.get("description") or "").strip(),
        "description_cn": "",
        "topics": ", ".join(topics),
        "category": categorize_by_topic(topics),
        "url": repo["html_url"],
    }


GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"


def _translate_single(text, source="en", target="zh-CN"):
    """用 requests 直接调 Google Translate 免费接口翻译单条文本。"""
    if not text:
        return ""
    params = {
        "client": "gtx",
        "sl": source,
        "tl": target,
        "dt": "t",
        "q": text,
    }
    resp = requests.get(GOOGLE_TRANSLATE_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return "".join(part[0] for part in data[0] if part[0])


def translate_descriptions(descriptions):
    """批量把英文描述翻译成中文。直接调 Google Translate 免费接口（无需第三方包）。"""
    results = []
    for desc in descriptions:
        if not desc:
            results.append("")
            continue
        try:
            results.append(_translate_single(desc))
            time.sleep(0.3)
        except Exception:
            results.append(desc)
    return results


if __name__ == "__main__":
    items = fetch_trending_repos(days=7, per_page=5)
    for repo in items:
        row = repo_to_row(repo)
        print(f"{row['name']}  stars={row['stars']}  category={row['category']}  desc={row['description'][:60]}")
