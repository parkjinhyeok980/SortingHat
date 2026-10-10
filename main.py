"""python main.py: UI 없이 재현 가능한 집계 보고서 생성."""
import json
from analysis.preprocessing import prepare, ROOT
from analysis.eda import add_bands, rates
from analysis.statistical_tests import run_tests
from analysis.logistic_regression import fit_logistic
from analysis.decision_tree import fit_tree
from analysis.retention import actions


def main():
    df, audit = prepare()
    output = ROOT / 'reports'
    output.mkdir(exist_ok=True)
    audit['schema'].to_csv(output / 'data_quality.csv', index=False)
    audit['outliers'].to_csv(output / 'outlier_diagnostics.csv', index=False)
    metadata = {k: v for k, v in audit.items() if k not in ['schema', 'outliers']}
    metadata.update(leavers=int(df.Attrition.sum()), attrition_rate=float(df.Attrition.mean()))
    (output / 'summary.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    run_tests(df).to_csv(output / 'statistical_tests.csv', index=False, encoding='utf-8-sig')
    logistic = fit_logistic(df)
    logistic['table'].to_csv(output / 'odds_ratios.csv', index=False)
    logistic['vif'].to_csv(output / 'vif.csv', index=False)
    tree = fit_tree(df)
    tree['rules'].to_csv(output / 'tree_rules.csv', index=False)
    (output / 'tree.txt').write_text(tree['text'], encoding='utf-8')
    actions(df).to_csv(output / 'retention_actions.csv', index=False, encoding='utf-8-sig')
    banded = add_bands(df)
    for c in ['Department', 'JobRole', 'JobLevel', 'TenureBand', 'OverTime', 'JobSatisfaction', 'IncomeBand', 'PromotionBand']:
        if c in banded:
            rates(banded, c).to_csv(output / f'rates_{c}.csv', index=False)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    print('Reports:', output)


if __name__ == '__main__':
    main()
