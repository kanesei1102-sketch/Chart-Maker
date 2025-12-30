import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import numpy as np

# ---------------------------------------------------------
# 設定
# ---------------------------------------------------------
st.set_page_config(page_title="Bar Plot Maker (Sig)", layout="wide")
st.title("📊 棒グラフ作成ツール（有意差ライン対応版）")
st.markdown("""
数値データを貼り付けるだけで作成できます。
**有意差ラベル（**** や n.s.）** を入力すると、自動的にバーの上に描画されます。
""")

# セッション設定
if 'cond_count' not in st.session_state:
    st.session_state.cond_count = 3

def add_condition():
    st.session_state.cond_count += 1

def remove_condition():
    if st.session_state.cond_count > 1:
        st.session_state.cond_count -= 1

# サイドバー設定
with st.sidebar:
    st.header("設定")
    st.button("＋ 条件を増やす", on_click=add_condition)
    if st.session_state.cond_count > 1:
        st.button("－ 条件を減らす", on_click=remove_condition)
    
    st.divider()
    st.subheader("グループ設定")
    group1_name = st.text_input("グループ1 (例: Control)", value="Control")
    group2_name = st.text_input("グループ2 (例: A)", value="A")
    
    st.subheader("色の設定")
    color1 = st.color_picker("グループ1の色", "#808080")
    color2 = st.color_picker("グループ2の色", "#69f0ae")

# ---------------------------------------------------------
# データ入力処理
# ---------------------------------------------------------
cond_data_list = [] # 各条件のデータとメタデータを保存するリスト

for i in range(st.session_state.cond_count):
    with st.container():
        st.markdown("---")
        # デフォルト名
        def_name = ["DMSO", "X", "Y", "Z"][i] if i < 4 else f"Cond_{i+1}"
        
        # 3カラム構成：条件名・有意差ラベル・データ入力
        c_meta, c_g1, c_g2 = st.columns([1.5, 2, 2])
        
        with c_meta:
            st.markdown(f"#### 条件 {i+1}")
            cond_name = st.text_input("条件名", value=def_name, key=f"name_{i}")
            # ★ここで有意差ラベルを入力
            sig_label = st.text_input(
                "有意差ラベル (空欄なら表示なし)", 
                placeholder="例: ****, n.s.", 
                key=f"sig_{i}"
            )
        
        with c_g1:
            st.write(f"▼ **{group1_name}**")
            def_val1 = "420\n430\n410\n440" if i == 0 else ""
            input1 = st.text_area(f"データ1", value=def_val1, height=100, key=f"d1_{i}", label_visibility="collapsed")

        with c_g2:
            st.write(f"▼ **{group2_name}**")
            def_val2 = "180\n190\n185\n175" if i == 0 else ""
            input2 = st.text_area(f"データ2", value=def_val2, height=100, key=f"d2_{i}", label_visibility="collapsed")

        # データ処理
        current_df = pd.DataFrame()
        valid_data = False
        
        if input1 and input2:
            try:
                nums1 = [float(x.strip()) for x in input1.strip().split('\n') if x.strip()]
                nums2 = [float(x.strip()) for x in input2.strip().split('\n') if x.strip()]
                
                df1 = pd.DataFrame({'Value': nums1, 'Group': group1_name, 'Condition': cond_name})
                df2 = pd.DataFrame({'Value': nums2, 'Group': group2_name, 'Condition': cond_name})
                
                current_df = pd.concat([df1, df2])
                valid_data = True
            except:
                st.error(f"条件 {i+1}: 数値以外のデータが含まれています。")

        if valid_data:
            # 描画順序を保つためにリストに保存
            cond_data_list.append({
                'name': cond_name,
                'df': current_df,
                'sig': sig_label
            })

# ---------------------------------------------------------
# グラフ描画
# ---------------------------------------------------------
if cond_data_list:
    # 全データを結合
    final_df = pd.concat([item['df'] for item in cond_data_list], ignore_index=True)
    
    # 条件の表示順序を固定（入力順）
    order_list = [item['name'] for item in cond_data_list]

    st.subheader("プレビュー")
    
    try:
        sns.set_style("ticks")
        plt.rcParams['font.family'] = 'sans-serif'

        # catplotで描画（col_orderで順序を指定）
        g = sns.catplot(
            data=final_df, 
            kind="bar", 
            x='Group', y='Value', col='Condition', hue='Group',
            col_order=order_list,  # ★順序を固定
            palette={group1_name: color1, group2_name: color2},
            edgecolor='black', capsize=0.1, errwidth=1.5, ci='sd',
            height=5, aspect=0.6, sharey=True
        )

        g.map_dataframe(sns.stripplot, x='Group', y='Value', hue='Group',
                        palette=['white', 'white'], edgecolor='gray', 
                        linewidth=1, size=6, jitter=True, dodge=True)

        # 軸ラベルとタイトルの設定
        g.set_axis_labels("", "Number of cells")
        g.set_titles("{col_name}")

        # -------------------------------------------------------
        # ★ 有意差ラインとアスタリスクの描画処理 ★
        # -------------------------------------------------------
        for i, ax in enumerate(g.axes.flat):
            if i < len(cond_data_list):
                meta = cond_data_list[i]
                sig_text = meta['sig']
                
                # ラベルが入力されている場合のみ描画
                if sig_text:
                    # その条件におけるデータの最大値を探す
                    # (バーの高さ or ドットの高さ の高い方を取得)
                    d = meta['df']
                    max_val = d['Value'].max()
                    
                    # 線の高さを設定（最大値の10%上くらい）
                    y_line = max_val * 1.1 
                    h = max_val * 0.02 # 線の両端のヒゲの長さ

                    # 線を描く (x=0 と x=1 の間)
                    ax.plot([0, 0, 1, 1], [y_line-h, y_line, y_line, y_line-h], lw=1.5, c='k')
                    
                    # 文字を書く
                    ax.text(0.5, y_line, sig_text, ha='center', va='bottom', color='k', fontsize=14)

            # -------------------------------------------------------
            # 軸のスリム化処理（前回と同じ）
            # -------------------------------------------------------
            if i > 0: # 2つ目以降
                sns.despine(ax=ax, left=True)
                ax.yaxis.set_ticks([])
                ax.set_ylabel("")
            else: # 1つ目
                sns.despine(ax=ax, top=True, right=True)

        st.pyplot(g.figure)

        # ダウンロード
        img = io.BytesIO()
        g.figure.savefig(img, format='png', bbox_inches='tight')
        st.download_button("画像をダウンロード", data=img, file_name="sig_bar_plot.png", mime="image/png")

    except Exception as e:
        st.error(f"描画エラー: {e}")
else:
    st.info("データを入力してください")
