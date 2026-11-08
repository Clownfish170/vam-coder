#!/usr/bin/env python
"""VSO 场景矩阵生成器（冻结设计 v2 §3/§4 的机器可读版）。
输出 scenario_matrix.csv（唯一副作用 + 打印统计）。"""

from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 列：id, layer, sample_class, initial_state, injection, expected_behavior,
#      expected_decision, b1_expected, b2_expected, machine_check, e2e, phase2
NEG, POS, CTRL = "negative", "positive", "false_block_control"
BOUNDARY = "boundary"
ALLOW, FORCE, INSUF = "ALLOW_OMISSION", "FORCE_FULL", "INSUFFICIENT"
BLK = "BLOCK"

ROWS: list[dict] = []


def R(**kw):
    ROWS.append(kw)


# ---------------- Layer V（可见性证明层）—— B1/B2/VSO 三机制预期
R(id="V1", layer="visibility", sample_class=NEG,
  initial_state="tracker 持旧版本 sha；磁盘文件已变更",
  injection="构造 tracker._files[rel]=old_sha，磁盘为 new_content（函数级注入）",
  expected_behavior="证明过期 → 拒绝省略，全量交付",
  expected_decision=FORCE, b1_expected="allow", b2_expected="deny",
  machine_check="safe_omission reasons 含 no_visible_proof_in_messages；最终 messages 含 new 内容",
  e2e=1, phase2=1)
R(id="V2", layer="visibility", sample_class=NEG,
  initial_state="目标文件无任何可见性记录",
  injection="清空 tracker 中该文件条目",
  expected_behavior="证明缺失 → 拒绝省略",
  expected_decision=FORCE, b1_expected="allow", b2_expected="deny",
  machine_check="safe_omission 拒绝；信息经全量路径出现在最终 messages",
  e2e=0, phase2=0)
R(id="V3", layer="visibility", sample_class=NEG,
  initial_state="证明条目 sha ≠ 当前文件 sha（记录被篡改）",
  injection="tracker._files[rel]=forged_sha；desired=磁盘真实 sha",
  expected_behavior="证明与实际不一致 → 拒绝省略",
  expected_decision=FORCE, b1_expected="allow", b2_expected="deny",
  machine_check="safe_omission 拒绝（hash 不匹配）",
  e2e=0, phase2=0)
R(id="V4", layer="visibility", sample_class=NEG,
  initial_state="同 sha 曾发送，但对应 assistant 消息不在最终 messages（历史裁剪）",
  injection="tracker 保留证明；构造最终 messages 缺失该 FILE 块；omitted 含该文件",
  expected_behavior="可见性不成立 → 最终验证失败 → 回退全量（VSO 独占检出：B1/B2 均会授权）",
  expected_decision=FORCE, b1_expected="allow", b2_expected="allow",
  machine_check="verify_omissions_in_messages.ok=False（not_in_final_messages）；回退后信息在最终 messages；EDR 独占计数+1",
  e2e=1, phase2=1)
R(id="V5", layer="visibility", sample_class=NEG,
  initial_state="多步链中外部修改覆盖文件，tracker 仍持旧证明",
  injection="step 间改写磁盘文件；不更新 tracker",
  expected_behavior="按当前 sha 验证失败 → 拒绝省略",
  expected_decision=FORCE, b1_expected="allow", b2_expected="deny",
  machine_check="safe_omission 拒绝；回退全量",
  e2e=0, phase2=1)

# ---------------- Layer C（约束与预算层）
R(id="C1", layer="constraint_budget", sample_class=NEG,
  initial_state="must（非编辑目标）文件进入省略候选且【无可见性证明】；E⊆M 成立",
  injection="构造 plan 候选含 must 文件 + 清空其证明",
  expected_behavior="must 不被绕过 → 拒绝省略、全量交付（有证明的 must 省略按冻结 RSR 定义属允许，不在本负向样本）",
  expected_decision=FORCE, b1_expected="allow", b2_expected="deny",
  machine_check="must 文件出现在最终 messages；omitted∩must=∅；E⊆M",
  e2e=1, phase2=1)
