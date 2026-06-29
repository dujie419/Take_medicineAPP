下面把这套 **Git 协作方式** 详细拆开讲，适合你们两个人做这个“按时吃药 App”项目。

你们的目标是：**两个人不按前后端分工，而是按业务线分工，但代码仍然放在同一个 Git 仓库里统一管理。**

------

# 一、先理解这几个分支分别干什么

建议仓库里有这几个主要分支：

```
main
dev
feature/auth-medicine-ai
feature/plan-reminder-log
feature/docs-test
```

## 1. `main` 分支

`main` 是 **正式稳定版本分支**。

它只放：

- 能正常运行的代码
- 可以演示的版本
- 可以提交作业的版本
- 不应该频繁改动

简单理解：

> `main` 就是最终交付版本。

平时不要直接在 `main` 上写代码。

------

## 2. `dev` 分支

`dev` 是 **日常集成分支**。

两个人每天开发完成后，都把自己的功能合并到 `dev`。

简单理解：

> `dev` 是两个人每天合并代码、联调测试的地方。

例如：

- A 做完登录模块，合并到 `dev`
- B 做完计划页面，合并到 `dev`
- 两个人一起在 `dev` 上测试完整流程

------

## 3. `feature/auth-medicine-ai` 分支

这是 A 同学的业务分支。

A 负责：

```
登录认证
用户资料
药品管理
AI 识药
AI 识别记录
```

所以 A 平时就在这个分支开发：

```
git checkout feature/auth-medicine-ai
```

------

## 4. `feature/plan-reminder-log` 分支

这是 B 同学的业务分支。

B 负责：

```
用药计划
今日提醒
Android 通知
中文语音
服药记录
```

所以 B 平时就在这个分支开发：

```
git checkout feature/plan-reminder-log
```

------

## 5. `feature/docs-test` 分支

这个分支可以用来整理：

```
README
接口文档
数据库文档
测试报告
演示说明
分工说明
```

也可以不单独建，直接在 A 或 B 的分支里写文档。但如果文档比较多，建议单独建。

------

# 二、推荐的完整 Git 流程

整体流程是：

```
main
 ↓
dev
 ↓
feature/xxx
```

开发时：

```
从 dev 拉出自己的 feature 分支
在 feature 分支写代码
写完一个小功能就提交 commit
每天把 dev 最新代码同步到自己的 feature 分支
功能稳定后合并回 dev
dev 测试稳定后再合并到 main
```

------

# 三、第一次创建仓库和分支

假设你们已经有 GitHub 仓库。

## 1. 克隆项目

两个人都先执行：

```
git clone 仓库地址
cd Take_medicineAPP
```

例如：

```
git clone https://github.com/xxx/Take_medicineAPP.git
cd Take_medicineAPP
```

------

## 2. 查看当前分支

```
git branch
```

一般刚克隆下来是在：

```
main
```

------

## 3. 创建 `dev` 分支

由其中一个人执行一次即可：

```
git checkout -b dev
git push -u origin dev
```

意思是：

```
从当前 main 创建 dev 分支
并推送到远程 GitHub
```

------

## 4. A 创建自己的业务分支

A 同学执行：

```
git checkout dev
git pull origin dev
git checkout -b feature/auth-medicine-ai
git push -u origin feature/auth-medicine-ai
```

意思是：

```
切到 dev
拉取最新 dev
从 dev 创建 A 的业务分支
推送到远程仓库
```

------

## 5. B 创建自己的业务分支

B 同学执行：

```
git checkout dev
git pull origin dev
git checkout -b feature/plan-reminder-log
git push -u origin feature/plan-reminder-log
```

------

# 四、A 同学每天怎么开发、提交、推送

A 同学负责：

```
登录
用户
药品
AI 识药
```

## 1. 每天开始开发前

A 先切到自己的分支：

```
git checkout feature/auth-medicine-ai
```

然后拉取远程自己的分支：

```
git pull origin feature/auth-medicine-ai
```

再同步最新 `dev` 的代码：

```
git pull origin dev
```

这样做的目的：

> 确保自己是在最新项目代码基础上开发，避免和 B 的代码差太远。

------

## 2. 写完一个小功能后查看状态

比如 A 写完了登录接口。

执行：

```
git status
```

你会看到哪些文件被修改了。

------

## 3. 添加要提交的文件

可以添加全部修改：

```
git add .
```

也可以只添加某几个文件：

```
git add backend/app/api/auth.py backend/app/models/user.py
```

初学者可以先用：

```
git add .
```

------

## 4. 提交代码

例如 A 完成短信验证码接口：

```
git commit -m "feat(auth): add sms code api"
```

