# Codex-Antigravity Dialogue

让 **Codex Desktop 与 Google Antigravity Desktop** 在同一授权项目内交换消息、交接任务并读取结果的双端 skill。

**版本 0.1.0。** 这是独立维护的工作流 skill，不是 OpenAI 或 Google 官方产品，也不是 MCP 服务或一键桥接安装器。使用它仍需已有可用的桥接与原生权限；不需要 Claude，不用 CLI 会话替代桌面对话。

## 能做什么

- 查询连接状态，区分服务就绪、消息接受、收到回复和任务完成。
- 查找并确认现有目标对话，按用户授权发送任务并取回结果。
- 超时后沿原请求继续查询，避免重复派单和双方循环确认。
- 用可选只读脚本检查本地入口、配置及已导出的状态 JSON。

不会自动安装 MCP、修改权限、启动服务、创建对话、执行历史实验或把其他项目的上下文传给对方。

## 安装到两端

1. 下载 GitHub Releases 中的 skill ZIP，或克隆本仓库。
2. 确认各自应用实际识别的 skill 目录。将文件放成 `<skill-root>/codex-antigravity-dialogue/SKILL.md`，同时保留 `references`、`scripts` 和 `agents`。
3. 两端使用相同版本。已有同名 skill 时先检查差异，不覆盖个人修改。
4. 刷新宿主支持的 skill 列表或在下一次会话确认发现情况。磁盘有文件不代表当前会话已加载。

不同应用版本的目录约定可能变化，详见 [安装说明](references/installation.md)。ZIP 不包含桥接代码、凭据或后台服务。

## 使用示例

Codex 可显式调用 `$codex-antigravity-dialogue`；反重力使用其支持的 skill 调用方式或指明 skill 名。

```text
用 codex-antigravity-dialogue 看看连接状态，不要发送消息。

给已经确认的反重力对话做一次 echo 测试，不改文件、不运行实验。

把已选文件交给已确认的 Codex 对话，只读审阅并返回结论。

继续查询刚才的请求，不要重新派单。
```

目标由当前项目、对话身份和在线工具结果确认，不写死路径或对话 ID。实际发送前必须具有对应任务和接收方的授权。

## 只读诊断

可选脚本使用 Python 3.11+，仅依赖标准库。以下命令在仓库或已安装 skill 目录中运行，将占位路径替换为当前应用实际使用的配置：

```powershell
python scripts/doctor.py --host codex --config "<active-config.toml>"
python scripts/doctor.py --host antigravity --config "<active-mcp_config.json>"
```

脚本也可分析已经导出的状态或回执；输入格式和退出码见 [诊断说明](references/diagnostics.md)。它不会联网或发送测试消息，因此无法单独证明两端已打通。输出会明确标注 `live_probe_performed=false` 和 `task_completion=not_verified`。

## 兼容范围与验证

历史上，一套经过本地兼容修正的 Windows bridge 2.3.2 完成过双向通信。**这不等于未修改的上游包、其他系统或其他 Desktop 版本均已通过。** 详见 [兼容与证据范围](references/compatibility.md)。

仓库提供两类检查，不能混为一谈：

- 自动测试：验证诊断脚本、输入处理、回执关联和文件打包；不连接真实 Agent。
- [8 个行为评估场景](evals/scenarios.json)：用于检查 Agent 在歧义、超时、忙碌、权限失败及回调场景中的决策。它们是测试输入与预期，不是已通过的模型评估结果。

开发者在仓库根目录执行：

```powershell
python -m unittest discover -s tests -v
python scripts/package.py
```

GitHub Actions 配置了 Windows/Linux、Python 3.11/3.13 的离线测试。是否通过以对应提交的实际运行结果为准。测试不用账号、凭据、聊天记录或活跃桥接。

评估 Agent 行为时，以模拟工具返回代替真实发送，核对 `expected` 与 `forbidden`。不要把这些评估提示直接发送到生产对话。真实双向测试须另外确认测试接收方和发送授权。

## 设计参考

仅借鉴工作流组织方式，没有复制或捆绑其他项目的运行代码：

- [Agent Relay skills](https://github.com/AgentWorkforce/skills)：接收方发现、消息交换和任务交接。
- [Anthropic skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator)：明确触发条件、按需加载参考资料和真实场景评估。
- [Codex MCP Bridge](https://github.com/buidangminh23/codex-mcp-bridge)：本 skill 针对的底层桥接项目，独立安装和维护。

本仓库采用 [MIT License](LICENSE)。上游软件遵循其各自许可。
