# mediaforge 流水线

这个分支保留第二次开发成果：一个更实用的媒体规范化工具。

它不再提供多个散命令，而是围绕一个真实任务：

```text
normalize input -> normalized mp4 + cover + report
```

核心价值：

- 统一媒体输出规格。
- 抽取第一帧作为封面。
- 生成可供后端入库的 JSON 报告。
- 仍然覆盖 FFmpeg 五个常用库。