如果完成登录接口：

```
git commit -m "feat(auth): add sms login api"
```

如果完成药品列表接口：

```
git commit -m "feat(medicine): add medicine list api"
```

如果修复登录 bug：

```
git commit -m "fix(auth): fix token expired handling"
```

------

## 5. 推送到远程

```
git push origin feature/auth-medicine-ai
```

这样 GitHub 上就能看到 A 的最新代码。

------

# 五、B 同学每天怎么开发、提交、推送

B 同学负责：

```
计划
今日提醒
服药记录
Android 通知
语音提醒
```

## 1. 每天开始开发前

B 执行：

```
git checkout feature/plan-reminder-log
git pull origin feature/plan-reminder-log
git pull origin dev
```

------

## 2. 写完计划创建功能后提交

查看修改：

```
git status
```

添加文件：

```
git add .
```

提交：

```
git commit -m "feat(plan): add create medication plan"
```

推送：

```
git push origin feature/plan-reminder-log
```

------

## 3. 写完今日提醒功能后提交

```
git add .
git commit -m "feat(today): add today reminder api"
git push origin feature/plan-reminder-log
```

------

## 4. 修复同一时间多药合并 bug

```
git add .
git commit -m "fix(today): merge reminders with same time"
git push origin feature/plan-reminder-log
```

------

# 六、怎么把自己的功能合并到 `dev`

当 A 或 B 的某个功能已经写完，并且自己测试通过后，就可以合并到 `dev`。

有两种方式：

1. 在命令行合并
2. 在 GitHub 上提 Pull Request

如果你们是初学者，更推荐 **GitHub Pull Request**，因为更清楚、更安全。

------

# 七、方式一：命令行合并到 dev

假设 A 要把 `feature/auth-medicine-ai` 合并到 `dev`。

## A 的操作

### 1. 先确保自己的分支代码已经提交

```
git status
```

如果提示：

```
nothing to commit, working tree clean
```

说明当前没有未提交的修改。

------

### 2. 推送自己的分支

```
git push origin feature/auth-medicine-ai
```

------

### 3. 切换到 `dev`

```
git checkout dev
```

------

### 4. 拉取最新 `dev`

```
git pull origin dev
```

------

### 5. 合并 A 的分支

```
git merge feature/auth-medicine-ai
```

------

### 6. 如果没有冲突，推送 `dev`

```
git push origin dev
```

这样 A 的代码就进入 `dev` 了。

------

## B 合并到 dev 也是一样

```
git checkout dev
git pull origin dev
git merge feature/plan-reminder-log
git push origin dev
```

------

# 八、方式二：GitHub Pull Request 合并到 dev

推荐你们用这个。

## A 的流程

A 开发完成后，先推送自己的分支：

```
git push origin feature/auth-medicine-ai
```

然后打开 GitHub 仓库页面：

```
Pull requests
  ↓
New pull request
```

选择：

```
base: dev
compare: feature/auth-medicine-ai
```

意思是：

> 我要把 A 的业务分支合并到 dev。

然后创建 PR：

```
Create pull request
```

PR 标题可以写：

```
feat(auth): complete sms login and user profile
```

描述可以写：

```
本次完成：
1. 手机号验证码接口
2. 登录接口
3. JWT 生成和校验
4. 获取当前用户接口
5. 修改用户称呼接口

测试：
1. 测试手机号 13800000000
2. 测试验证码 123456
3. 登录后能获取 token
4. 使用 token 可以访问 /api/v1/auth/me
```

然后另一个人检查一下，没有问题就点击：

```
Merge pull request
```

------

## B 的流程

B 推送自己的分支：

```
git push origin feature/plan-reminder-log
```

在 GitHub 创建 PR：

```
base: dev
compare: feature/plan-reminder-log
```

PR 标题：

```
feat(plan): complete plan and today reminder
```

描述：

```
本次完成：
1. 新增计划接口
2. 查询计划接口
3. 修改计划接口
4. 删除计划接口
5. 今日提醒接口
6. 同一时间多药合并

测试：
1. 可以为已有药品创建计划
2. 每日次数和提醒时间数量不一致会报错
3. 同一时间多个药品可以合并展示
```

------

# 九、合并 `dev` 到自己的 feature 分支

这是你们最容易忽略的一步。

假设 B 已经把计划模块合并到了 `dev`，A 的分支还没有这些代码。

A 继续开发前，应该把 `dev` 最新代码同步到自己的分支。

A 执行：

```
git checkout feature/auth-medicine-ai
git pull origin dev
```

或者更完整：

```
git checkout feature/auth-medicine-ai
git fetch origin
git merge origin/dev
```

