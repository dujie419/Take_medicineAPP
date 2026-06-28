# B 同学用药计划模块交接说明

更新时间：2026-06-28

## 1. 本次完成范围

本次完成了 B 同学负责业务线中的 B-1 用药计划管理闭环：

- 用药计划和提醒时间数据模型
- 用药计划数据库迁移
- 计划新增、列表、详情、修改和删除接口
- 计划暂停与启用
- 当前用户数据隔离
- 药品归属校验
- 每日次数与提醒时间数量一致性校验
- 提醒时间格式、数量、重复值校验
- 计划起止日期校验
- 计划列表、新增和编辑前端页面
- 无计划、无药品、加载失败等页面状态
- 前端删除二次确认和启停失败回滚
- 后端 Schema 与路由测试

本次只完成“用药计划管理模块”，尚未包含：

- 今日提醒接口和页面
- 同一时间多药合并
- 服药记录
- Android 本地通知、震动和 TTS
- 重复提醒和自定义录音

## 2. 已完成接口

所有计划接口都需要登录，并携带：

```text
Authorization: Bearer <access_token>
```

### 获取当前用户的计划列表

```text
GET /api/v1/plans
```

成功返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": 1,
        "medicine_id": 1,
        "medicine": {
          "id": 1,
          "name": "阿司匹林",
          "specification": "100mg"
        },
        "dose": "1片",
        "daily_times": 2,
        "start_date": "2026-06-28",
        "end_date": null,
        "remark": "饭后服用",
        "is_enabled": true,
        "reminder_times": [
          "08:00",
          "20:00"
        ],
        "created_at": "2026-06-28T17:00:00",
        "updated_at": "2026-06-28T17:00:00"
      }
    ],
    "total": 1
  }
}
```

说明：

- 只返回当前登录用户自己的计划。
- 已软删除的计划不会出现在列表中。
- 计划按创建时间和 ID 倒序排列。
- 提醒时间按时间升序返回。

### 新增用药计划

```text
POST /api/v1/plans
```

请求示例：

```json
{
  "medicine_id": 1,
  "dose": "1片",
  "daily_times": 2,
  "start_date": "2026-06-28",
  "end_date": null,
  "remark": "饭后服用",
  "is_enabled": true,
  "reminder_times": [
    "08:00",
    "20:00"
  ]
}
```

创建成功返回 HTTP `201`。

注意：

- `medicine_id` 必须属于当前登录用户。
- `user_id` 不由前端传入，后端统一使用当前登录用户 ID。
- `daily_times` 必须等于 `reminder_times` 的数量。
- 每天最多支持 24 个提醒时间。

### 获取计划详情

```text
GET /api/v1/plans/{plan_id}
```

只能查看当前登录用户自己的、未删除的计划。计划不存在或属于其他用户时返回 404。

### 修改用药计划

```text
PUT /api/v1/plans/{plan_id}
PATCH /api/v1/plans/{plan_id}
```

当前前端使用 `PATCH`，后端同时保留 `PUT`。

修改提醒时间示例：

```json
{
  "dose": "1片",
  "daily_times": 2,
  "start_date": "2026-06-28",
  "end_date": "2026-07-28",
  "remark": "饭后服用",
  "is_enabled": true,
  "reminder_times": [
    "09:00",
    "21:00"
  ]
}
```

只修改启停状态：

```json
{
  "is_enabled": false
}
```

编辑计划时不允许传入或修改 `medicine_id`。如果需要更换药品，应删除原计划后重新创建。

### 删除用药计划

```text
DELETE /api/v1/plans/{plan_id}
```

删除采用软删除方式：

- `is_enabled` 设置为 `false`。
- `deleted_at` 写入删除时间。
- 原始计划数据保留在数据库中。
- 删除后的计划不再出现在列表和详情接口中。

前端删除前会弹出二次确认窗口。

## 3. 参数校验规则

### 每日次数

`daily_times` 取值范围：

```text
1 到 24
```

每日次数必须等于提醒时间数量。

正确示例：

```json
{
  "daily_times": 2,
  "reminder_times": ["08:00", "20:00"]
}
```

错误示例：

```json
{
  "daily_times": 2,
  "reminder_times": ["08:00"]
}
```

### 提醒时间

提醒时间必须使用：

```text
HH:mm
```

有效示例：

```text
08:00
20:30
```

无效示例：

```text
8:00
24:00
08:60
08:00:30
```

同一个计划内提醒时间不能重复。后端会排序后保存和返回。

### 日期范围

- `start_date` 必填。
- `end_date` 可以为空，表示长期有效。
- `end_date` 不能早于 `start_date`。
- 开始日期和结束日期可以是同一天。

### 剂量和备注

- `dose` 必填，去除首尾空格后不能为空，最长 100 个字符。
- `remark` 选填，去除首尾空格后为空时保存为 `null`，最长 500 个字符。

## 4. 数据库变更

新增 Alembic 迁移：

```text
backend/alembic/versions/20260628_0003_create_medication_plans.py
```

迁移版本关系：

```text
20260628_0001  users
20260628_0002  medicines
20260628_0003  medication_plans、reminder_times
```

当前 Alembic 版本：

```text
20260628_0003 (head)
```

### medication_plans 表

字段：

```text
id
user_id
medicine_id
dose
daily_times
start_date
end_date
remark
is_enabled
deleted_at
created_at
updated_at
```

关联关系：

- `user_id` 外键关联 `users.id`，用户删除时级联删除计划。
- `medicine_id` 外键关联 `medicines.id`，存在计划时限制删除药品。
- 通过 `user_id + is_enabled` 索引支持用户有效计划查询。
- 通过 `start_date + end_date` 索引支持后续今日提醒日期过滤。

### reminder_times 表

字段：

```text
id
plan_id
reminder_time
created_at
updated_at
```

约束：

- `plan_id` 外键关联 `medication_plans.id`。
- 删除计划时级联删除提醒时间。
- `plan_id + reminder_time` 有唯一约束，避免同一计划出现重复时间。

### 迁移兼容说明

共享数据库之前已经手工创建过计划表，因此 `20260628_0003` 在升级时会先检查表是否存在：

- 表不存在时，完整创建表、外键、索引和唯一约束。
- 表已存在时，不重复创建，只推进 Alembic 版本。

同步数据库：

```powershell
cd D:\Projects\Take_medicineAPP\backend
conda activate take-medicine-api
alembic upgrade head
alembic current
```

## 5. 用户隔离和删除策略

计划模块所有查询都同时校验：

```text
plan.id
plan.user_id == current_user.id
plan.deleted_at IS NULL
```

创建计划时还会校验：

```text
medicine.id
medicine.user_id == current_user.id
```

因此：

- 用户不能使用其他用户的药品创建计划。
- 用户不能查看、修改或删除其他用户的计划。
- 前端传入的 `user_id` 不会被信任。
- 已删除计划不能被再次查询或修改。

## 6. 前端完成内容

新增或完成页面：

```text
frontend/frontend/pages/plans/index.vue
frontend/frontend/pages/plans/form.vue
```

页面路由：

```text
/pages/plans/index
/pages/plans/form
/pages/plans/form?id={plan_id}
```

### 计划列表页面

已支持：

- 加载计划列表
- 下拉刷新
- 加载状态
- 网络错误状态和重新加载
- 无计划空状态
- 跳转新增计划
- 跳转新增药品
- 展示药品名称和规格
- 展示每次剂量
- 展示提醒时间
- 展示起止日期
- 展示启用或暂停状态
- 修改计划启停状态
- 启停失败时恢复原开关状态
- 跳转编辑页面
- 删除二次确认
- 删除后刷新列表

### 新增和编辑页面

已支持：

- 加载当前用户药品
- 选择已有药品
- 自动带入药品默认剂量
- 编辑计划时禁止更换药品
- 输入每次剂量
- 设置开始日期和结束日期
- 清除结束日期，表示长期有效
- 添加、修改和删除提醒时间
- 设置计划备注
- 设置启用状态
- 无药品时引导到新增药品页面
- 从新增药品页面返回后刷新药品列表
- 前端重复时间和日期范围校验
- 自动根据提醒时间数量生成 `daily_times`
- 提交前按时间排序
- 创建或修改成功后返回计划列表
- 显示用药安全提示

### 与 A 同学模块的协作方式

计划模块复用 A 同学已有的：

```text
take_medicine_base_url
take_medicine_token
take_medicine_user
GET /api/v1/medicines
```

B 模块通过 `authStore` 读取后端地址和 Token，没有修改 A 同学的：

```text
frontend/frontend/common/api.js
frontend/frontend/pages/medicines/*
```

只在“我的”页面已登录区域追加了“用药计划”入口，不改变认证、用户资料和药品管理逻辑。

Token 缺失或接口返回 401 时，计划模块会：

- 清除本地登录信息。
- 显示中文提示。
- 返回“我的”登录页面。

## 7. 重要代码文件

### 后端

数据模型：

```text
backend/app/models/medication_plan.py
backend/app/models/reminder_time.py
```

请求和返回 Schema：

```text
backend/app/schemas/plan.py
```

业务服务：

```text
backend/app/services/plan_service.py
```

API 路由：

```text
backend/app/api/v1/plans.py
backend/app/api/v1/router.py
```

数据库迁移：

```text
backend/alembic/versions/20260628_0003_create_medication_plans.py
```

测试：

```text
backend/tests/test_plan_schemas.py
backend/tests/test_plan_routes.py
```

### 前端

计划接口：

```text
frontend/frontend/api/plans.js
```

B 模块请求封装：

```text
frontend/frontend/utils/request.js
```

药品列表适配接口：

```text
frontend/frontend/api/medicines.js
```

计划页面：

```text
frontend/frontend/pages/plans/index.vue
frontend/frontend/pages/plans/form.vue
```

页面注册和入口：

```text
frontend/frontend/pages.json
frontend/frontend/pages/index/index.vue
```

## 8. 启动和联调方式

### 启动 MySQL 和 Redis

```powershell
cd D:\Projects\Take_medicineAPP
docker compose up -d
```

### 更新数据库

```powershell
cd D:\Projects\Take_medicineAPP\backend
conda activate take-medicine-api
alembic upgrade head
```

### 启动后端

推荐从 `backend` 目录启动：

```powershell
cd D:\Projects\Take_medicineAPP\backend
conda activate take-medicine-api
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

### 启动前端

使用 HBuilderX 打开：

```text
D:\Projects\Take_medicineAPP\frontend\frontend
```

登录后在“我的”页面点击：

```text
用药计划
```

Android 真机访问电脑后端时，不能使用 `127.0.0.1`，应将本地保存的后端地址设置为电脑局域网地址，例如：

```text
http://192.168.1.100:8000
```

后端地址不要重复添加 `/api/v1`，计划模块会自动拼接完整接口路径。

## 9. 测试记录

### 自动化测试

执行：

```powershell
cd D:\Projects\Take_medicineAPP\backend
conda activate take-medicine-api
python -m pytest tests -q
```

当前结果：

```text
29 passed
```

计划模块已覆盖：

- 创建计划参数标准化
- 提醒时间自动排序
- 每日次数和提醒时间数量一致性
- 重复提醒时间校验
- `HH:mm` 格式校验
- 起止日期校验
- 每日次数范围校验
- 未知字段拒绝
- 空修改请求拒绝
- 必填字段拒绝 `null`
- 编辑时禁止修改药品
- 计划路由注册检查
- `GET /api/v1/plans`
- `POST /api/v1/plans`
- `GET /api/v1/plans/{plan_id}`
- `PUT/PATCH /api/v1/plans/{plan_id}`
- `DELETE /api/v1/plans/{plan_id}`

### 手动接口测试

项目根目录的文件：

```text
test_main.http
```

可以按顺序运行：

1. 健康检查。
2. 获取验证码。
3. 登录。
4. 查询当前用户。
5. 创建测试药品。
6. 创建用药计划。
7. 查询用药计划。

### 前端静态检查

已完成：

- `pages.json` 配置解析。
- “我的”、计划列表、计划表单脚本语法检查。
- A 同学 `common/api.js` 和药品页面未被修改。

H5 和 Android 的页面显示、点击和真机网络仍需要使用 HBuilderX 做最终人工验收。

## 10. 验收建议

建议按以下顺序验收完整计划闭环：

```text
登录
  → 新增药品
  → 进入用药计划
  → 创建计划
  → 查看计划列表
  → 编辑计划
  → 暂停计划
  → 启用计划
  → 删除计划
```

重点检查：

- 不同用户只能看到自己的计划。
- 其他用户的药品不能被用于创建计划。
- 两个相同提醒时间不能提交。
- 结束日期早于开始日期不能提交。
- 修改提醒时间时 `daily_times` 同步更新。
- 暂停计划后页面状态正确。
- 删除前有二次确认。
- 删除后计划不再显示。
- Token 失效后能返回登录页。

## 11. 后续模块接手建议

下一步应继续完成 B-2 今日提醒模块。

今日提醒查询计划时应过滤：

```text
MedicationPlan.user_id == current_user.id
MedicationPlan.is_enabled == true
MedicationPlan.deleted_at IS NULL
MedicationPlan.start_date <= today
MedicationPlan.end_date IS NULL 或 MedicationPlan.end_date >= today
```

其中 `today` 必须根据当前用户的 `timezone` 计算，默认：

```text
Asia/Shanghai
```

后续还需要实现：

- `GET /api/v1/today`
- 同一时间多药合并
- 中文语音播报文本
- medication_logs 服药记录表
- 服药记录幂等写入
- Android 本地通知刷新

新增、编辑、暂停、启用或删除计划后，Android 通知模块后续必须重新同步本地提醒。目前计划管理模块只更新服务端数据，尚未实现本地通知调度。

## 12. 当前注意事项

- 创建计划前必须先有当前用户自己的药品。
- 计划接口统一使用 `/api/v1/plans`，不能省略 `/api/v1`。
- 前端保存的后端基础地址不要包含 `/api/v1`。
- 受保护接口必须携带 JWT。
- 编辑计划不能更换药品。
- 删除采用软删除，不会立即物理删除数据库记录。
- 当前计划按每日重复处理，暂不支持按星期或隔日服药。
- 当前尚未接入今日提醒、服药记录和 Android 本地通知。
- 用药信息只用于管理和提醒，不能替代医生处方和药品说明书。