R(id="C2", layer="constraint_budget", sample_class=NEG,
  initial_state="edit target 同时被标为可省略（target/检索/省略三方冲突）",
  injection="绕过 assemble 排除规则，直接以 safe_omission 授权 target",
  expected_behavior="r2.2 优先：target 必须在当前 CONTEXT 全量 → 最终验证失败 → 回退全量",
  expected_decision=FORCE, b1_expected="allow", b2_expected="allow",
  machine_check="verify: edit_target 在当前 context 且 hash=disk；DHO=0",
  e2e=0, phase2=1)
R(id="C3", layer="constraint_budget", sample_class=NEG,
  initial_state="装配所需 tokens > context_window",
  injection="构造 plan.required_context_tokens_est=9000（window=8192）",
  expected_behavior="预算耗尽 ≠ 可安全省略 → INSUFFICIENT，不发请求",
  expected_decision=INSUF, b1_expected="NA", b2_expected="NA",
  machine_check="ctx.insufficient=True；requests=0；reasons 含 REQUIRED_CONTEXT_EXCEEDS_LIMIT",
  e2e=1, phase2=1)
R(id="C4", layer="constraint_budget", sample_class="boundary",
  initial_state="装配预算超限但仅可选内容超、must 可容纳",
  injection="构造 optional 超 budget_tokens 的 plan（must 在内）",
  expected_behavior="仅可选按既有规则被丢弃；must 全量；不产生 INSUFFICIENT",
  expected_decision=ALLOW, b1_expected="allow", b2_expected="NA",
  machine_check="dropped_optional_digest/optional 非空且 must 全在最终 messages；over_budget 标记；此样本为『允许省略（仅可选）』的受控负向边界",
  e2e=0, phase2=0)

# ---------------- Layer H（历史与信息完整性层）
R(id="H1", layer="history_integrity", sample_class=NEG,
  initial_state="单条 assistant 消息内容损坏（结构完整）",
  injection="向 history 注入 FILE 块但 body 篡改（hash≠磁盘）；tracker_from_history 构建证明",
  expected_behavior="该条不得授权省略 → 回退全量；不静默使用损坏历史",
  expected_decision=FORCE, b1_expected="allow", b2_expected="deny",
  machine_check="proof hash≠disk → safe_omission 拒绝；回退后最终 messages 含磁盘内容",
  e2e=1, phase2=1)
R(id="H2", layer="history_integrity", sample_class=NEG,
  initial_state="history 不可恢复（截断至仅 system / 角色错乱）",
  injection="构造 history=[system] 或 role 顺序损坏",
  expected_behavior="无任何省略授权 → 回退全量（不静默）",
  expected_decision=FORCE, b1_expected="allow", b2_expected="deny",
  machine_check="tracker 无证明 → 拒绝省略；信息经全量交付",
  e2e=0, phase2=1)
R(id="H3", layer="history_integrity", sample_class=NEG,
  initial_state="must 文件从磁盘缺失",
  injection="删除临时工作区中该文件后调用装配",
  expected_behavior="MISSING_REQUIRED_FILE → INSUFFICIENT，不发请求",
  expected_decision=INSUF, b1_expected="NA", b2_expected="NA",
  machine_check="ctx.insufficient=True；reasons 含 MISSING_REQUIRED_FILE；requests=0",
  e2e=0, phase2=0)
R(id="H4", layer="history_integrity", sample_class=NEG,
  initial_state="构造 omitted∩edit_targets 非空的企图",
  injection="以 omisssion 列表夹带 edit_target 调用最终验证（冻结 DHO 公式计量）",
  expected_behavior="发送前拦截 → 回退；attempted_dho>0 且 final_dho=0",
  expected_decision=FORCE, b1_expected="allow", b2_expected="allow",
  machine_check="attempted_dho≥1；final_dho==0（冻结公式）；target 在最终 messages",
  e2e=0, phase2=0)
R(id="H5", layer="history_integrity", sample_class=NEG,
  initial_state="动态信息已更新但未重新证明，仍尝试省略",
  injection="更新文件内容后保留旧证明并尝试省略",
  expected_behavior="更新内容必须重新验证与交付 → 拒绝省略",
  expected_decision=FORCE, b1_expected="allow", b2_expected="deny",
  machine_check="safe_omission 拒绝；新内容出现在最终 messages",
  e2e=0, phase2=0)

