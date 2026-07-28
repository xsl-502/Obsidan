clear all
set more off

* 修改为你的本地路径
cd "/Users/xsl/Desktop/Obsidian/经管毕业论文"

import delimited "02_数据集/基准回归样本_流动性风险_2014-2023.csv", clear encoding(UTF-8)

encode bank_name, gen(bank_id)
xtset bank_id year

* 描述性统计
summarize liquidity_risk liquidity_ratio dfi_index dfi_breadth dfi_depth dfi_digitization ///
    capital_adequacy_ratio npl_ratio cost_income_ratio roa roe ln_total_assets

* 相关性分析
pwcorr liquidity_risk dfi_index capital_adequacy_ratio npl_ratio cost_income_ratio, sig

* 基准回归：逐步加入控制变量和固定效应
reg liquidity_risk dfi_index, robust
est store m1

reg liquidity_risk dfi_index capital_adequacy_ratio npl_ratio cost_income_ratio, robust
est store m2

reg liquidity_risk dfi_index capital_adequacy_ratio npl_ratio cost_income_ratio i.year, robust
est store m3

xtreg liquidity_risk dfi_index capital_adequacy_ratio npl_ratio cost_income_ratio i.year, fe robust
est store m4

* 分维度回归
xtreg liquidity_risk dfi_breadth capital_adequacy_ratio npl_ratio cost_income_ratio i.year, fe robust
est store d1

xtreg liquidity_risk dfi_depth capital_adequacy_ratio npl_ratio cost_income_ratio i.year, fe robust
est store d2

xtreg liquidity_risk dfi_digitization capital_adequacy_ratio npl_ratio cost_income_ratio i.year, fe robust
est store d3

* 加入可选控制变量的稳健性检验：样本会进一步缩小
xtreg liquidity_risk dfi_index capital_adequacy_ratio npl_ratio cost_income_ratio roa ln_total_assets i.year, fe robust
est store r1

* 如已安装 esttab，可导出结果
* esttab m1 m2 m3 m4 d1 d2 d3 r1 using "02_数据集/基准回归结果.rtf", replace se star(* 0.1 ** 0.05 *** 0.01)

