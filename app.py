# -*- coding: utf-8 -*-
"""GitHub 热门项目监视器 —— 本地 Streamlit 应用。

功能:
- 按时间窗口/语言/条数筛选最近新建的高星项目
- 按领域分类浏览（AI、Web、工具、数据 等）
- 描述和标签可选中文/英文/双语显示
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
st.caption("监视最近新创建、涨星最快的开源项目，支持分类浏览 + 中英文切换")


@st.cache_data(ttl=3600, show_spinner="正在拉取 GitHub 数据...")
def load(days, language, per_page, token):
    items = fetch_trending_repos(
        days=days, language=language or None, per_page=per_page, token=token or None
    )
    return pd.DataFrame([repo_to_row(r) for r in items])


@st.cache_data(ttl=7200, show_spinner="正在翻译描述...")
def translate_all(descriptions):
    return translate_descriptions(descriptions)


@st.cache_data(ttl=7200, show_spinner="正在翻译标签...")
def translate_topics_all(topics_list):
    """批量翻译标签列表，每个标签独立翻译后返回。"""
    unique_topics = set()
    for t in topics_list:
        for tag in str(t).split(", "):
            tag = tag.strip()
            if tag:
                unique_topics.add(tag)
    translations = {}
    if unique_topics:
        results = translate_descriptions(list(unique_topics))
        for orig, tr in zip(sorted(unique_topics), results):
            translations[orig] = tr
    translated_list = []
    for t in topics_list:
        parts = []
        for tag in str(t).split(", "):
            tag = tag.strip()
            if not tag:
                continue
            parts.append(translations.get(tag, tag))
        translated_list.append(", ".join(parts))
    return translated_list


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
    st.subheader("显示语言")
    desc_lang = st.selectbox(
        "📝 描述显示",
        options=["双语", "中文", "英文"],
        index=0,
        help="选择项目描述的显示语言",
    )
    tag_lang = st.selectbox(
        "🏷 标签显示",
        options=["双语", "中文", "英文"],
        index=2,
        help="选择标签的显示语言",
    )

    need_translate = "中文" in (desc_lang, tag_lang) or "双语" in (desc_lang, tag_lang)

    if GITHUB_TOKEN:
        st.success("已检测到 GITHUB_TOKEN")
    else:
        st.info("未设置 GITHUB_TOKEN，匿名限流约 60 次/小时")
    if st.button("🔄 强制刷新", width="stretch"):
        load.clear()
        translate_all.clear()
        translate_topics_all.clear()

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

# 翻译（按需触发）
if need_translate:
    if "中文" in desc_lang or "双语" in desc_lang:
        df["description_cn"] = translate_all(df["description"].tolist())
    else:
        df["description_cn"] = ""
    if "中文" in tag_lang or "双语" in tag_lang:
        df["topics_cn"] = translate_topics_all(df["topics"].tolist())
    else:
        df["topics_cn"] = ""
else:
    df["description_cn"] = ""
    df["topics_cn"] = ""


def show_desc(row):
    """根据用户选择的语言偏好返回描述文本。"""
    desc_en = row["description"]
    desc_cn = row["description_cn"]
    if desc_lang == "中文" and desc_cn:
        return desc_cn
    if desc_lang == "双语" and desc_cn and desc_cn != desc_en:
        return f"{desc_cn}\n\n_{desc_en}_"
    return desc_en


def show_topics(row):
    """根据用户选择的语言偏好返回标签文本。"""
    topics_en = row["topics"]
    topics_cn = row["topics_cn"]
    if tag_lang == "中文" and topics_cn:
        return topics_cn
    if tag_lang == "双语" and topics_cn and topics_cn != topics_en:
        return f"{topics_cn} / {topics_en}"
    return topics_en


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

# --- Tab 1: 全部项目 ---
with tab_all:
    display_df = df.copy()
    display_df["描述"] = display_df.apply(show_desc, axis=1)
    display_df["标签"] = display_df.apply(show_topics, axis=1)
    st.dataframe(
        display_df[["name", "stars", "forks", "language", "category", "created", "url", "描述", "标签"]],
        column_config={
            "name": st.column_config.TextColumn("项目", width="medium"),
            "url": st.column_config.LinkColumn("链接", width="small"),
            "stars": st.column_config.NumberColumn("⭐", format="%d"),
            "forks": st.column_config.NumberColumn("Fork", format="%d"),
            "language": st.column_config.TextColumn("语言", width="small"),
            "category": st.column_config.TextColumn("分类", width="small"),
            "描述": st.column_config.TextColumn("描述", width="large"),
            "标签": st.column_config.TextColumn("标签", width="medium"),
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
                topics_text = show_topics(row)
                if topics_text:
                    st.caption(f"🏷 {topics_text}")
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
                topics_text = show_topics(row)
                if topics_text:
                    st.caption(f"🏷 {topics_text}")
                st.divider()
