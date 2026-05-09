# 视频批量加水印工具

批量为本地视频添加文字水印，内置 FFmpeg，支持 NVIDIA/Intel/AMD 显卡加速，无损画质输出，下载即用。

## 下载使用

前往 [Releases](../../releases) 页面下载 `视频加水印.exe`，双击即可运行，无需安装任何环境。

## 功能

- 批量拖拽添加视频（MP4 MKV MOV AVI WMV 等）
- 自定义字体（Arial / Segoe UI / Calibri）
- 水印位置、大小、颜色、透明度、边距全部可调
- 自动检测显卡硬件加速（NVIDIA / Intel / AMD），支持 RTX 50 系列
- 输出质量五档：极压 CRF35 / 压缩 CRF28 / 快速 CRF23 / 高质量 CRF18 / 近乎无损 CRF10
- 完成后拖入新文件自动清空旧记录
- 自定义输出目录和文件名前缀

## 运行环境

Windows 10/11 x64，无需安装 Python 或 FFmpeg。

## 开源声明

本软件内置 [FFmpeg](https://ffmpeg.org)，遵循 [GPL v3 许可证](https://www.gnu.org/licenses/gpl-3.0.html)。
FFmpeg 版权归其原作者所有。