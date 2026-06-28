# A 同学认证与用户资料模块交接说明

更新时间：2026-06-28

## 1. 本次完成范围

本次完成了 A 同学负责业务线中的第一阶段后端能力：

- FastAPI 后端基础入口
- 统一 API 返回格式
- 统一异常返回格式
- Redis 验证码缓存方案
- 手机号验证码登录
- 首次登录自动注册
- JWT 生成与鉴权
- 当前用户信息查询
- 用户称呼修改
- users 用户表迁移

验证码不再存 MySQL，按最新方案使用 Redis 保存短期状态；MySQL 当前只保存用户数据。

## 2. 已完成接口

### 健康检查

```text
GET /health
```

成功返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "ok",
    "message": "Take Medicine API is running"
  }
}
```

### 获取短信验证码

```text
POST /api/v1/auth/sms-codes
```

请求：

```json
{
  "phone": "13800000000"
}
```

开发模式下不会真实发短信，验证码固定使用：

```text
123456
```

### 登录或首次自动注册

```text
POST /api/v1/auth/login
```

请求：

```json
{
  "phone": "13800000000",
  "code": "123456"
}
```

成功后返回 `access_token`、`token_type` 和当前用户信息。

### 获取当前用户

```text
GET /api/v1/auth/me
```

需要请求头：

```text
Authorization: Bearer <access_token>
```

### 修改当前用户称呼

```text
PATCH /api/v1/auth/me
```

请求：

```json
{
  "nickname": "张阿姨"
}
```

称呼会自动去除首尾空格，不能为空。

## 3. 数据库变更

新增 Alembic 迁移文件：

```text
backend/alembic/versions/20260628_0001_create_users.py
```

当前迁移会创建：

```text
users
alembic_version
```

`users` 表字段：

```text
id
phone
nickname
timezone
is_active
created_at
updated_at
```

手机号 `phone` 有唯一索引。

执行迁移命令：

```powershell
cd D:\all_codes\Take_medicineAPP\backend
alembic upgrade head
```

## 4. Redis 设计

验证码相关状态使用 Redis。

新增配置：

```env
REDIS_URL=redis://127.0.0.1:6379/0
SMS_CODE_EXPIRE_SECONDS=300
SMS_SEND_COOLDOWN_SECONDS=60
SMS_MAX_DAILY_SEND=10
SMS_MAX_VERIFY_ATTEMPTS=5
```

Redis key 设计：

```text
sms:code:{phone}
sms:attempts:{phone}
sms:cooldown:{phone}
sms:daily:{phone}:{yyyyMMdd}
```

含义：

- `sms:code:{phone}` 保存验证码摘要，默认 5 分钟过期。
- `sms:attempts:{phone}` 保存验证码错误次数。
- `sms:cooldown:{phone}` 控制 60 秒内不能重复发送。
- `sms:daily:{phone}:{yyyyMMdd}` 控制单手机号每日发送次数。

## 5. 配置和依赖变更

### environment.yml

新增 Python Redis 客户端：

```yaml
- redis
```

如果其他同学本地环境缺少该包，执行：

```powershell
conda env update -f environment.yml --prune
```

或临时安装：

```powershell
python -m pip install redis
```

### docker-compose.yml

已补充 Redis 服务：

```yaml
redis:
  image: redis:7
  container_name: take_medicine_redis
  restart: always
  ports:
    - "6379:6379"
```

如果 Docker 后续可用，可以直接启动 MySQL 和 Redis。

## 6. 重要代码文件

后端入口：

```text
backend/app/main.py
```

配置读取：

```text
backend/app/core/config.py
```

数据库连接：

```text
backend/app/core/database.py
```

Redis 连接：

```text
backend/app/core/redis.py
```

JWT 和验证码摘要：

```text
backend/app/core/security.py
```

鉴权依赖：

```text
backend/app/api/deps.py
```

认证路由：

```text
backend/app/api/v1/auth.py
```

用户模型：

```text
backend/app/models/user.py
```

认证服务：

```text
backend/app/services/auth_service.py
backend/app/services/sms_service.py
```

Schema：

```text
backend/app/schemas/auth.py
backend/app/schemas/user.py
backend/app/schemas/common.py
```

## 7. 启动方式

推荐从 `backend` 目录启动：

```powershell
cd D:\all_codes\Take_medicineAPP\backend
conda activate take-medicine-api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

PyCharm 运行配置关键项：

```text
应用程序文件:
D:/all_codes/Take_medicineAPP/backend/app/main.py

应用程序名称:
app

运行方式:
Uvicorn

运行选项:
--host 0.0.0.0 --port 8000 --reload
```

注意不要启动根目录旧的：

```text
D:/all_codes/Take_medicineAPP/main.py
```

否则 `/health` 会 404。

## 8. 测试记录

已完成验证：

- `/health` 返回 200。
- `/docs` 能看到认证接口。
- Redis 启动后，`POST /api/v1/auth/sms-codes` 可成功返回。
- 使用手机号 `13800000000` 和验证码 `123456` 可登录。
- 登录成功后返回 JWT。
- Swagger Authorize 携带 token 后，`GET /api/v1/auth/me` 成功。
- `PATCH /api/v1/auth/me` 可修改称呼。
- Alembic 迁移后数据库中存在 `users` 和 `alembic_version` 表。

## 9. 下一模块接手建议

下一位同学如果继续开发 B 同学模块，可以直接复用：

```python
from app.api.deps import get_current_user
```

所有需要登录的接口都应该加当前用户依赖，避免用户数据串号。

示例：

```python
@router.get("/example")
def example(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user.id
```

后续药品、计划、今日提醒、服药记录等接口都应通过 `current_user.id` 过滤数据。

建议下一步优先实现 A 同学后续药品管理接口：

```text
GET /api/v1/medicines
POST /api/v1/medicines
GET /api/v1/medicines/{id}
```

药品接口完成后，B 同学的用药计划模块就可以基于药品数据继续开发。

## 10. 当前注意事项

- 验证码依赖 Redis，Redis 未启动时验证码接口会返回 503。
- 登录依赖 MySQL，必须先执行 `alembic upgrade head`。
- `.env` 不提交，`.env.example` 已补充 Redis 相关配置。
- 生产环境不能继续使用默认 `JWT_SECRET_KEY=please-change-this-secret`。
- 生产环境不能继续使用 `SMS_MODE=mock`。
- 受保护接口统一使用 `Authorization: Bearer <token>`。
