# PythonMinecraftLauncher

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/lijiayuapp/PythonMinecraftLauncher.svg)](https://github.com/lijiayuapp/PythonMinecraftLauncher/stargazers)

## ✨ 项目简介

**PythonMinecraftLauncher** 是一个基于 Python 开发的高度可扩展 Minecraft 版本下载器和启动器库。提供多线程下载、版本过滤、进度跟踪、正版认证等高级功能，让 Minecraft 游戏管理变得更加简单高效。

## 🚀 主要特性

- 🚀 **多线程下载** - 支持多线程并发下载，大幅提升下载速度
- 📦 **完整版本管理** - 支持下载客户端、资源文件、库文件等完整组件
- 🔍 **智能版本过滤** - 按版本类型（正式版、快照版、历史版本）筛选
- 📊 **实时进度跟踪** - 详细的下载进度和速度显示
- 🛡️ **文件完整性验证** - 自动验证文件 SHA1 校验和
- 🎮 **内置启动器** - 支持在线/离线模式启动游戏
- 🔐 **正版认证** - 完整的微软账户认证流程
- 🖥️ **跨平台支持** - 支持 Windows、Linux、macOS 系统
- ⚡ **高度可配置** - 灵活的下载配置和自定义选项

## 📥 安装指南

### 前提条件

- **Python 3.7** 或更高版本
- 稳定的网络连接
- Java 8 或更高版本（用于启动游戏）

### 安装步骤

1. **克隆仓库或下载源代码**
```bash
git clone https://github.com/lijiayuapp/PythonMinecraftLauncher.git
cd PythonMinecraftLauncher
```

2. **安装依赖**
```bash
pip install requests
```

## 🎯 快速开始

### 基本用法

```python
from minecraft_downloader import MinecraftDownloader, MinecraftLauncher, DownloadConfig, VersionType
from minecraft_auth import MinecraftAuthenticator, AuthConfig

# 创建下载配置
config = DownloadConfig(
    max_workers=10,
    download_dir="./minecraft"
)

# 创建下载器
downloader = MinecraftDownloader(config)

# 设置进度回调
def progress_callback(message, current=None, total=None):
    if current and total:
        print(f"\r{message} ({current}/{total})", end="", flush=True)
    else:
        print(message)

downloader.set_progress_callback(progress_callback)

# 获取版本列表
versions = downloader.get_version_list(
    version_type=VersionType.RELEASE,
    limit=5
)

# 下载最新版本
if versions:
    latest_version = versions[0]
    success = downloader.download_version(latest_version)
    
    if success:
        # 创建启动器
        launcher = MinecraftLauncher(downloader)
        
        # 创建认证器（Azure应用客户端ID）
        auth_config = AuthConfig(client_id="your-client-id")
        auth = MinecraftAuthenticator(auth_config)
        
        # 在线模式启动
        if auth.is_logged_in():
            launch_args = auth.get_launch_arguments()
            launcher.launch_with_auth(
                version_id=latest_version.id,
                auth_args=launch_args,
                memory="4G"
            )
        else:
            # 离线模式启动
            offline_args = auth.get_offline_arguments("Player")
            launcher.launch_with_auth(
                version_id=latest_version.id,
                auth_args=offline_args,
                memory="4G"
            )
```

## 📚 核心模块

### `minecraft_downloader.py` - 下载与启动模块

负责 Minecraft 版本的下载、管理和启动功能。

#### 主要类：

1. **`MinecraftDownloader`** - 核心下载器
   - `get_version_list()` - 获取可用版本列表
   - `get_version_info()` - 获取特定版本信息
   - `download_version()` - 下载完整版本
   - `set_progress_callback()` - 设置下载进度回调

2. **`MinecraftLauncher`** - 游戏启动器
   - `get_installed_versions()` - 查看已安装版本
   - `launch_with_auth()` - 使用认证参数启动游戏
   - `generate_launch_script()` - 生成启动脚本

3. **`DownloadConfig`** - 下载配置
   ```python
   config = DownloadConfig(
       max_workers=10,     # 并发线程数
       download_dir="./minecraft",  # 游戏目录
       chunk_size=1048576, # 分块大小（1MB）
       timeout=30,         # 超时时间
       max_retries=3       # 最大重试次数
   )
   ```

#### 版本类型：
- `VersionType.RELEASE` - 正式版
- `VersionType.SNAPSHOT` - 快照版
- `VersionType.OLD_BETA` - 历史测试版
- `VersionType.OLD_ALPHA` - 历史Alpha版
- `VersionType.ALL` - 所有版本

### `minecraft_auth.py` - 正版认证模块

提供完整的微软账户认证流程，支持在线和离线模式。

#### 主要类：

1. **`MinecraftAuthenticator`** - 核心认证器
   ```python
   # 初始化认证器（必须提供Azure应用客户端ID）
   config = AuthConfig(client_id="your-client-id")
   auth = MinecraftAuthenticator(config)
   
   # 登录认证
   result = auth.login()
   if result.success:
       # 获取启动参数
       launch_args = auth.get_launch_arguments()
   ```

2. **`AuthConfig`** - 认证配置
   ```python
   config = AuthConfig(
       client_id="required",    # 必填：Azure应用客户端ID
       cache_file="auth.json",  # 令牌缓存文件
       timeout=30,              # 请求超时
       auto_refresh=True        # 自动刷新令牌
   )
   ```

#### 主要功能：
- **微软设备代码流登录** - 完整的OAuth 2.0认证流程
- **令牌缓存管理** - 自动保存和恢复登录状态
- **玩家档案获取** - 获取用户名、UUID、皮肤等信息
- **离线模式支持** - 生成离线启动参数
- **游戏许可证验证** - 确保账号拥有Minecraft

## 🔧 高级用法

### 正版认证流程

```python
from minecraft_auth import MinecraftAuthenticator, AuthConfig

# 1. 创建认证器
auth_config = AuthConfig(
    client_id="your-azure-app-client-id"
)
auth = MinecraftAuthenticator(auth_config)

# 2. 检查登录状态
if not auth.is_logged_in():
    # 3. 开始登录
    result = auth.login()
    
    if result.success:
        print(f"登录成功！欢迎 {result.profile.username}")
    else:
        print(f"登录失败：{result.error_message}")
        # 使用离线模式
        offline_args = auth.get_offline_arguments("MyPlayer")
else:
    print(f"已登录为：{auth.get_profile().username}")

# 4. 获取启动参数
launch_args = auth.get_launch_arguments()
```

### 自定义UI认证流程

```python
# 获取设备代码信息（用于自定义UI）
device_info = auth.get_device_code_info()

# 显示给用户
print(f"请访问：{device_info['verification_uri']}")
print(f"输入代码：{device_info['user_code']}")

# 轮询授权状态
import time
while True:
    result = auth.poll_device_auth(device_info['device_code'])
    
    if result.success:
        print("登录成功！")
        break
    elif "等待授权" in result.error_message:
        time.sleep(device_info['interval'])
        continue
    else:
        print(f"授权失败：{result.error_message}")
        break
```

### 离线模式

```python
# 生成离线启动参数
offline_args = auth.get_offline_arguments("MyOfflinePlayer")

# 使用启动器启动
from minecraft_downloader import MinecraftLauncher

launcher = MinecraftLauncher(downloader)
success = launcher.launch_with_auth(
    version_id="1.20.1",
    auth_args=offline_args,
    memory="4G"
)
```

### 批量操作

```python
# 批量下载多个版本
versions = ["1.20.1", "1.19.4", "1.18.2"]

for version_id in versions:
    try:
        # 检查是否已安装
        if not launcher.is_version_installed(version_id):
            print(f"开始下载 {version_id}...")
            version_info = downloader.get_version_info(version_id)
            success = downloader.download_version(version_info)
            
            if success:
                print(f"{version_id} 下载完成")
            else:
                print(f"{version_id} 下载失败")
    except Exception as e:
        print(f"处理 {version_id} 时出错：{e}")
```

## ⚙️ 配置说明

### Azure应用注册

使用正版认证功能需要注册Azure应用：

1. 访问 [Azure门户](https://portal.azure.com)
2. 创建新的应用注册
3. 配置重定向URI为 `http://localhost`
4. 启用"公开客户端"选项
5. 获取客户端ID（client_id）

### 内存配置建议

| 游戏版本 | 推荐内存 | 最小内存 |
|---------|----------|----------|
| 1.18+   | 4-8GB    | 2GB      |
| 1.13-1.17 | 3-6GB  | 2GB      |
| 1.8-1.12 | 2-4GB    | 1GB      |
| 旧版本   | 1-2GB    | 512MB    |

### 目录结构

```
minecraft/
├── versions/           # 版本文件
│   └── [version-id]/
│       ├── [version-id].jar
│       ├── [version-id].json
│       └── natives/    # 原生库文件
├── assets/            # 资源文件
│   ├── indexes/       # 资源索引
│   └── objects/       # 资源对象
├── libraries/         # 库文件
└── launch_*.bat      # 生成的启动脚本
```

## 🛠️ 故障排除

### 常见问题

**Q: 正版认证失败怎么办？**
A: 
1. 检查Azure应用客户端ID是否正确
2. 确保Azure应用已正确配置重定向URI
3. 验证网络连接是否正常
4. 确认微软账户拥有Minecraft许可证

**Q: 下载速度很慢？**
A: 
- 增加 `max_workers` 参数提升并发数
- 检查网络连接和代理设置
- 使用稳定的网络环境

**Q: 启动游戏时报Java错误？**
A:
- 确保已安装Java 8或更高版本
- 检查Java路径是否正确配置
- 调整内存设置（`-Xmx`参数）

**Q: 文件验证失败？**
A:
- 库会自动重新下载损坏的文件
- 检查磁盘空间是否充足
- 验证网络连接稳定性

### 错误代码

| 错误类型 | 描述 | 解决方法 |
|---------|------|----------|
| `VersionNotFoundError` | 版本未找到 | 检查版本ID是否正确 |
| `NetworkError` | 网络连接错误 | 检查网络连接和代理设置 |
| `AuthError` | 认证过程错误 | 检查客户端ID和网络连接 |
| `NoGameLicenseError` | 无游戏许可证 | 确认账户拥有Minecraft |
| `JavaNotFoundError` | Java未找到 | 安装Java或指定Java路径 |

## 🔐 安全性说明

- 认证令牌会本地缓存，确保缓存文件安全
- 建议定期清除缓存文件
- 不要分享认证令牌和客户端ID
- 使用离线模式时，用户名仅用于本地显示

## 📄 许可证

本项目采用 **MIT 许可证** - 详见 [LICENSE](LICENSE) 文件。

## ⚠️ 免责声明

本项目与 **Mojang Studios** 无关，**Minecraft** 是 Mojang Studios 的商标。使用本库下载和运行 Minecraft 需要遵守 Minecraft 的最终用户许可协议（EULA）。

## 🤝 贡献指南

我们欢迎各种形式的贡献：

1. 🐛 **报告Bug** - 在GitHub Issues中提交问题
2. 💡 **功能建议** - 提出改进建议
3. 📝 **文档改进** - 完善使用文档
4. 🔧 **代码贡献** - 提交Pull Request

## 📞 联系方式

- **项目主页**: https://github.com/lijiayuapp/PythonMinecraftLauncher
- **问题反馈**: GitHub Issues
- **邮箱**: lijiayuappman@outlook.com

---

**如果这个项目对你有帮助，请给个 ⭐️ 支持一下！**
