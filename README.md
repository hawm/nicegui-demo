## 运行

### 本地运行
```
poetry install --no-root
poetry run python main.py
```

### Docker运行
```
docker build -t nicegui-demo ./
docker run -p 8080:8080 -v ./data:/app/data nicegui-demo
```

## 思路
1. 搜索NiceGUI、SQLAlchemy、Poetry等进入官网查看文档和实例
2. 过程中遇到问题先搜索后询问AI


## 问题
1. Poetry新建项目安装NiceGUI依赖会报Python版本错误，需要修改`pyproject.toml`中`requires-python = ">=3.12,<4.0"`
