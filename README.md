# GitHub 热门项目监视器

监视最近新创建、涨星最快的 GitHub 开源项目。

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 在线访问

部署在 Streamlit Community Cloud（免费）。

## 可选：提高 API 限流额度

设置环境变量 `GITHUB_TOKEN`（[点这里创建 Token](https://github.com/settings/tokens/new?scopes=repo)）：

- 匿名：60 次/小时
- 带 Token：5000 次/小时
