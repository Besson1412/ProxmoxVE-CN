#!/usr/bin/env python3
"""
patch_cn.py: Proxmox VE 社区脚本国内源替换与本地化处理脚本
用于在同步上游代码后，自动批量替换源为国内镜像，并优化网络超时设置。
"""

import os
import re
import sys
from pathlib import Path

# 替换规则
REPLACEMENTS = [
    # 1. Proxmox PVE 软件源 -> 中科大 (USTC) 镜像
    (re.compile(r"https?://download\.proxmox\.com/debian/pve"), "https://mirrors.ustc.edu.cn/proxmox/debian/pve"),
    (re.compile(r"https?://enterprise\.proxmox\.com/debian/pve"), "https://mirrors.ustc.edu.cn/proxmox/debian/pve"),

    # 2. Ceph 源 -> 中科大 (USTC) 镜像
    (re.compile(r"https?://download\.proxmox\.com/debian/ceph-(quincy|reef)"), r"https://mirrors.ustc.edu.cn/proxmox/debian/ceph-\1"),
    (re.compile(r"https?://enterprise\.proxmox\.com/debian/ceph-(quincy|reef)"), r"https://mirrors.ustc.edu.cn/proxmox/debian/ceph-\1"),
    (re.compile(r"https?://download\.proxmox\.com/debian/\$\{CEPH_RELEASE\}"), "https://mirrors.ustc.edu.cn/proxmox/debian/${CEPH_RELEASE}"),
    (re.compile(r"https?://enterprise\.proxmox\.com/debian/\$\{CEPH_RELEASE\}"), "https://mirrors.ustc.edu.cn/proxmox/debian/${CEPH_RELEASE}"),

    # 3. Debian 官方源 -> 中科大 (USTC) 镜像
    (re.compile(r"https?://deb\.debian\.org/debian"), "https://mirrors.ustc.edu.cn/debian"),
    (re.compile(r"https?://security\.debian\.org/debian-security"), "https://mirrors.ustc.edu.cn/debian-security"),

    # 4. deb822 (PVE 8/9 sources 格式)
    (re.compile(r"URIs:\s*https?://deb\.debian\.org/debian"), "URIs: https://mirrors.ustc.edu.cn/debian"),
    (re.compile(r"URIs:\s*https?://security\.debian\.org/debian-security"), "URIs: https://mirrors.ustc.edu.cn/debian-security"),
    (re.compile(r"URIs:\s*https?://download\.proxmox\.com/debian/pve"), "URIs: https://mirrors.ustc.edu.cn/proxmox/debian/pve"),
    (re.compile(r"URIs:\s*https?://enterprise\.proxmox\.com/debian/pve"), "URIs: https://mirrors.ustc.edu.cn/proxmox/debian/pve"),
    (re.compile(r"URIs:\s*https?://download\.proxmox\.com/debian/\$\{CEPH_RELEASE\}"), "URIs: https://mirrors.ustc.edu.cn/proxmox/debian/${CEPH_RELEASE}"),

    # 5. 上游脚本递归引用的 GitHub Raw 链接 -> ghproxy 加速
    (re.compile(r"https://raw\.githubusercontent\.com/community-scripts/ProxmoxVE/main"), "https://ghproxy.net/https://raw.githubusercontent.com/Besson1412/ProxmoxVE-CN/main"),

    # 6. 核心 Telemetry/core URL 优化超时避免国内卡死
    (re.compile(r'curl -fsSL "\$\{COMMUNITY_SCRIPTS_CORE_URL:-https://raw\.githubusercontent\.com/community-scripts/core/main\}/api/api\.func"'),
     'curl -fsSL --connect-timeout 2 "${COMMUNITY_SCRIPTS_CORE_URL:-https://ghproxy.net/https://raw.githubusercontent.com/community-scripts/core/main}/api/api.func"'),
]

LXC_ROUTINE_SNIPPET = '''  CHOICE=$(whiptail --backtitle "Proxmox VE Helper Scripts" --title "LXC TEMPLATE MIRROR" --menu "Change Proxmox LXC Container Template download URL to USTC mirror?\\n \\nSpeed up downloading container templates (Ubuntu/Debian/Alpine) in China." 14 58 2 \\
    "yes" " " \\
    "no" " " 3>&2 2>&1 1>&3)
  case $CHOICE in
  yes)
    msg_info "Updating LXC Template Download Mirror"
    if [ -f /usr/share/perl5/PVE/APLInfo.pm ]; then
      sed -i.bak 's#http://download.proxmox.com/images#https://mirrors.ustc.edu.cn/proxmox/images#' /usr/share/perl5/PVE/APLInfo.pm
      systemctl restart pvedaemon.service || true
      msg_ok "Updated LXC Template Download Mirror to USTC"
    else
      msg_error "APLInfo.pm not found"
    fi
    ;;
  no) msg_error "Selected no to Updating LXC Template Mirror" ;;
  esac
'''

def patch_post_pve_install(filepath: Path):
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    # 检查是否已注入 LXC 模板加速逻辑
    if "LXC TEMPLATE MIRROR" not in content:
        target_marker = 'CHOICE=$(whiptail --backtitle "Proxmox VE Helper Scripts" --title "UPDATE"'
        if target_marker in content:
            # 注入在 UPDATE 选项之前
            content = content.replace(target_marker, LXC_ROUTINE_SNIPPET + "\n  " + target_marker)
            filepath.write_text(content, encoding="utf-8")
            print(f"Injected LXC mirror snippet into {filepath}")

def patch_file(filepath: Path) -> bool:
    try:
        content = filepath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, Exception):
        return False

    modified = content
    for pattern, repl in REPLACEMENTS:
        modified = pattern.sub(repl, modified)

    if modified != content:
        filepath.write_text(modified, encoding="utf-8")
        return True
    return False

def main():
    repo_root = Path(__file__).resolve().parent.parent
    print(f"Starting CN patch routine in: {repo_root}")

    # 特别针对 tools/pve/post-pve-install.sh 注入增强逻辑
    post_install_script = repo_root / "tools" / "pve" / "post-pve-install.sh"
    if post_install_script.exists():
        patch_post_pve_install(post_install_script)

    # 清理上游专用的 PocketBase / Bot 等无效流水线，避免 Actions 报错
    workflows_dir = repo_root / ".github" / "workflows"
    if workflows_dir.exists():
        for wf in workflows_dir.glob("*"):
            if wf.name != "sync-upstream.yml":
                wf.unlink()
                print(f"Removed upstream bot workflow: {wf.name}")

    target_extensions = {".sh", ".func", ".py", ".md", ".json"}
    target_dirs = ["tools", "ct", "install", "misc", "turnkey", "vm"]

    patched_count = 0
    for target_dir in target_dirs:
        dir_path = repo_root / target_dir
        if not dir_path.exists():
            continue
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in target_extensions:
                if patch_file(file_path):
                    patched_count += 1

    print(f"Finished. Successfully patched {patched_count} files.")

if __name__ == "__main__":
    main()
