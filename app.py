# -*- coding: utf-8 -*-
"""GitHub 热门项目监视器 —— 本地 Streamlit 应用。

功能:
- 按时间窗口/语言/条数筛选最近新建的高星项目
- 按领域分类浏览（AI、Web、工具、数据 等）
- 一键翻译英文描述为中文
"""

import os

import pandas as pd
import streamlit as st

from fetch import (
    fetch_trending_repos,
    repo_to_row,
    translate_descriptions,
)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

st.set_page_config(page_title="GitHub 热门项目监视器", page_icon="🔥", layout="wide")

st.title("🔍 GitHub 热门项目监视器")
st.caption("监视最近新创建、涨星最快的开源项目，支持分类浏览 + 中文翻译")


@st.cache_data(ttl=3600, show_spinner="正在拉取 GitHub 数据...")
def load(days, language, per_page, token):
    items = fetch_trending_repos(
        days=days, language=language or None, per_page=per_page, token=token or None
    )
    return pd.DataFrame([repo_to_row(r) for r in items])


@st.cache_data(ttl=7200, show_spinner="正在翻译描述...")
def translate_all(descriptions):
    return translate_descriptions(descriptions)


# ──────────────────────────────────────
# 侧边栏：筛选条件
# ──────────────────────────────────────
with st.sidebar:
    st.header("筛选条件")
    days = st.slider(
        "时间窗口（天）", min_value=1, max_value=30, value=7,
        help="只看最近 N 天内新创建的仓库",
    )
    language = st.text_input(
        "限定语言（留空则不限）", value="",
        help="例如 python / go / rust / typescript",
    )
    per_page = st.slider("展示条数", min_value=10, max_value=100, value=30, step=10)

    st.divider()
    translate_enabled = st.toggle("🌐 翻译描述为中文", value=True)

    if GITHUB_TOKEN:
        st.success("已检测到 GITHUB_TOKEN")
    else:
        st.info("未设置 GITHUB_TOKEN，匿名限流约 60 次/小时")
    if st.button("🔄 强制刷新", width="stretch"):
        load.clear()
        translate_all.clear()

# ──────────────────────────────────────
# 数据加载
# ──────────────────────────────────────
try:
    df = load(days, language, per_page, GITHUB_TOKEN)
except Exception as e:
    st.error(f"抓取失败：{e}")
    st.stop()

if df.empty:
    st.warning("没有找到符合条件的项目，试试放宽时间窗口或清除语言限制。")
    st.stop()

# 翻译
if translate_enabled and not df.empty:
    descriptions = df["description"].tolist()
    translations = translate_all(descriptions)
    df["description_cn"] = translations
else:
    df["description_cn"] = ""

# ──────────────────────────────────────
# 顶部统计
# ──────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("项目数", len(df))
c2.metric("总 Star 数", int(df["stars"].sum()))
c3.metric("最高 Star", int(df["stars"].max()))
top_cat = df["category"].value_counts().index[0] if len(df) > 0 else "-"
c4.metric("最热分类", top_cat)

# ──────────────────────────────────────
# 主区域：Tabs 切换视图
# ──────────────────────────────────────
tab_all, tab_cat, tab_lang = st.tabs(["📋 全部项目", "📂 按分类", "💻 按语言"])


def show_desc(row):
    """展示描述：有翻译时同时显示中英文。"""
    desc_en = row["description"]
    desc_cn = row["description_cn"]
    if desc_cn and desc_cn != desc_en:
        return f"{desc_cn}\n\n_{desc_en}_"
    return desc_en


# --- Tab 1: 全部项目 ---
with tab_all:
    display_df = df.copy()
    display_df["描述"] = display_df.apply(show_desc, axis=1)
    st.dataframe(
        display_df[["name", "stars", "forks", "language", "category", "created", "url", "描述", "topics"]],
        column_config={
            "name": st.column_config.TextColumn("项目", width="medium"),
            "url": st.column_config.LinkColumn("链接", width="small"),
            "stars": st.column_config.NumberColumn("⭐", format="%d"),
            "forks": st.column_config.NumberColumn("Fork", format="%d"),
            "language": st.column_config.TextColumn("语言", width="small"),
            "category": st.column_config.TextColumn("分类", width="small"),
            "描述": st.column_config.TextColumn("描述", width="large"),
            "topics": st.column_config.TextColumn("标签", width="medium"),
        },
        hide_index=True,
        use_container_width=True,
        height=600,
    )

# --- Tab 2: 按分类 ---
with tab_cat:
    cat_counts = df["category"].value_counts()
    for cat_name, count in cat_counts.items():
        sub_df = df[df["category"] == cat_name].sort_values("stars", ascending=False)
        with st.expander(f"{cat_name}（{count} 个项目）", expanded=True):
            for _, row in sub_df.iterrows():
                col_name, col_stars, col_lang = st.columns([4, 1, 1])
                col_name.markdown(f"**[{row['name']}]({row['url']})**")
                col_stars.metric("⭐", int(row["stars"]))
                col_lang.write(f"`{row['language']}`")
                desc_text = show_desc(row)
                if desc_text:
                    st.markdown(desc_text)
                if row["topics"]:
                    st.caption(f"🏷 {row['topics']}")
                st.divider()

# --- Tab 3: 按语言 ---
with tab_lang:
    lang_counts = df[df["language"] != "-"]["language"].value_counts()
    for lang_name, count in lang_counts.items():
        sub_df = df[df["language"] == lang_name].sort_values("stars", ascending=False)
        with st.expander(f"{lang_name}（{count} 个项目）", expanded=True):
            for _, row in sub_df.head(10).iterrows():
                col_name, col_stars, col_cat = st.columns([4, 1, 1])
                col_name.markdown(f"**[{row['name']}]({row['url']})**")
                col_stars.metric("⭐", int(row["stars"]))
                col_cat.write(f"`{row['category']}`")
                desc_text = show_desc(row)
                if desc_text:
                    st.markdown(desc_text)
                st.divider()