这样 A 的分支就包含 B 已经合并到 `dev` 的代码。

B 同理：

```
git checkout feature/plan-reminder-log
git pull origin dev
```

------

# 十、什么时候合并 `dev` 到 `main`

`main` 是稳定版本，不要每天乱合并。

建议在这些时候合并：

```
第一版登录流程完成
第一版药品和计划流程完成
第一版今日提醒流程完成
第一版可演示版本完成
最终提交作业前
```

------

## 合并方式

先切到 `main`：

```
git checkout main
```

拉取最新：

```
git pull origin main
```

合并 `dev`：

```
git merge dev
```

推送：

```
git push origin main
```

也可以通过 GitHub Pull Request：

```
base: main
compare: dev
```

更推荐 PR，因为可以检查清楚。

------

# 十一、如果出现代码冲突怎么办

冲突常见于两个人同时改了同一个文件。

例如两个人都改了：

```
backend/app/main.py
frontend/pages.json
frontend/api/request.js
```

Git 会提示 conflict。

------

## 1. 冲突示例

文件里可能出现：

```
<<<<<<< HEAD
A 写的代码
=======
B 写的代码
>>>>>>> feature/plan-reminder-log
```

意思是：

```
上面是当前分支的代码
下面是要合并进来的代码
Git 不知道保留哪个
需要人工处理
```

------

## 2. 解决方法

你需要手动改成最终正确版本。

例如：

```
from app.api.auth import router as auth_router
from app.api.medicine import router as medicine_router
from app.api.plan import router as plan_router
from app.api.today import router as today_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(medicine_router, prefix="/api/v1")
app.include_router(plan_router, prefix="/api/v1")
app.include_router(today_router, prefix="/api/v1")
```

然后保存文件。

------

## 3. 标记冲突已解决

```
git add .
git commit -m "fix: resolve merge conflict"
```

如果是在 merge 过程中，Git 可能会自动生成 merge commit 信息，你直接：

```
git commit
```

也可以。

------

# 十二、推荐的提交信息规范

你前面列的提交信息是对的，可以这样理解：

```
feat(auth): add sms login api
```

分成三部分：

```
类型(模块): 做了什么
```

------

## 1. 常用类型

| 类型       | 含义     | 示例                                    |
| ---------- | -------- | --------------------------------------- |
| `feat`     | 新功能   | `feat(plan): add create plan page`      |
| `fix`      | 修 bug   | `fix(today): fix reminder status error` |
| `docs`     | 文档     | `docs: add local setup guide`           |
| `test`     | 测试     | `test(log): add idempotent test`        |
| `refactor` | 重构     | `refactor(auth): split jwt service`     |
| `chore`    | 杂项配置 | `chore: update environment.yml`         |
| `style`    | 样式调整 | `style(today): adjust card layout`      |

------

## 2. 常用模块名

| 模块       | 含义         |
| ---------- | ------------ |
| `auth`     | 登录认证     |
| `user`     | 用户资料     |
| `medicine` | 药品         |
| `ai`       | AI 识药      |
| `plan`     | 用药计划     |
| `today`    | 今日提醒     |
| `log`      | 服药记录     |
| `notify`   | Android 通知 |
| `tts`      | 语音播报     |
| `docs`     | 文档         |
| `test`     | 测试         |

------

## 3. A 同学常见提交示例

```
git commit -m "feat(auth): add sms code api"
git commit -m "feat(auth): add jwt login"
git commit -m "feat(user): add update nickname api"
git commit -m "feat(medicine): add create medicine api"
git commit -m "feat(medicine): add medicine list page"
git commit -m "feat(ai): add image recognition mock"
git commit -m "fix(ai): handle invalid model json response"
```

------

## 4. B 同学常见提交示例

```
git commit -m "feat(plan): add create medication plan"
git commit -m "feat(plan): add reminder time validation"
git commit -m "feat(today): add today reminder api"
git commit -m "fix(today): merge reminders with same time"
git commit -m "feat(log): add medication log create api"
git commit -m "test(log): add medication log idempotent test"
git commit -m "feat(notify): add android local notification"
git commit -m "feat(tts): add chinese speech reminder"
```

------

# 十三、每天实际操作流程总结

## A 同学每天操作

```
# 1. 进入项目
cd Take_medicineAPP

# 2. 切到自己的分支
git checkout feature/auth-medicine-ai

# 3. 拉取自己分支最新代码
git pull origin feature/auth-medicine-ai

# 4. 同步 dev 最新代码
git pull origin dev

# 5. 开发代码
# 例如写登录、药品、AI识药

# 6. 查看修改
git status

# 7. 添加文件
git add .

# 8. 提交
git commit -m "feat(auth): add sms login api"

# 9. 推送
git push origin feature/auth-medicine-ai
```

