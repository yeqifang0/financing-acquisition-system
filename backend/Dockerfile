FROM python:3.12-slim
WORKDIR /app

# 先复制依赖描述，利用 Docker layer cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制全部源码
COPY . .

# 确保 SQLite 数据目录存在且可写
RUN mkdir -p /app/data && chmod 777 /app/data

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