# ---------------- 正向安全省略 P1–P9（互异条件）
POS_DEFS = [
    ("P1", "近期可见：上一步 assistant FILE 回写、文件未变", "mark_from_assistant(上一步) + 同内容省略"),
    ("P2", "跨步可见：证明来自 k−2 步、中间无修改", "两步前 assistant FILE + 两次空步后省略"),
    ("P3", "多文件批：3 文件各自独立证明后同时省略", "3×mark_from_assistant + omitted=[3文件]"),
    ("P4", "混合批：1 省略 + 1 全量 edit target 共存", "1 文件省略证明 + target 在当前 context 全量"),
    ("P5", "动态更新正向：本步更新后新 sha 重新证明再省略", "assistant 回写新内容 → 按新 sha 省略"),
    ("P6", "模型输出回写：文件=最新 assistant FILE 块", "文件内容与最新 assistant 回写一致"),
    ("P7", "O′/REUSE 正常路径：缓存命中且最终 messages 含同内容", "safe_omission 返回 O_prime=visible_hash_match"),
    ("P8", "长历史：证明位于 trim 预算内仍可见", "20 条历史后证明仍在 messages"),
    ("P9", "must 邻接非 must：相关非目标文件已证明", "非 must 相关文件按证明省略"),
]
for pid, cond, inj in POS_DEFS:
    R(id=pid, layer="positive_boundary", sample_class=POS,
      initial_state=cond, injection=inj,
      expected_behavior="证明成立且未变 → 允许省略（防全不省略刷分）",
      expected_decision=ALLOW, b1_expected="allow", b2_expected="allow",
      machine_check="safe_omission.allow=True；verify_omissions_in_messages.ok=True；信息在最终 messages",
      e2e=0,  # 冻结设计 §4：e2e 子集仅 V4/V1/C1/C3/H1
      phase2=(1 if pid in ("P1", "P5") else 0))

# ---------------- 假阻断对照 FP1–FP8（正向无故障独立实例，不同合成文件）
for i in range(1, 9):
    R(id=f"FP{i}", layer="false_block_control", sample_class=CTRL,
      initial_state=f"无故障正向实例 #{i}（独立合成文件 ctrl_{i}.py）",
      injection="无（对照运行）",
      expected_behavior="不得被误阻断",
      expected_decision=ALLOW, b1_expected="allow", b2_expected="allow",
      machine_check=f"observed==ALLOW_OMISSION；ctrl_{i}.py 经正常省略路径",
      e2e=0, phase2=0)

PHASE2 = {"V1", "V4", "C1", "C2", "C3", "H1", "H2", "V5", "P1", "P5"}
E2E = {r["id"] for r in ROWS if r.get("e2e") == 1}
for r in ROWS:
    r["e2e"] = int(r["id"] in {"V4", "V1", "C1", "C3", "H1"})
    r["phase2"] = int(r["id"] in PHASE2)
    # 统一 deny/allow 词表
    for k in ("b1_expected", "b2_expected"):
        v = r.get(k, "NA")
        r[k] = {"deny": "block", "allow": "allow", "NA": "NA"}.get(v, v)

FIELDS = ["id", "layer", "sample_class", "initial_state", "injection",
          "expected_behavior", "expected_decision", "b1_expected", "b2_expected",
          "machine_check", "e2e", "phase2"]
out = HERE / "scenario_matrix.csv"
with out.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(ROWS)

neg = sum(1 for r in ROWS if r["sample_class"] == NEG)
pos = sum(1 for r in ROWS if r["sample_class"] == POS)
ctrl = sum(1 for r in ROWS if r["sample_class"] == CTRL)
bnd = sum(1 for r in ROWS if r["sample_class"] == "boundary")
print(f"scenario_matrix.csv written: total={len(ROWS)} negative={neg} positive={pos} control={ctrl} boundary={bnd}")
assert neg == 13 and pos == 9 and ctrl == 8, (neg, pos, ctrl)
print(f"e2e subset={sorted(r['id'] for r in ROWS if r['e2e']==1)}")
print(f"phase2 frozen={sorted(r['id'] for r in ROWS if r['phase2']==1)}")
