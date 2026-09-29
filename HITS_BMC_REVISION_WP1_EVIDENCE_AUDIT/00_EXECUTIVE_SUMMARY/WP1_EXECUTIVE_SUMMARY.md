# HITS BMC Revision WP1

Date:2026-09-29. User-reported revision requested; submission ID fa1e4873-011b-4f15-8b0d-29f6df21fabe. Internal deadline2026-10-10; journal deadline2026-10-12 (user instruction, not portal-verified).

## Gate
**WP1_HOLD_DUE_TO_SOURCE_DATA_GAP**

已完成本地证据恢复与描述性审计，不修改manuscript、不重跑Core/Enhanced、不新增DCA/校准/共线性模型、不生成图。22条意见已建矩阵，原始评审信未恢复，不能将摘要伪装成逐字原文。

## 三个首要问题
1. **研究期/日期来源**：当前实际输入CBC年份与2020-2026稿件入组期冲突，1802/1820早于2019；±182天无法解释。平移程序输入/输出和模型输入尚未形成验证链。
2. **图表和预测版本混用**：Table2来自verified10次CV；可恢复的Figure3/ROC脚本使用legacy20次OOF。Canonical代码没有保存患者预测。必须恢复准确来源，不允许用近似AUC替代。
3. **伦理/年龄证据缺口**：知情同意须作者文件确认；稿件年龄1818与当前代码及历史输出1820不一致，不能假定已修复。

## 冻结保护
主队列1820、AMI453、non-AMI1367重现；冻结AUC和CI只读取。数值仍保留原值，但源证据缺口影响其可解释性。PDW维持DROP、Core7架构不变。本仓库仅汇总、代码和短摘录，不含患者级数据。公开仓库由用户明确授权，PR保持OPEN不合并。

## 34项直接回答
1. CBC来自按诊断存在、四项CBC非缺失数、WBC时间存在、qc完整度及原始行序排序后选中的同一宽表行；不是最早CBC规则。

2. Admission仅130/1820有日期；CBC差值中位数-1754.205天，无法认作同次住院时序。造影/首次诊断时间未恢复；TIMING_RECONSTRUCTION=NOT_FEASIBLE（当前材料）。

3. Fbg时间1707，数值1705；与CBC同日1553/1707。可计算检验间差值，但不能证明同次入院/术前。

4. 直接来源是discharge_diagnosis文本规则；不是肌钙蛋白或ECG裁定。

5. 没有找到独立医生复核的可核验证据，不能声称已完成。

6. 2010人各1行、269人各2行；269条是同ID多余行，整行完全重复0；没有证据称其均为独立重复住院。

7. 多行患者269；可靠重复住院人数UNKNOWN。17组有一个入院日期，252组无日期，无组有两个不同非缺失入院日期。

8. 精确排序见第1项；时间只判断有无，不按先后；qc_nonmissing_count的上游组件未恢复。

9. 诊断可用性参与选择，存在选择偏倚风险；未见按AMI标签/模型效果择行。269组均没有两条竞争的非空诊断。

10. Canonical outer5折x10次，inner5折，elastic-net l1_ratio0.25/0.5/0.75，C0.1/1/10；单指标无需调参。

11. 拟合中位数/中心/标准差及调参局限在训练折；固定转换先验指定。代码层成立，不代表上游选择/时序无偏。

12. 每人10个OOF概率取算术平均，再计算患者层性能；重复AUC分布另报。

13. 1000次抽样固定的患者平均OOF预测及其结局；配对比较同抽患者；无模型重拟合、无重分折、无新预测。

14. 较早组训练、较晚组固定验证；development内另有3次CV参考，不是later组内CV。日期来源仍未证实。

15. 早期1001/196 AMI，缓冲271/79，后期548/178；源CBC有1802人早于2019，与稿件2020-2026冲突待回源。

16. 453-196早期-79缓冲=178后期；再排40条不符高特异文本规则=138；对照288，总426。

17. 使用出院后汇总诊断信息；阳性规则不使用肌钙蛋白、ECG或治疗证据，strict对照可含血运重建文字。

18. AMI缺27/453=5.9603%；non-AMI缺88/1367=6.4375%；总115/1820=6.3187%。

19. 代码层同人同fold并配对：1705人、426 AMI；既存完整病例delta0.009678，CI0.002300-0.016932。

20. 性别0缺；高血压79缺（AMI18/对照61）；糖尿病48缺（11/37）。稿件年龄1818可用（452/1366），当前Python及历史canonical为1820；不擅自覆盖，待恢复修正来源。

21. 四临床模型N/AMI/AUC/CI/Brier/校准均有；对Clinical基础模型的配对增量CI和内部Enhanced对PIV增量CI未恢复。数字存在不等于年龄版本一致。

22. Table2为canonical10次平均OOF；Figure3溯源指向legacy20次平均OOF。不能称同一预测集；需回收canonical预测修复图源。

23. Figure5前三类各3模型共9个AUC CI已有；alternative/asymmetric3个只有AUC，无单模型CI；deltaCI不能替代。

24. 有300次full-development bootstrap系数/选择频率/符号稳定性和部分Hb诊断；完整Core7相关矩阵/VIF未恢复，本轮未新算。

25. NLR/PLR/MLR/SII/SIRI/PIV/HRR均有主及strict验证AUC/CI；保留PIV为主要比较。

26. 内部PIV为log1p+训练标准化+单变量无惩罚logistic，同人同outer折；时间验证为raw ordinal AUC，不是校准概率。

27. NOT_VALID_FOR_UNIFIED_MODEL：cTnI173、cTnT88、hs-cTnT390原始结果非空，平台/ULN/有效index时序未恢复；不直接相加或合并。

28. 不能有证据地称consecutive；入组筛查台账、完整造影母队列及ETL未恢复。

29. AUTHOR_DOCUMENT_CONFIRMATION_REQUIRED；批准号/稿件声明不是知情同意文件证明。

30. 当前不能用有效canonical既存预测直接做新DCA：canonical未保存，legacy虽存在不可替代；需恢复或另行授权再生。

31. E2/E3/E4/E6/E7/E10/R1-M4/R1-M6主要可整理已有证据；仍受源数据/表述边界限制。

32. 获授权后可做Spearman、未有CI/配对CI、canonical分布/分组数及条件性DCA；canonical预测再生属于需单独授权的重分析。

33. 作者需确认伦理与同意、真实研究期/筛查范围/日期平移、实验室与住院时序、年龄修正及实际投稿/原始评审文件。

34. WP1_HOLD_DUE_TO_SOURCE_DATA_GAP；审计交付完成不等于返修可提交。未进入WP2。

## 审阅入口
- REVIEWER_COMMENT_MASTER_MATRIX.csv:22条评论、证据及后续动作。
- REVISION_RISK_REGISTER.csv:14项风险，包含新发现的版本与来源冲突。
- ../08_REVISION_PLANNING/WP2_ANALYSIS_AUTHORIZATION_PLAN.md:需审阅批准，不构成授权。
- ../09_CODE/evidence/CANONICAL_RESULT_REGISTRY.csv:原冻结数字；../09_CODE/SOURCE_MANIFEST.csv:源文件校验。

复现范围：有权限的本地源文件持有者可重跑09_CODE描述性审计；公开仓库不可能在没有受控原始数据时重建患者级分析。未以不存在的文件宣称完全复现。
