import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io

# ---------------------------------------------------------
# 1. ページ設定とセッション状態の初期化
# ---------------------------------------------------------
st.set_page_config(page_title="Bar Plot Maker (Dynamic)", layout="wide")

st.title("📊 科学論文風 棒グラフ作成ツール")
st.markdown("""
**条件（Condition）ごとにデータを入力してください。**
* データ入力欄には **「Group」と「Value」** の2列を入力してください（タブ区切り推奨）。
* 「条件を追加」ボタンで入力枠を増やせます。
""")

# セッション状態（条件の数）を管理
if 'cond_count' not in st.session_state:
    st.session_state.cond_count = 1  # 最初は1つ

def add_condition():
    st.session_state.cond_count += 1

def remove_condition():
    if st.session_state.cond_count > 1:
        st.session_state.cond_count -= 1

# ---------------------------------------------------------
# 2. サイドバー：グラフ全体の操作
# ---------------------------------------------------------
with st.sidebar:
    st.header("操作パネル")
    st.button("＋ 条件を追加する", on_click=add_condition, type="primary")
    if st.session_state.cond_count > 1:
        st.button("－ 最後の条件を削除", on_click=remove_condition)
    
    st.divider()
    st.write(f"現在の条件数: {st.session_state.cond_count}")
    st.info("データ数の上限: 各条件につき100個程度まで推奨")

# ---------------------------------------------------------
# 3. データ入力エリア（動的に生成）
# ---------------------------------------------------------
all_dfs = [] # ここに各条件のデータフレームを貯める

# デフォルトデータのサンプル（2列だけ）
sample_text_1 = """Group\tValue
Control\t420
Control\t430
A\t180
A\t190"""

sample_text_2 = """Group\tValue
Control\t500
Control\t510
A\t200
A\t210"""

# 条件の数だけループして入力フォームを作る
cols = st.columns(min(st.session_state.cond_count, 3)) # 横並び（最大3列まで）にするか、縦に積むか

for i in range(st.session_state.cond_count):
    # レイアウト: たくさんある場合は縦に並べる
    with st.container():
        st.markdown(f"### 条件 {i+1}")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # 条件名の入力（デフォルト値を設定）
            default_name = ["DMSO", "X", "Y", "Z"][i] if i < 4 else f"Cond_{i+1}"
            cond_name = st.text_input(f"条件名 ({i+1})", value=default_name, key=f"name_{i}")
        
        with col2:
            # データの入力
            default_val = sample_text_1 if i == 0 else (sample_text_2 if i == 1 else "")
            data_text = st.text_area(
                f"データ ({cond_name}) - Headerあり: Group, Value",
                value=default_val,
                height=150,
                key=f"data_{i}",
                placeholder="Group\tValue\nControl\t100\n..."
            )

        # データがあれば処理してリストに追加
        if data_text:
            try:
                # 読み込み
                temp_df = pd.read_csv(io.StringIO(data_text), sep='\t')
                if temp_df.shape[1] < 2:
                    temp_df = pd.read_csv(io.StringIO(data_text), sep=',')
                
                # カラム名が足りない場合のチェック
                if temp_df.shape[1] >= 2:
                    # 強制的にカラム名を統一（結合時のエラー防止）
                    # 1列目=Group, 2列目=Value とみなす
                    temp_df = temp_df.iloc[:, :2]
                    temp_df.columns = ['Group', 'Value']
                    
                    # 条件名カラムを追加
                    temp_df['Condition'] = cond_name
                    
                    # 100個制限のチェック（警告のみ）
                    if len(temp_df) > 100:
                        st.warning(f"⚠️ {cond_name}のデータ数が100を超えています（{len(temp_df)}個）。描画が重くなる可能性があります。")
                    
                    all_dfs.append(temp_df)
                else:
                    st.error(f"条件 {i+1}: 列が足りません。「Group」と「Value」の2列が必要です。")
            
            except Exception as e:
                st.error(f"条件 {i+1} の読み込みエラー: {e}")
        
        st.divider()

# ---------------------------------------------------------
# 4. 結合とグラフ描画
# ---------------------------------------------------------
if all_dfs:
    # 全データを縦に結合
    final_df = pd.concat(all_dfs, ignore_index=True)
    
    st.subheader(f"グラフプレビュー (総データ数: {len(final_df)})")
    
    # 描画処理
    try:
        sns.set_style("ticks")
        
        # 条件ごとにグラフを分ける (catplot)
        g = sns.catplot(
            data=final_df, 
            kind="bar", 
            x='Group',      
            y='Value',        
            col='Condition',     # 条件ごとに枠を分ける
            hue='Group',
            palette={'Control': 'gray', 'A': '#69f0ae'} if 'Control' in final_df['Group'].values else None,
            edgecolor='black', capsize=0.1, errwidth=1.5, ci='sd',
            height=5, aspect=0.7,
            sharey=True
        )

        # 個別プロット
        g.map_dataframe(sns.stripplot, x='Group', y='Value', hue='Group',
                        palette=['white', 'white'], edgecolor='gray', 
                        linewidth=1, size=6, jitter=True, dodge=True)

        g.set_axis_labels("", "Value")
        g.set_titles("{col_name}")
        
        st.pyplot(g.figure)

        # ダウンロード
        img = io.BytesIO()
        g.figure.savefig(img, format='png', bbox_inches='tight')
        st.download_button("画像をダウンロード", data=img, file_name="multi_cond_plot.png", mime="image/png")

    except Exception as e:
        st.error(f"描画エラー: {e}")
else:
    st.info("データを入力するとここにグラフが表示されます。")
