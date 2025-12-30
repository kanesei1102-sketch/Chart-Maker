import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io

# ---------------------------------------------------------
# 設定
# ---------------------------------------------------------
st.set_page_config(page_title="Bar Plot Maker (Simple)", layout="wide")
st.title("📊 棒グラフ作成ツール（数値コピペ版）")
st.markdown("Excelの数値列をそのまま貼り付けてください。ヘッダー（Group, Valueなどの文字）は不要です。")

# セッション状態で条件数を管理
if 'cond_count' not in st.session_state:
    st.session_state.cond_count = 3  # デフォルトで3条件（DMSO, X, Y）用意

def add_condition():
    st.session_state.cond_count += 1

def remove_condition():
    if st.session_state.cond_count > 1:
        st.session_state.cond_count -= 1

# サイドバー
with st.sidebar:
    st.header("設定")
    st.button("＋ 条件を増やす", on_click=add_condition)
    if st.session_state.cond_count > 1:
        st.button("－ 条件を減らす", on_click=remove_condition)
    
    st.divider()
    # グループ名の設定（全体共通）
    st.subheader("グループ名")
    group1_name = st.text_input("グループ1の名前", value="Control")
    group2_name = st.text_input("グループ2の名前", value="A")
    
    # 色の設定
    st.subheader("色の設定")
    color1 = st.color_picker("グループ1の色", "#808080") # グレー
    color2 = st.color_picker("グループ2の色", "#69f0ae") # 緑

# ---------------------------------------------------------
# データ入力と処理
# ---------------------------------------------------------
all_dfs = [] 

# 条件の数だけループ
for i in range(st.session_state.cond_count):
    with st.container():
        st.markdown(f"---")
        # デフォルトの条件名
        def_name = ["DMSO", "X", "Y", "Z"][i] if i < 4 else f"Cond_{i+1}"
        
        # レイアウト：左に条件名、右に2つのデータ入力欄
        c_title, c_g1, c_g2 = st.columns([1, 2, 2])
        
        with c_title:
            st.markdown(f"#### 条件 {i+1}")
            cond_name = st.text_input("条件名", value=def_name, key=f"name_{i}")
        
        with c_g1:
            st.write(f"▼ **{group1_name}** の数値")
            # サンプルデータ(最初の1つだけ入れておく)
            def_val1 = "420\n430\n410\n440" if i == 0 else ""
            input1 = st.text_area(f"{group1_name}のデータ", value=def_val1, height=100, key=f"d1_{i}", placeholder="数値を改行で入力")

        with c_g2:
            st.write(f"▼ **{group2_name}** の数値")
            def_val2 = "180\n190\n185\n175" if i == 0 else ""
            input2 = st.text_area(f"{group2_name}のデータ", value=def_val2, height=100, key=f"d2_{i}", placeholder="数値を改行で入力")

        # データ処理
        # 入力1 (Group 1)
        if input1:
            try:
                # 数値だけを取り出す（改行区切り）
                nums1 = [float(x.strip()) for x in input1.strip().split('\n') if x.strip()]
                df1 = pd.DataFrame({'Value': nums1})
                df1['Group'] = group1_name
                df1['Condition'] = cond_name
                all_dfs.append(df1)
            except:
                st.error(f"条件{i+1} ({group1_name}): 数値以外が含まれています")

        # 入力2 (Group 2)
        if input2:
            try:
                nums2 = [float(x.strip()) for x in input2.strip().split('\n') if x.strip()]
                df2 = pd.DataFrame({'Value': nums2})
                df2['Group'] = group2_name
                df2['Condition'] = cond_name
                all_dfs.append(df2)
            except:
                st.error(f"条件{i+1} ({group2_name}): 数値以外が含まれています")

# ---------------------------------------------------------
# グラフ描画
# ---------------------------------------------------------
if all_dfs:
    final_df = pd.concat(all_dfs, ignore_index=True)
    
    st.subheader("プレビュー")
    try:
        sns.set_style("ticks")
        
        # catplotで条件ごとに枠を分ける
        g = sns.catplot(
            data=final_df, 
            kind="bar", 
            x='Group', y='Value', col='Condition', hue='Group',
            palette={group1_name: color1, group2_name: color2}, # サイドバーで設定した色
            edgecolor='black', capsize=0.1, errwidth=1.5, ci='sd',
            height=5, aspect=0.7, sharey=True
        )

        # 個別データプロット
        g.map_dataframe(sns.stripplot, x='Group', y='Value', hue='Group',
                        palette=['white', 'white'], edgecolor='gray', 
                        linewidth=1, size=6, jitter=True, dodge=True)

        g.set_axis_labels("", "Number of cells") # Y軸ラベル
        g.set_titles("{col_name}")
        
        st.pyplot(g.figure)

        # ダウンロード
        img = io.BytesIO()
        g.figure.savefig(img, format='png', bbox_inches='tight')
        st.download_button("画像をダウンロード", data=img, file_name="bar_plot.png", mime="image/png")

    except Exception as e:
        st.error(f"エラー: {e}")
else:
    st.info("データを入力してください")
