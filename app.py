import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import numpy as np

# ---------------------------------------------------------
# 設定
# ---------------------------------------------------------
st.set_page_config(page_title="Bar Plot Maker (Width)", layout="wide")
st.title("📊 棒グラフ作成ツール（太さ調整版）")
st.markdown("""
**新機能:** サイドバーで「棒グラフの幅」を変更できるようになりました。
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
    st.header("データ設定")
    st.button("＋ 条件を増やす", on_click=add_condition)
    if st.session_state.cond_count > 1:
        st.button("－ 条件を減らす", on_click=remove_condition)
    
    st.divider()
    st.subheader("グループ設定")
    group1_name = st.text_input("グループ1 (例: Control)", value="Control")
    group2_name = st.text_input("グループ2 (例: A)", value="A")
    
    st.divider()
    st.header("デザイン設定")
    st.subheader("色の設定")
    color1 = st.color_picker("グループ1の色", "#808080")
    color2 = st.color_picker("グループ2の色", "#69f0ae")
    
    st.subheader("グラフの形状")
    # ★追加: 棒の太さを調整するスライダー (0.1〜1.0)
    bar_width = st.slider("棒グラフの幅", min_value=0.1, max_value=1.0, value=0.6, step=0.1)
    
    # ついでにエラーバーのキャップ（横線）の長さも調整できるようにしておくと便利です
    cap_size = st.slider("エラーバーの横線 (Capsize)", min_value=0.0, max_value=0.5, value=0.1, step=0.05)

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
                pass

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

    global_max_val = final_df['Value'].max()
    y_limit = global_max_val * 1.3

    st.subheader("プレビュー")
    
    try:
        # フォント設定
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['xtick.direction'] = 'out'
        plt.rcParams['ytick.direction'] = 'out'
        
        # 描画
        # ★ width=bar_width を追加しました
        g = sns.catplot(
            data=final_df, 
            kind="bar", 
            x='Group', y='Value', col='Condition', hue='Group',
            col_order=order_list,
            palette={group1_name: color1, group2_name: color2},
            edgecolor='black', 
            capsize=cap_size, # ★ここも変数化
            errwidth=1.5, ci='sd',
            width=bar_width,  # ★ここが太さ調整のキモです
            height=5, aspect=0.6, 
            sharey=False,
            legend=False # 凡例はcatplot側では消して、必要なら別途描画するが、今回はX軸ラベルでわかるのでOK
        )

        g.map_dataframe(sns.stripplot, x='Group', y='Value', hue='Group',
                        palette=['white', 'white'], edgecolor='gray', 
                        linewidth=1, size=6, jitter=True, dodge=True)

        g.set_axis_labels("", "Number of cells")
        g.set_titles("{col_name}")

        # 軸の手動調整
        for i, ax in enumerate(g.axes.flat):
            ax.set_ylim(0, y_limit)

            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            ax.spines['bottom'].set_visible(True)
            ax.spines['bottom'].set_color('black')
            ax.spines['bottom'].set_linewidth(1.2)
            
            if i == 0:
                ax.spines['left'].set_visible(True)
                ax.spines['left'].set_color('black')
                ax.spines['left'].set_linewidth(1.2)
                
                ax.yaxis.set_visible(True)
                ax.tick_params(axis='y', which='major', length=6, width=1.2, labelsize=12, labelleft=True)
                ax.set_ylabel("Number of cells", fontsize=14)
            else:
                ax.spines['left'].set_visible(False)
                ax.yaxis.set_visible(False)
                ax.set_ylabel("")
            
            # 有意差ライン
            if i < len(cond_data_list):
                meta = cond_data_list[i]
                sig_text = meta['sig']
                if sig_text:
                    d = meta['df']
                    this_max = d['Value'].max()
                    
                    y_line = this_max * 1.1 
                    h = this_max * 0.02
                    
                    groups_in_this_cond = d['Group'].unique()
                    
                    # 棒が細くなったときに有意差ラインの幅も調整したい場合はここを触りますが
                    # 基本的には 0〜1 の間の線でOKです
                    line_start = 0
                    line_end = 1
                    
                    # バーが細すぎる場合、線の端を少し内側に寄せると綺麗に見えます（簡易的な調整）
                    # 今回は標準的な描画方法のままにします
                    
                    if len(groups_in_this_cond) >= 2:
                        ax.plot([line_start, line_start, line_end, line_end], [y_line-h, y_line, y_line, y_line-h], lw=1.5, c='k')
                        ax.text(0.5, y_line, sig_text, ha='center', va='bottom', color='k', fontsize=14)
                    else:
                        ax.text(0, y_line, sig_text, ha='center', va='bottom', color='k', fontsize=14)

        plt.subplots_adjust(wspace=0)

        st.pyplot(g.figure)

        img = io.BytesIO()
        g.figure.savefig(img, format='png', bbox_inches='tight')
        st.download_button("画像をダウンロード", data=img, file_name="width_adjusted_plot.png", mime="image/png")

    except Exception as e:
        st.error(f"描画エラー: {e}")
else:
    st.info("データを入力してください")
