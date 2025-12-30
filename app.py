import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# --- 1. データ準備 (サンプルデータの生成) ---
# 実際の使用時は、ここをご自身のデータ(CSVなど)から読み込む処理に置き換えてください。
np.random.seed(42) # 再現性のため乱数シードを固定
conditions = ['DMSO', 'X', 'Y']
groups = ['Control', 'A']
data = []

# 各条件・グループごとに、正規分布に従うランダムなデータを生成
for cond in conditions:
    for group in groups:
        # 画像の傾向に合わせて平均値(loc)と標準偏差(scale)を設定
        if cond == 'DMSO':
            if group == 'Control': values = np.random.normal(loc=410, scale=30, size=10)
            else:                  values = np.random.normal(loc=180, scale=25, size=10)
        elif cond == 'X':
            if group == 'Control': values = np.random.normal(loc=490, scale=35, size=10)
            else:                  values = np.random.normal(loc=210, scale=30, size=10)
        else: # Condition Y
            if group == 'Control': values = np.random.normal(loc=400, scale=30, size=10)
            else:                  values = np.random.normal(loc=390, scale=30, size=10)
        
        for v in values:
            data.append({'Condition': cond, 'Group': group, 'Value': v})

df = pd.DataFrame(data)

# --- 2. グラフの描画 ---
# seabornのスタイル設定（背景を白、軸をシンプルに）
sns.set_style("ticks")
fig, ax = plt.subplots(figsize=(8, 6)) # グラフのサイズ指定

# a) 棒グラフとエラーバーの描画
# ci='sd' でエラーバーを標準偏差に設定 (標準誤差なら ci=68 など)
# capsizeでエラーバーの横線の長さを指定
sns.barplot(x='Condition', y='Value', hue='Group', data=df,
            palette={'Control': 'gray', 'A': '#69f0ae'}, # 色を指定
            edgecolor='black', linewidth=1, capsize=0.1, errwidth=1.5, ci='sd', ax=ax)

# b) 個別データポイント (stripplot) の重ね書き
# dodge=True で棒グラフの位置に合わせてポイントをずらす
sns.stripplot(x='Condition', y='Value', hue='Group', data=df,
              palette={'Control': 'white', 'A': 'white'}, # ポイントの中を白く
              edgecolor='gray', linewidth=1, size=6, jitter=True, dodge=True, ax=ax)

# --- 3. 有意差の注釈 (アスタリスクと線) ---
# 手動で座標を指定して描画します。自動化も可能ですが、配置の微調整が必要なため手動が確実です。
# 線の高さやテキストの位置はデータに合わせて調整が必要です。

# DMSOの有意差 (****)
y_line = 450 # 線の高さ
h = 10       # 線の両端の小さな縦線の高さ
ax.plot([-0.2, 0.2], [y_line, y_line], lw=1, color='black') # 横線
ax.text(0, y_line + h, "****", ha='center', va='bottom', fontsize=16)

# Xの有意差 (****)
y_line = 510
ax.plot([0.8, 1.2], [y_line, y_line], lw=1, color='black')
ax.text(1, y_line + h, "****", ha='center', va='bottom', fontsize=16)

# Yの有意差 (N.S.)
y_line = 460
ax.plot([1.8, 2.2], [y_line, y_line], lw=1, color='black')
ax.text(2, y_line + h, "N.S.", ha='center', va='bottom', fontsize=12)


# --- 4. その他の調整 ---
ax.set_ylabel("Number of cells", fontsize=14) # Y軸ラベル
ax.set_xlabel("") # X軸ラベルは条件名で十分なので空にする
ax.set_ylim(0, 600) # Y軸の範囲

# 凡例の調整（stripplotの分が重複するので削除）
handles, labels = ax.get_legend_handles_labels()
# 最初の2つ(barplotの凡例)だけを表示
ax.legend(handles[:2], labels[:2], title='', loc='center left', bbox_to_anchor=(1, 0.5), frameon=False, fontsize=12)

# 不要な枠線を消す
sns.despine()
# 軸の目盛りのフォントサイズ調整
ax.tick_params(labelsize=12)

plt.tight_layout() # レイアウトの自動調整
plt.show() # グラフを表示 (ファイルに保存する場合は plt.savefig('plot.png') )
