import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import numpy as np

# ---------------------------------------------------------
# 設定
# ---------------------------------------------------------
st.set_page_config(page_title="Bar Plot Maker (Final)", layout="wide")
st.title("📊 棒グラフ作成ツール（軸・数値 修正版）")
st.markdown("""
**軸の表示を修正しました。**
縦軸と横軸がしっかり繋がり、数値も必ず表示されます。
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
                pass # エラー時は無視

        if input2:
            try:
                nums2 = [float(x.strip()) for x in input2.strip().split('\n') if x.strip()]
                if nums2:
                    dfs_temp.append(pd.DataFrame({'Value': nums2, 'Group': group2_name, 'Condition': cond_name}))
            except:
                pass
        
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
        # フォント設定
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['xtick.direction'] = 'out' # 目盛りを外向きに
        plt.rcParams['ytick.direction'] = 'out'
        
        # 描画
        # sharey=False にすることで、各グラフが独立して軸を持つようにします（後で手動で消すため）
        g = sns.catplot(
            data=final_df, 
            kind="bar", 
            x='Group', y='Value', col='Condition', hue='Group',
            col_order=order_list,
            palette={group1_name: color1, group2_name: color2},
            edgecolor='black', capsize=0.1, errwidth=1.5, ci='sd',
            height=5, aspect=0.6, 
            sharey=True # 軸の範囲（スケール）は統一する
        )

        g.map_dataframe(sns.stripplot, x='Group', y='Value', hue='Group',
                        palette=['white', 'white'], edgecolor='gray', 
                        linewidth=1, size=6, jitter=True, dodge=True)

        g.set_axis_labels("", "Number of cells")
        g.set_titles("{col_name}")

        # ★ 軸の強制修正処理 ★
        for i, ax in enumerate(g.axes.flat):
            # まず、すべての枠線（スパイン）の設定をリセット
            ax.spines['top'].set_visible(False)   # 上は消す
            ax.spines['right'].set_visible(False) # 右は消す
            
            # 下（X軸）は全員表示、かつ黒色ではっきりさせる
            ax.spines['bottom'].set_visible(True)
            ax.spines['bottom'].set_color('black')
            ax.spines['bottom'].set_linewidth(1.2)
            
            # 左（Y軸）の設定
            if i == 0:
                # 1番目のグラフ: Y軸を表示
                ax.spines['left'].set_visible(True)
                ax.spines['left'].set_color('black')
                ax.spines['left'].set_linewidth(1.2)
                
                # 目盛りと数値を強制表示
                ax.yaxis.set_ticks_position('left')
                ax.tick_params(axis='y', which='major', length=6, width=1.2, labelsize=12, labelleft=True)
                ax.set_ylabel("Number of cells", fontsize=14)
            else:
                # 2番目以降: Y軸の線を消す
                ax.spines['left'].set_visible(False)
                ax.yaxis.set_ticks([]) # 目盛りを消す
                ax.set_ylabel("")      # ラベルを消す
            
            # 有意差ラインの描画
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

        # グラフ間の調整
        plt.subplots_adjust(wspace=0.1)

        st.pyplot(g.figure)

        img = io.BytesIO()
        g.figure.savefig(img, format='png', bbox_inches='tight')
        st.download_button("画像をダウンロード", data=img, file_name="final_plot.png", mime="image/png")

    except Exception as e:
        st.error(f"描画エラー: {e}")
else:
    st.info("データを入力してください")
