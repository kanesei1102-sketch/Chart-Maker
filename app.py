import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import numpy as np

# ---------------------------------------------------------
# 設定
# ---------------------------------------------------------
st.set_page_config(page_title="Bar Plot Maker (Fixed)", layout="wide")
st.title("📊 棒グラフ作成ツール（軸・数値修正版）")
st.markdown("""
数値データを貼り付けるだけで作成できます。
**有意差ラベル（**** や n.s.）** も対応しています。
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
cond_data_list = [] 

for i in range(st.session_state.cond_count):
    with st.container():
        st.markdown("---")
        def_name = ["DMSO", "X", "Y", "Z"][i] if i < 4 else f"Cond_{i+1}"
        
        c_meta, c_g1, c_g2 = st.columns([1.5, 2, 2])
        
        with c_meta:
            st.markdown(f"#### 条件 {i+1}")
            cond_name = st.text_input("条件名", value=def_name, key=f"name_{i}")
            sig_label = st.text_input(
                "有意差ラベル", 
                placeholder="例: ****", 
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

        dfs_temp = []
        if input1:
            try:
                nums1 = [float(x.strip()) for x in input1.strip().split('\n') if x.strip()]
                if nums1:
                    dfs_temp.append(pd.DataFrame({'Value': nums1, 'Group': group1_name, 'Condition': cond_name}))
            except:
                st.error(f"条件 {i+1}: 数値エラー")

        if input2:
            try:
                nums2 = [float(x.strip()) for x in input2.strip().split('\n') if x.strip()]
                if nums2:
                    dfs_temp.append(pd.DataFrame({'Value': nums2, 'Group': group2_name, 'Condition': cond_name}))
            except:
                st.error(f"条件 {i+1}: 数値エラー")
        
        if dfs_temp:
            current_df = pd.concat(dfs_temp)
            cond_data_list.append({
                'name': cond_name,
                'df': current_df,
                'sig': sig_label
            })

# ---------------------------------------------------------
# グラフ描画
# ---------------------------------------------------------
if cond_data_list:
    final_df = pd.concat([item['df'] for item in cond_data_list], ignore_index=True)
    order_list = [item['name'] for item in cond_data_list]

    st.subheader("プレビュー")
    
    try:
        # スタイル設定
        sns.set_style("ticks") # 軸の目盛りを表示するスタイル
        plt.rcParams['font.family'] = 'sans-serif'
        
        # 描画
        g = sns.catplot(
            data=final_df, 
            kind="bar", 
            x='Group', y='Value', col='Condition', hue='Group',
            col_order=order_list,
            palette={group1_name: color1, group2_name: color2},
            edgecolor='black', capsize=0.1, errwidth=1.5, ci='sd',
            height=5, aspect=0.6, sharey=True
        )

        g.map_dataframe(sns.stripplot, x='Group', y='Value', hue='Group',
                        palette=['white', 'white'], edgecolor='gray', 
                        linewidth=1, size=6, jitter=True, dodge=True)

        g.set_axis_labels("", "Number of cells")
        g.set_titles("{col_name}")

        # ★ 軸の修正ポイント ★
        for i, ax in enumerate(g.axes.flat):
            # 1. まず全ての軸で、上と右の枠線を消す (trim=Falseで軸を離さない！)
            sns.despine(ax=ax, top=True, right=True, trim=False)
            
            # 2. 2つ目以降のグラフだけ、左の軸（Y軸）を消す
            if i > 0:
                sns.despine(ax=ax, left=True, top=True, right=True, trim=False)
                ax.yaxis.set_ticks([]) # 目盛りを消す
                ax.set_ylabel("")      # ラベルを消す
            else:
                # 3. 1つ目のグラフは、Y軸の数値を強制的に表示する
                ax.tick_params(axis='y', which='major', left=True, labelleft=True)
            
            # 4. 有意差ラインの描画
            if i < len(cond_data_list):
                meta = cond_data_list[i]
                sig_text = meta['sig']
                if sig_text:
                    d = meta['df']
                    max_val = d['Value'].max()
                    y_line = max_val * 1.1 
                    h = max_val * 0.02
                    
                    groups_in_this_cond = d['Group'].unique()
                    if len(groups_in_this_cond) >= 2:
                        ax.plot([0, 0, 1, 1], [y_line-h, y_line, y_line, y_line-h], lw=1.5, c='k')
                        ax.text(0.5, y_line, sig_text, ha='center', va='bottom', color='k', fontsize=14)
                    else:
                        ax.text(0, y_line, sig_text, ha='center', va='bottom', color='k', fontsize=14)

        # グラフ同士の間隔を少し詰める（見栄え調整）
        plt.subplots_adjust(wspace=0.1)

        st.pyplot(g.figure)

        img = io.BytesIO()
        g.figure.savefig(img, format='png', bbox_inches='tight')
        st.download_button("画像をダウンロード", data=img, file_name="fixed_plot.png", mime="image/png")

    except Exception as e:
        st.error(f"描画エラー: {e}")
else:
    st.info("データを入力してください")
