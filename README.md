# 视频批量加水印工具

批量为本地视频添加文字水印，支持 NVIDIA/Intel/AMD 显卡加速，无损画质输出。

## 使用前提

- Python 3.10+
- FFmpeg（下载后放到程序同目录）

## 安装依赖

```bash
pip install PyQt6
```

## 运行

```bash
pythonw video_watermark.py
```

## 功能

- 批量拖拽添加视频（MP4 MKV MOV AVI 等）
- 自定义字体（Arial / Segoe UI / Calibri）
- 水印位置、大小、颜色、透明度、边距全部可调
- 自动检测显卡硬件加速
- 输出质量三档（快速 / 高质量 / 近乎无损）
- 自定义输出目录和文件名前缀
