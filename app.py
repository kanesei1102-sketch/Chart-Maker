import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io

# ---------------------------------------------------------
# 1. ページの設定
# ---------------------------------------------------------
st.set_page_config(page_title="Bar Plot Maker", layout="wide")

st.title("📊 科学論文風 棒グラフ作成ツール")
st.markdown("""
Excelやスプレッドシートのデータをコピーして、下のボックスに貼り付けてください。
（データ形式：タブ区切り または カンマ区切り）
""")

# ---------------------------------------------------------
# 2. データ入力エリア（デフォルトでサンプルデータを入れておく）
# ---------------------------------------------------------
default_data = """Condition\tGroup\tValue
DMSO\tControl\t420
DMSO\tControl\t430
DMSO\tA\t180
DMSO\tA\t190
X\tControl\t500
X\tControl\t510
X\tA\t200
X\tA\t210
Y\tControl\t400
Y\tControl\t410
Y\tA\t400
Y\tA\t390"""

# テキスト入力ボックスを作成
raw_text = st.text_area("ここにデータを貼り付け (Headerを含めてください)", value=default_data, height=200)

# ---------------------------------------------------------
# 3. データの読み込みとグラフ描画
# ---------------------------------------------------------
if raw_text:
    try:
        # タブ区切りとして読み込みを試みる
        df = pd.read_csv(io.StringIO(raw_text), sep='\t')
        
        # もし1列しかなかったらカンマ区切りかもしれないので再試行
        if df.shape[1] < 2:
            df = pd.read_csv(io.StringIO(raw_text), sep=',')

        # データが正しく読み込めているか表示
        st.subheader("読み込んだデータ確認")
        st.dataframe(df.head())

        # カラム名のチェック（ユーザーが違う名前を使っている場合に備える）
        cols = df.columns
        if len(cols) < 3:
            st.error("エラー: データには少なくとも3つの列（例: Condition, Group, Value）が必要です。")
        else:
            # 自動で列を割り当て（1列目をX軸、2列目を色分け、3列目を数値と仮定）
            # 必要ならサイドバーで選べるようにするのもアリですが、まずはシンプルに
            col_x = cols[0]      # Condition
            col_hue = cols[1]    # Group
            col_y = cols[2]      # Value

            # --- グラフの設定 ---
            st.subheader("プレビュー")
            
            # 描画設定
            sns.set_style("ticks")
            fig, ax = plt.subplots(figsize=(8, 6))

            # 1. 棒グラフ
            sns.barplot(x=col_x, y=col_y, hue=col_hue, data=df,
                        palette={'Control': 'gray', 'A': '#69f0ae'} if 'Control' in df[col_hue].values else None, # 色の自動指定（Controlがあればグレーに）
                        edgecolor='black', capsize=0.1, errwidth=1.5, ci='sd', ax=ax)

            # 2. プロット（点）
            sns.stripplot(x=col_x, y=col_y, hue=col_hue, data=df,
                          palette=['white', 'white'], # 点の中は白
                          edgecolor='gray', linewidth=1, size=6, jitter=True, dodge=True, ax=ax)

            # 凡例の整理（重複を消す）
            handles, labels = ax.get_legend_handles_labels()
            # hueの数だけ凡例を残す
            n_groups = df[col_hue].nunique()
            ax.legend(handles[:n_groups], labels[:n_groups], title='', loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)

            # 見た目の調整
            sns.despine()
            ax.set_ylabel("Value", fontsize=14)
            
            # Streamlitで表示
            st.pyplot(fig)

            # --- ダウンロードボタン ---
            # 画像をバッファに保存
            fn = "plot.png"
            img = io.BytesIO()
            plt.savefig(img, format='png', bbox_inches='tight')
            
            st.download_button(
                label="画像をダウンロード (PNG)",
                data=img,
                file_name=fn,
                mime="image/png"
            )

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        st.write("データの形式を確認してください（タブ区切り、またはカンマ区切り推奨）。")
