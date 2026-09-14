# -*- coding: utf-8 -*-
"""GitHub 热门项目数据抓取模块。"""

import os
from datetime import datetime, timedelta, timezone

import requests

GITHUB_API = "https://api.github.com/search/repositories"


def fetch_trending_repos(days=7, language=None, per_page=30, token=None):
    """抓取最近 `days` 天内新建、按 star 数降序的仓库。

    参数:
        days: 往回看的窗口天数，对应搜索条件 created:>{date}
        language: 可选，限定主要语言（如 "python"、"go"）
        per_page: 返回条数（GitHub 上限 100）
        token: GitHub Personal Access Token；不传则匿名，限流约 60 次/小时

    返回:
        list[dict]: Search API 返回的 items 原始仓库信息
    """
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


def repo_to_row(repo):
    """把 API 返回的原始仓库 dict 精简成展示用的一行。"""
    return {
        "name": repo["full_name"],
        "stars": repo["stargazers_count"],
        "forks": repo["forks_count"],
        "language": repo.get("language") or "-",
        "created": repo["created_at"][:10],
        "description": (repo.get("description") or "").strip(),
        "topics": ", ".join(repo.get("topics", []) or []),
        "url": repo["html_url"],
    }


if __name__ == "__main__":
    # 直接运行本文件做冒烟测试，方便排查网络 / 限流问题
    items = fetch_trending_repos(days=7, per_page=5)
    for repo in items:
        row = repo_to_row(repo)
        print(f"{row['name']}  stars={row['stars']}  lang={row['language']}")
