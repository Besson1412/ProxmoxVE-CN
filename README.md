# Proxmox VE 社区助手脚本国内优化镜像

本项目为 [community-scripts/ProxmoxVE](https://github.com/community-scripts/ProxmoxVE) 的国内加速镜像与本地化增强版本。

每日通过 GitHub Actions 自动与上游保持同步更新，并自动化将官方源替换为国内中科大 (USTC) 高速镜像，同步推送到国内 GitCode 平台，让国内 Proxmox VE 节点能够极速、顺畅地执行一键配置与安装脚本。

---

## 🚀 极速一键使用

在刚安装完成的 Proxmox VE 节点的 Shell（SSH 终端或网页 Console）中直接复制执行以下命令：

### 推荐：GitCode 国内直连源（无需任何网络代理）
```bash
bash -c "$(curl -fsSL 'https://api.gitcode.com/api/v5/repos/Besson1412/ProxmoxVE-CN/raw/tools/pve/post-pve-install.sh?ref=main')"
```

### 备选：GitHub 加速代理通道
```bash
bash -c "$(curl -fsSL https://ghproxy.net/https://raw.githubusercontent.com/Besson1412/ProxmoxVE-CN/main/tools/pve/post-pve-install.sh)"
```

---

## ⚡ 本地化核心改造

1. **Debian APT 基础源加速**
   - 适配 PVE 8 (Debian 12 Bookworm) 与 PVE 9 (Debian 13 Trixie deb822 `.sources` 格式)。
   - 自动切换为中国科学技术大学 (USTC) 镜像：`mirrors.ustc.edu.cn/debian` 与 `debian-security`。

2. **Proxmox VE 软件源加速**
   - 自动禁用需要付费订阅的 `pve-enterprise` 企业源。
   - 自动开启并替换 `pve-no-subscription` 社区非订阅源为国内高速镜像。

3. **Ceph 存储组件源优化**
   - 包含 Ceph Quincy、Reef 等各版本组件源替换为 USTC 镜像。

4. **LXC / CT 容器模板下载加速（独家增强）**
   - 脚本集成 CT 模板下载源切换功能，可一键将 `/usr/share/perl5/PVE/APLInfo.pm` 中的模板下载地址切换为中科大源。
   - 彻底解决在 Proxmox VE 网页控制台下载 Debian、Ubuntu、Alpine 等容器系统模板极度缓慢的问题。

5. **网络防卡顿优化**
   - 针对国内网络环境下无法访问 `raw.githubusercontent.com` 的情况，对脚本中内置的 Telemetry 及远程依赖调用添加短超时保护，防止脚本启动时无响应等待 30 秒。

---

## 🔄 自动化同步与维护架构

```text
[上游社区仓库] community-scripts/ProxmoxVE
       │ 每日定时拉取 (GitHub Actions)
       ▼
[GitHub] Besson1412/ProxmoxVE-CN
  ├─ upstream 分支: 纯净保留上游原始代码，永不修改
  ├─ scripts/patch_cn.py: 自动化源替换与逻辑增强脚本
  └─ main 分支: 经过自动化流水线转换后的国内专属分支
       │
       ├─► 自动同步推送到国内 GitCode 仓库 (Besson1412/ProxmoxVE-CN)
       └─► 国内服务器无缝高速拉取执行
```

### 手动触发同步
在 GitHub 仓库页面进入 **Actions** -> 选择 **Sync Upstream and Patch CN** -> 点击 **Run workflow** 即可随时手动触发全量同步。

---

## 📜 许可证与致谢

- 原始脚本版权归 [community-scripts](https://github.com/community-scripts/ProxmoxVE) 及其贡献者所有，遵循 MIT 许可证。
- 感谢 [中国科学技术大学开源镜像站](https://mirrors.ustc.edu.cn/) 提供稳定的高速源支持。
