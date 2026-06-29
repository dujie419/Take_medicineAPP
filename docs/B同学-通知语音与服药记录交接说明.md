# B 同学通知语音与服药记录模块交接说明

更新时间：2026-06-29

## 1. 已完成内容

- 新增 `GET /api/v1/medication-logs`，支持 `limit`、`offset`、用户隔离和倒序查询。
- 历史记录返回药品名称、剂量、计划时间、实际时间、状态和稍后提醒时间。
- 保留原有 POST 接口，并处理并发请求造成的唯一键竞争。
- 新增独立服药记录页面：`/pages/medication-logs/index`。
- 新增 Android UTS 插件，提供本地通知、震动、TTS、重复提醒和自定义录音。
- 今日提醒、计划新增、修改、暂停、启用和删除后会重新同步本地通知。
- Token 失效时先清除当前用户通知，再清除登录信息。

## 2. Android 调度规则

- 仅调度当天状态为 `pending` 或 `snoozed` 的提醒。
- 首次提醒后每 5 分钟重复一次，截止到计划时间后 2 小时，最多 25 次。
- Android 12 以上优先使用精确闹钟；没有权限时降级为 1 分钟窗口提醒。
- Android 13 以上按需申请通知权限。
- 通知点击后进入今日提醒页面。
- 自定义录音按用户 ID 和提醒组 ID 隔离；没有录音时使用中文 TTS。

UTS 插件包含 AndroidManifest 配置，需要使用 HBuilderX 4.25 以上版本进行真机联编。涉及 Manifest 合并时，建议制作自定义调试基座。

## 3. A 同学需要接入的两个位置

B 分支没有修改 A 同学维护的“我的”页面。A 合并后只需：

1. 在“我的”页面增加入口：

```js
uni.navigateTo({ url: '/pages/medication-logs/index' })
```

2. 退出登录前清除该账号的本地通知：

```js
import { cancelCurrentUserReminders } from '@/services/reminderManager.js'

cancelCurrentUserReminders()
authStore.clearAuth()
```

必须先取消通知，再清除本地用户信息，否则无法取得用户 ID。

## 4. 真机验收

1. 使用 HBuilderX 打开 `frontend/frontend`。
2. 制作并运行包含 `tm-reminder` UTS 插件的 Android 调试基座。
3. 创建距当前时间几分钟的计划，在今日页允许通知权限。
4. 验证到点通知、震动、中文播报和点击跳转。
5. 验证“已服用”和“已跳过”后重复提醒立即停止。
6. 验证“稍后提醒”从五分钟后重新开始。
7. 录制超过一秒的提醒音，验证试听、替换 TTS 和删除后恢复 TTS。
8. 在 Android 12、13、14 以上设备分别验证精确闹钟和通知权限拒绝场景。

## 5. 自动化测试

执行：

```powershell
conda run -n take-medicine-api python -m pytest backend\tests -q
```

当前结果：

```text
65 passed
```
