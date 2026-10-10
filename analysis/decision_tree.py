"""깊이 3의 탐색적 규칙. 학습/검증을 분리하고 개인 예측은 노출하지 않는다."""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text
from analysis.logistic_regression import design


def fit_tree(df):
    complete, x, _ = design(df)
    if complete.Attrition.value_counts().min() < 10 or len(complete) < 100:
        raise ValueError('트리 학습/검증을 위한 표본이 부족합니다.')
    train, valid = train_test_split(complete.index, test_size=.3, stratify=complete.Attrition, random_state=42)
    # 최소 리프 40명: 작은 집단의 과도한 규칙 생성을 억제한다.
    model = DecisionTreeClassifier(max_depth=3, min_samples_leaf=40, random_state=42)
    model.fit(x.loc[train], complete.loc[train, 'Attrition'])
    paths = {}
    def walk(node, rules):
        tree = model.tree_
        if tree.children_left[node] == tree.children_right[node]:
            paths[node] = ' AND '.join(rules) or '전체'
            return
        feature = x.columns[tree.feature[node]]
        threshold = tree.threshold[node]
        walk(tree.children_left[node], rules + [f'{feature} ≤ {threshold:.6g}'])
        walk(tree.children_right[node], rules + [f'{feature} > {threshold:.6g}'])
    walk(0, [])
    rows = []
    for split, ids in [('train', train), ('validation', valid)]:
        data = pd.DataFrame({'leaf': model.apply(x.loc[ids]), 'Attrition': complete.loc[ids, 'Attrition'].to_numpy()})
        for leaf, group in data.groupby('leaf'):
            rows.append({'split': split, 'leaf': int(leaf), 'rule': paths[leaf], 'n': len(group),
                         'leavers': int(group.Attrition.sum()), 'rate': group.Attrition.mean()})
    importance = pd.DataFrame({'variable': x.columns, 'importance': model.feature_importances_}).sort_values('importance', ascending=False)
    return {'model': model, 'features': list(x.columns), 'rules': pd.DataFrame(rows),
            'importance': importance, 'text': export_text(model, feature_names=list(x.columns)),
            'train_base': complete.loc[train, 'Attrition'].mean(), 'validation_base': complete.loc[valid, 'Attrition'].mean()}
