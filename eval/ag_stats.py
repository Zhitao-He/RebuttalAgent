import numpy as np
from scipy import stats
import json
import pandas as pd
import matplotlib.pyplot as plt
def mean_absolute_error(y_true, y_pred):
    """
    计算平均绝对误差（MAE）
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return np.mean(np.abs(y_true - y_pred))

def pearson_correlation(y_true, y_pred):
    """
    计算Pearson相关系数
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    r, _ = stats.pearsonr(y_true, y_pred)
    return r

def spearman_correlation(y_true, y_pred):
    """
    计算Spearman等级相关系数
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    rho, _ = stats.spearmanr(y_true, y_pred)
    return rho

def kendall_correlation(y_true, y_pred):
    """
    计算Kendall秩相关系数
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    tau, _ = stats.kendalltau(y_true, y_pred)
    return tau
def fuzzy_division_score(human_scores, model_scores):
    """
    计算 fuzzy division 命中率。
    :param human_scores: List[int] 人类标注的分数
    :param model_scores: List[int] 模型分数
    :return: float 命中率
    """
    def get_fuzzy_range(score):
        if 0 <= score <= 2:
            return 0  # Unfollow
        elif 3 <= score <= 5:
            return 1  # Bad
        elif 6 <= score <= 8:
            return 2  # Good
        elif 9 <= score <= 10:
            return 3  # Excellent
        else:
            raise ValueError("Score out of valid range (1-10): {}".format(score))
    
    assert len(human_scores) == len(model_scores)
    correct = 0
    for h, m in zip(human_scores, model_scores):
        if get_fuzzy_range(h) == get_fuzzy_range(m):
            correct += 1
    return correct / len(human_scores)
def strict_division_score(human_scores, model_scores):
    """
    计算 strict division 命中率。
    :param human_scores: List[int] 人类标注分数
    :param model_scores: List[int] 模型分数
    :return: float 命中率
    """
    def get_strict_range(score):
        if 0<= score <= 1:
            return 0
        elif score == 2:
            return 1
        elif score == 3:
            return 2
        elif 4 <= score <= 5:
            return 3
        elif score == 6:
            return 4
        elif 7 <= score <= 8:
            return 5
        elif 9 <= score <= 10:
            return 6
        else:
            raise ValueError("Score out of valid range (1-10): {}".format(score))
    
    assert len(human_scores) == len(model_scores)
    correct = 0
    for h, m in zip(human_scores, model_scores):
        if get_strict_range(h) == get_strict_range(m):
            correct += 1
    return correct / len(human_scores)
def compute_metrics(y_true, y_pred):
    """
    计算四个指标，返回字典
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    mae = np.mean(np.abs(y_true - y_pred))
    pearson_r, _ = stats.pearsonr(y_true, y_pred)
    spearman_r, _ = stats.spearmanr(y_true, y_pred)
    kendall_tau, _ = stats.kendalltau(y_true, y_pred)
    fuzzy = fuzzy_division_score(y_true,y_pred)
    strict = strict_division_score(y_true,y_pred)

    return {
        "MAE": mae,
        "Pearson_r": pearson_r,
        "Spearman_rho": spearman_r,
        "Kendall_tau": kendall_tau,
        "FuzzyAcc": fuzzy,
        "StrictAcc": strict
    }


def dataframe_to_image(df, filename='df_table.png'):
    fig, ax = plt.subplots(figsize=(len(df.columns)+2, len(df)*0.6 + 1))  # 动态调整图片大小
    ax.axis('off')  # 不显示坐标轴
    table = ax.table(cellText=df.round(3).values, colLabels=df.columns, rowLabels=df.index,
                     cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.auto_set_column_width(col=list(range(len(df.columns))))
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()
#with open(f"reward_test.json", 'r',encoding='utf-8') as file:
 #   labels = json.load(file)

model = "claude-3-5-sonnet-20240620"
with open(f'ag_test/{model}.json','r',encoding='utf-8') as file:
     outputs = json.load(file)






dimensions = ["Attitude", "Clarity", "Persuasiveness", "Constructiveness"]

results = {}
for dim in dimensions:
    y_pred = [item["output1"]["score"][dim] for item in outputs if "output1" in item]
    y_true = [item["output"]["score"][dim] for item in outputs if "output1" in item]
    print(len(y_pred))
    print(len(y_true))
    metrics = compute_metrics(y_true, y_pred)
    results[dim] = metrics

# 打印结果
for dim in dimensions:
    print(f"{dim}:")
    for metric, value in results[dim].items():
        print(f"  {metric}: {value:.4f}")
metrics = ["MAE", "Pearson_r", "Spearman_rho", "Kendall_tau", "FuzzyAcc", "StrictAcc"]
df = pd.DataFrame(results).T[metrics]  # 转置为行：维度，列：指标
print(df.to_markdown())  
dataframe_to_image(df, f'metrics/{model}.png')