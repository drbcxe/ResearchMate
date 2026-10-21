**七天使用同一套 Git / GitHub 工作方式**

命令在 D:\Study\简历\ResearchMate 运行。所有 GitHub 创建、提交和发布由你亲手完成，本手册不会替你执行上传。

**1．先理解五个位置**

工作目录：正在编辑的文件。暂存区：准备进入下一次提交的内容。本地提交：可查看/恢复的历史。远程仓库：GitHub 上的副本。PR：功能分支合入 main 前的差异与检查记录。

main 保持已通过验收的内容；每天一个功能分支、小步提交。独立项目仍可使用 PR 自审，并如实标明没有外部审阅。

**2．Day 1 初始化**

先确认路径与 Git 根目录：

```powershell
Set-Location -LiteralPath 'D:\Study\简历\ResearchMate'
Get-Location
git rev-parse --show-toplevel
```

当前没有仓库时，最后一条显示 not a git repository 是正常的。若它指向其它父目录，先弄清现有仓库边界，不在父仓库里再盲目初始化。

检查提交身份；缺少时使用你自己的姓名与 GitHub 配置的邮箱（可用 GitHub 提供的 noreply 邮箱）。不要照抄别人的身份。

```powershell
git config --get user.name
git config --get user.email
git init -b main
git config user.name '替换为你的提交姓名'
git config user.email '替换为你的提交邮箱'
```

后两条仅在本仓库设置，不修改全局身份。

- [ ] 补全 .gitignore，再暂存。
- [ ] 确认 .env 被忽略，.env.example 可以被提交。
- [ ] 首次先提交设计、现有工具/示例/测试与忽略规则作为基线。
- [ ] 不暂存仓库外的简历或研究数据。

```powershell
git status --short
git check-ignore .env
git add -- .gitignore README.md tools tests examples evals '工具与状态契约.md' '开发关卡.md' '验证记录.md' '7天开发清单'
git diff --cached --stat
git diff --cached
git commit -m 'chore: record ResearchMate starting baseline'
```

路径只添加当前真实存在且检查过的文件；要纳入本目录的设计手册，另用 git add -- '文件名.md' 或明确目录名添加。不要只因命令成功就跳过 staged diff。

在 GitHub 网页新建空 ResearchMate 仓库，选择自己需要的可见性；初始不勾自动 README/.gitignore，避免产生第二套初始历史。[GitHub 建仓库说明](https://docs.github.com/en/get-started/start-your-journey/creating-a-repository-for-your-project-on-github)

```powershell
$rmGithubUser = '替换为你的GitHub用户名'
git remote add origin "https://github.com/$rmGithubUser/ResearchMate.git"
git remote -v
git push -u origin main
git switch -c feat/day01-bootstrap
```

HTTPS 登录按 Git Credential Manager/浏览器完成，不把访问令牌写进 remote URL。远程若已有内容，先查清历史，不能用强推掩盖。

**3．每天开始**

Day 1 已创建分支，之后每一天：

```powershell
git switch main
git pull --ff-only
git status --short
git switch -c feat/day02-data-comparison
```

把最后的分支名换成当天约定：

| 天 | 分支 | 建议 PR 主题 |
|---|---|---|
| D1 | feat/day01-bootstrap | 前后端骨架与环境 |
| D2 | feat/day02-data-comparison | 导入与可追溯比较 |
| D3 | feat/day03-agent-chat | 真实工具调用对话 |
| D4 | feat/day04-memory-recovery | 登录、记忆与恢复 |
| D5 | feat/day05-tasks-reminders | 后台执行与提醒 |
| D6 | feat/day06-streaming-hardening | 事件流与故障行为 |
| D7 | release/v0.1.0 | 部署与首版交付 |

开始前有未提交改动时先看 diff，决定提交到原分支或妥善保存，再切分支；不运行强制清理。

**4．一项改动完成后的操作**

```powershell
git status --short
git diff
git add -- app admin-ui tests scripts migrations pyproject.toml uv.lock
git diff --cached --stat
git diff --cached
git commit -m 'feat: import experiment results and compare compatible runs'
git push -u origin feat/day02-data-comparison
```

只填写当天存在并准备提交的路径；锁文件有变化时和依赖声明一起提交。第一天尚无 migrations 时不要机械添加。

一项功能可有多个有意义的小提交，例如 feat: add artifact import、test: reject incompatible comparisons、fix: preserve uploaded artifact source。格式化变更与业务修改尽量让差异可读。

**5．PR 自审与合并**

- [ ] GitHub Compare & pull request，目标 main，来源为当天分支。
- [ ] 描述实际问题、结果行为、运行过的检查和边界。
- [ ] Files changed 逐个看：有无误提交文件、密钥、无关改动。
- [ ] Checks 全部完成，失败先读日志，修复后推同一分支。
- [ ] 自己审阅写“独立开发，自审；未经过外部代码审查”。
- [ ] 合并后更新本地 main；七天中可先保留旧功能分支。

PR 描述示例：

> 上传实验结果后，可以按当前文件版本比较两个实验，并展示来源行；评估协议不一致时返回明确拒绝。验证：比较工具测试、API/数据库用例、前端构建，以及合成 CSV 的成功/拒绝流程。限制：首版只比较同一文件中的单指标结果。

**6．常用查看与小范围撤销**

```powershell
git log --oneline --graph --decorate -12
git diff --stat
git diff --cached
git restore --staged -- '具体文件路径'
```

最后一条只是从暂存区取回，不删除工作目录里的编辑。已经推送 main 的错误优先新增修复提交或经过检查的 revert，保留可追溯历史。

锁文件冲突要结合依赖声明重新生成、测试后提交；数据库迁移冲突要核对迁移链，不能随便删一个版本文件。

**7．第七天检查**

- [ ] GitHub 中有完整源码、锁文件、迁移、示例、测试、启动说明。
- [ ] uv.lock 和 admin-ui/pnpm-lock.yaml 存在，CI 用 frozen/locked 安装。
- [ ] .env、.runtime、数据库文件、模型权重、私人简历和大数据集未被跟踪。
- [ ] main 对应实际验收代码，v0.1.0 tag 指向该提交。
- [ ] 新目录 clone 与新数据卷验证通过，Release 说明可复现。

上传 GitHub 是版本管理与协作交付；运行前后端使用本项目 Docker 部署步骤。GitHub 静态页面托管不能承担本项目 Python、数据库和 worker。

