# -*- coding: utf-8 -*-
"""GitHub 热门项目监视器 —— 本地 Streamlit 应用。

运行方式:
    streamlit run app.py
"""

import os

import pandas as pd
import streamlit as st

from fetch import fetch_trending_repos, repo_to_row

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

st.set_page_config(page_title="GitHub 热门项目监视器", page_icon="🔥", layout="wide")

st.title("🔍 GitHub 热门项目监视器")
st.caption("监视最近一段时间新创建、涨星最快的开源项目，数据来自 GitHub Search API")


@st.cache_data(ttl=3600, show_spinner="正在拉取 GitHub 数据...")
def load(days, language, per_page, token):
    items = fetch_trending_repos(
        days=days, language=language or None, per_page=per_page, token=token or None
    )
    return pd.DataFrame([repo_to_row(r) for r in items])


# 侧边栏：筛选条件
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

    if GITHUB_TOKEN:
        st.success("已检测到 GITHUB_TOKEN，限流额度更高")
    else:
        st.info("未设置 GITHUB_TOKEN，匿名限流约 60 次/小时")
    if st.button("🔄 强制刷新", use_container_width=True):
        load.clear()

try:
    df = load(days, language, per_page, GITHUB_TOKEN)
except Exception as e:
    st.error(f"抓取失败：{e}")
    st.stop()

if df.empty:
    st.warning("没有找到符合条件的项目，试试放宽时间窗口或清除语言限制。")
    st.stop()

# 顶部统计
c1, c2, c3 = st.columns(3)
c1.metric("项目数", len(df))
c2.metric("总 Star 数", int(df["stars"].sum()))
c3.metric("最高 Star", int(df["stars"].max()))

st.dataframe(
    df,
    column_config={
        "name": st.column_config.TextColumn("项目", width="medium"),
        "url": st.column_config.LinkColumn("链接", width="small"),
        "stars": st.column_config.NumberColumn("Star", format="%d"),
        "forks": st.column_config.NumberColumn("Fork", format="%d"),
        "description": st.column_config.TextColumn("描述", width="large"),
        "topics": st.column_config.TextColumn("标签", width="medium"),
    },
    column_order=["name", "stars", "forks", "language", "created", "url", "description", "topics"],
    hide_index=True,
    use_container_width=True,
    height=620,
)
