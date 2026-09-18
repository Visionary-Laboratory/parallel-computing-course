# 并行计算与算子编程 · 公开课程网站

本仓库发布课程概览、第一讲和第一讲术语索引。讲义支持连续阅读、逐页演示、交互图示与答案揭示。

网站：https://zzh-tech.github.io/parallel-computing-course/

## 发布

在仓库 Settings → Pages 中，将 Source 设为 **GitHub Actions**。推送到 `main` 后，工作流将 `site/` 发布为 GitHub Pages。

`site/` 是可独立托管的静态网站，不需要后端或数据库。页面与资源使用相对路径，可用于 GitHub 项目网站或自定义域名。

## 更新

日常修改在教师本地的课程编辑项目完成。运行 `pnpm pages:prepare` 重新生成此发布仓库，再在 GitHub Desktop 提交并推送。生成器保留本目录的 Git 历史，只更新经过筛选的公开文件。

此仓库不包含教师讲稿、备课备注、未公开讲次、连续练习、项目指南或完整课程源码。`release-manifest.json` 列出每次生成的文件与校验值。

## 本地查看

```sh
python3 -m http.server 4173 --directory site
```

打开 http://localhost:4173/ 。讲义快捷键：← / → 翻页或揭示答案，F 全屏。

## 引用

讲义中的参考文献与图表出处保留在对应页面的“来源与延伸阅读”中。第三方图像、论文与视频的权利归各自作者或权利人；引用说明不授予额外授权。
