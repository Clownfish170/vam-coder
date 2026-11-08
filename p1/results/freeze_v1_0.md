# P1-v1.0 冻结报告（必须层）

- 冻结时间：2026-10-30（资格测试同日）
- git commit：`155f934bc6c565bd304b2b7438259d592bc348c8`（分支 p1/v0.2；**未打 tag**——版本管理动作层待用户授权）
- 工作树：含未提交的 p1/v1.0 新增文件（见 git status；不重置用户工作区）
- task_set_version：`p1-v1.0.0-rc1`
- manifest：`p1/manifests/p1_v1.0_manifest_20261030.json`
  sha256=`e82072f4c222e9927762b383a1e344bcd799d5f08c38486665d7eed8cca696df`
- 预声明表：`p1\tasks\predeclared_mechanisms_v1.0.json` sha256=`20491be687c3b3c216d3e4e6649dcb3d9285e61b74e4b46455e4d1fd0a3ed732`
- 资格 run：`v1_qual_rep0_20261030_233659`（判定层修订后重判，见 qualification_report/diagnosis）
- 资格标签：OK=11 REVIEW=10（全部诊断为模型违例）CAP=2 TRIVIAL=1 EXCLUDE=0
- 服务端：llama-server（/version 404 → version=unknown）；模型 q6_k GGUF sha256 见 run_meta
- 未执行：git commit/tag/push（需用户授权）；Block A/B 正式实验（需用户授权 R 与预算）