功能稳定后，合并到 `dev`：

```
git checkout dev
git pull origin dev
git merge feature/auth-medicine-ai
git push origin dev
```

------

## B 同学每天操作

```
# 1. 进入项目
cd Take_medicineAPP

# 2. 切到自己的分支
git checkout feature/plan-reminder-log

# 3. 拉取自己分支最新代码
git pull origin feature/plan-reminder-log

# 4. 同步 dev 最新代码
git pull origin dev

# 5. 开发代码
# 例如写计划、今日提醒、服药记录

# 6. 查看修改
git status

# 7. 添加文件
git add .

# 8. 提交
git commit -m "feat(plan): add create medication plan"

# 9. 推送
git push origin feature/plan-reminder-log
```

功能稳定后，合并到 `dev`：

```
git checkout dev
git pull origin dev
git merge feature/plan-reminder-log
git push origin dev
```

------

# 十四、推荐你们实际采用的最简流程

如果你们刚开始用 Git，不要搞太复杂。
 建议用这个最简流程：

## 第一步：永远不要直接改 `main`

```
main 只放最终稳定版本
```

------

## 第二步：每个人只在自己的 feature 分支写代码

A：

```
feature/auth-medicine-ai
```

B：

```
feature/plan-reminder-log
```

------

## 第三步：每天开发前先同步 dev

A：

```
git checkout feature/auth-medicine-ai
git pull origin dev
```

B：

```
git checkout feature/plan-reminder-log
git pull origin dev
```

------

## 第四步：写完一个小功能就提交

```
git add .
git commit -m "feat(模块): 功能说明"
git push
```

例如：

```
git add .
git commit -m "feat(plan): add create plan page"
git push origin feature/plan-reminder-log
```

------

## 第五步：功能稳定后合并到 dev

```
git checkout dev
git pull origin dev
git merge 自己的feature分支
git push origin dev
```

------

## 第六步：dev 测试稳定后合并到 main

```
git checkout main
git pull origin main
git merge dev
git push origin main
```

------

# 十五、你们项目里的推荐分支对应任务

| 分支                        | 谁用               | 用来做什么                   |
| --------------------------- | ------------------ | ---------------------------- |
| `main`                      | 两人都不要直接开发 | 最终稳定版                   |
| `dev`                       | 两人共同           | 日常联调版                   |
| `feature/auth-medicine-ai`  | A                  | 登录、用户、药品、AI识药     |
| `feature/plan-reminder-log` | B                  | 计划、提醒、记录、通知、语音 |
| `feature/docs-test`         | 两人或其中一人     | 文档、测试、说明、报告       |

------

# 十六、特别注意事项

## 1. 不要把 `.env` 提交上去

`.env` 里面可能有：

```
数据库密码
JWT 密钥
短信密钥
AI API Key
```

必须加入 `.gitignore`。

只提交：

```
.env.example
```

------

## 2. 不要把本地数据库、上传图片提交上去

不要提交：

```
uploads/
mysql_data/
__pycache__/
node_modules/
dist/
unpackage/
```

这些也要写进 `.gitignore`。

------

## 3. 合并前一定要先跑一下项目

合并到 `dev` 前至少检查：

```
后端能启动
前端能运行
自己负责的功能能跑通
没有明显报错
```

------

## 4. 每次提交不要太大

不要一个 commit 包含：

```
登录 + 药品 + AI + 计划 + 通知 + 文档
```

这种很难回退。

建议一个 commit 只做一件事：

```
完成验证码接口
完成登录接口
完成药品列表页面
完成计划创建接口
修复今日提醒合并问题
```

------

## 5. 公共文件改动前先沟通

这些文件容易冲突：

```
backend/app/main.py
backend/app/core/config.py
backend/app/models/__init__.py
frontend/pages.json
frontend/api/request.js
docker-compose.yml
environment.yml
.env.example
```

如果要改这些文件，最好提前说一声。

------

# 十七、最终一句话总结

你们可以这样执行：

```
main：最终稳定版本
dev：每天合并联调用
A：在 feature/auth-medicine-ai 开发登录、药品、AI识药
B：在 feature/plan-reminder-log 开发计划、提醒、记录、通知
每天开发前 pull dev
小功能完成后 commit + push
功能稳定后 merge 到 dev
dev 测试稳定后 merge 到 main
```

最常用命令就是这几个：

```
git checkout 分支名
git pull origin 分支名
git pull origin dev
git status
git add .
git commit -m "feat(module): message"
git push origin 分支名
git merge 分支名
```