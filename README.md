## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <你的项目仓库地址>
cd <项目目录>
```

### 2. 创建和激活虚拟环境 (推荐)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境

* 根据需要修改 `config.py` 文件中的配置项，例如数据库连接信息、JWT 密钥等。
* 检查 `TORTOISE_ORM.py` 中的数据库连接配置是否正确。
* 确保 `pyproject.toml` 文件中的 `[tool.aerich]` 部分指向正确的 Tortoise ORM 配置。

### 5. 初始化数据库和执行迁移

```bash
# 初始化 Aerich (首次运行时需要)
aerich init -t TORTOISE_ORM.tortoise_config --location ./migrations/models

# 生成迁移文件
aerich migrate

# 应用迁移
aerich upgrade
```

*注意：你需要根据 `TORTOISE_ORM.py` 中定义的 `tortoise_config` 字典来调整 `-t` 参数。*

### 6. 运行应用

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

*`main:app` 指向 `main.py` 文件中的 `app` FastAPI 实例。*

现在，你可以通过浏览器或 API 测试工具访问 `http://localhost:8000` (或你配置的地址和端口) 来使用此应用了。API 文档通常位于 `/docs` 或 `/redoc`。

## 📝 使用说明

* **API 接口**: 查阅 `api/` 目录下的代码和 FastAPI 自动生成的文档 (`/docs`) 来了解可用的 API 接口。
* **配置**: 应用的核心配置在 `config.py` 中。
* **数据库模型**: 在 `model/` 目录下定义，使用 Tortoise ORM。
* **数据验证**: 在 `schemas/` 目录下定义 Pydantic 模型。
* **日志**: 日志配置在 `core/loguru.py`，日志文件默认输出到 `logs/` 目录。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。
