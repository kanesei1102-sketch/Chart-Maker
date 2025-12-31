import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches # 凡例用
import io
import numpy as np
import datetime

# ---------------------------------------------------------
# 設定
# ---------------------------------------------------------
st.set_page_config(page_title="Bar Plot Maker (With Legend)", layout="wide")
st.title("📊 棒グラフ作成ツール（凡例付き）")
st.markdown("""
**修正:** グラフの右側に、グループの凡例（Legend）を表示するようにしました。
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
    st.header("軸の設定")
    y_axis_label = st.text_input("Y軸のタイトル", value="Number of cells")
    
    st.divider()
    st.header("デザイン設定")
    st.subheader("色の設定")
    color1 = st.color_picker("グループ1の色", "#999999") # 論文っぽいグレー
    color2 = st.color_picker("グループ2の色", "#66c2a5") # エメラルドグリーン
    
    st.subheader("形状と配置")
    bar_width = st.slider("棒グラフの幅 (Width)", min_value=0.2, max_value=1.0, value=0.6, step=0.1)
    bar_gap = st.slider("棒の間の隙間 (Gap)", min_value=0.0, max_value=0.5, value=0.05, step=0.01)
    cap_size = st.slider("エラーバーの横線 (Capsize)", min_value=0.0, max_value=10.0, value=5.0, step=1.0)
    dot_size = st.slider("プロットのサイズ", 10, 100, 40)
    
    # ★追加: 凡例の表示切り替え
    show_legend = st.checkbox("凡例を表示する", value=True)

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
            sig_label = st.text_input("有意差ラベル", placeholder="例: ****", key=f"sig_{i}")
        
        with c_g1:
            st.write(f"▼ **{group1_name}**")
            def_val1 = "420\n430\n410\n440" if i == 0 else ""
            input1 = st.text_area(f"データ1", value=def_val1, height=100, key=f"d1_{i}", label_visibility="collapsed")

        with c_g2:
            st.write(f"▼ **{group2_name}**")
            def_val2 = "180\n190\n185\n175" if i == 0 else ""
            input2 = st.text_area(f"データ2", value=def_val2, height=100, key=f"d2_{i}", label_visibility="collapsed")

        vals1 = []
        vals2 = []
        if input1:
            try:
                vals1 = [float(x.strip()) for x in input1.strip().split('\n') if x.strip()]
            except: pass
        if input2:
            try:
                vals2 = [float(x.strip()) for x in input2.strip().split('\n') if x.strip()]
            except: pass
        
        if vals1 or vals2:
            cond_data_list.append({
                'name': cond_name,
                'g1': vals1,
                'g2': vals2,
                'sig': sig_label
            })

# ---------------------------------------------------------
# グラフ描画
# ---------------------------------------------------------
if cond_data_list:
    st.subheader("プレビュー")
    
    try:
        all_vals = []
        has_any_g1 = False
        has_any_g2 = False
        
        for item in cond_data_list:
            if item['g1']: has_any_g1 = True
            if item['g2']: has_any_g2 = True
            all_vals.extend(item['g1'])
            all_vals.extend(item['g2'])
        
        if not all_vals:
            st.warning("有効な数値データがありません")
            st.stop()
            
        global_max = max(all_vals)
        y_limit = global_max * 1.35
        
        n_plots = len(cond_data_list)
        # 凡例用のスペース確保のため、figsizeを少し調整してもいいですが、
        # bbox_inches='tight'で保存時に自動調整されるのでこのままでOK
        fig, axes = plt.subplots(1, n_plots, figsize=(n_plots * 3, 5), sharey=True)
        
        if n_plots == 1:
            axes = [axes]
            
        plt.subplots_adjust(wspace=0)
        plt.rcParams['font.family'] = 'sans-serif'

        # --- 各条件ごとの描画 ---
        for i, ax in enumerate(axes):
            data = cond_data_list[i]
            g1 = np.array(data['g1'])
            g2 = np.array(data['g2'])
            
            has_g1 = len(g1) > 0
            has_g2 = len(g2) > 0
            
            # 位置決定
            if has_g1 and has_g2:
                pos1 = -(bar_width/2 + bar_gap/2)
                pos2 = +(bar_width/2 + bar_gap/2)
            else:
                pos1 = 0
                pos2 = 0

            # Group 1
            if has_g1:
                mean1 = np.mean(g1)
                std1 = np.std(g1, ddof=1) if len(g1) > 1 else 0
                ax.bar(pos1, mean1, width=bar_width, color=color1, edgecolor='black', zorder=1)
                ax.errorbar(pos1, mean1, yerr=std1, fmt='none', color='black', capsize=cap_size, elinewidth=1.5, zorder=2)
                noise = np.random.normal(0, 0.04 * bar_width, len(g1))
                ax.scatter(pos1 + noise, g1, color='white', edgecolor='gray', s=dot_size, zorder=3)
            
            # Group 2
            if has_g2:
                mean2 = np.mean(g2)
                std2 = np.std(g2, ddof=1) if len(g2) > 1 else 0
                ax.bar(pos2, mean2, width=bar_width, color=color2, edgecolor='black', zorder=1)
                ax.errorbar(pos2, mean2, yerr=std2, fmt='none', color='black', capsize=cap_size, elinewidth=1.5, zorder=2)
                noise = np.random.normal(0, 0.04 * bar_width, len(g2))
                ax.scatter(pos2 + noise, g2, color='white', edgecolor='gray', s=dot_size, zorder=3)

            # X軸ラベル
            ticks = []
            labels = []
            if has_g1:
                ticks.append(pos1)
                labels.append(group1_name)
            if has_g2:
                ticks.append(pos2)
                labels.append(group2_name)
            
            ax.set_xticks(ticks)
            ax.set_xticklabels(labels, fontsize=11)
            ax.set_title(data['name'], fontsize=12, pad=10)
            
            # 有意差ライン
            sig_text = data['sig']
            if sig_text:
                current_max = 0
                if has_g1: current_max = max(current_max, np.max(g1))
                if has_g2: current_max = max(current_max, np.max(g2))
                
                y_line = current_max * 1.15
                h = current_max * 0.03
                
                if has_g1 and has_g2:
                    lx_start, lx_end = pos1, pos2
                elif has_g1:
                    lx_start, lx_end = pos1 - bar_width/3, pos1 + bar_width/3
                else: 
                    lx_start, lx_end = pos2 - bar_width/3, pos2 + bar_width/3
                
                ax.plot([lx_start, lx_start, lx_end, lx_end], [y_line-h, y_line, y_line, y_line-h], lw=1.5, c='k')
                ax.text((lx_start+lx_end)/2, y_line + current_max*0.02, sig_text, ha='center', va='bottom', fontsize=14, color='k')

            # 軸設定
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
                ax.set_ylabel(y_axis_label, fontsize=14) 
                ax.tick_params(axis='y', left=True, labelleft=True, width=1.2)
            else:
                ax.spines['left'].set_visible(False)
                ax.tick_params(axis='y', left=False, labelleft=False)

            margin = 0.5
            max_pos = (bar_width/2 + bar_gap/2) + bar_width/2
            ax.set_xlim(-(max_pos + margin), (max_pos + margin))

        # --- ★ここが追加ポイント: 凡例 (Legend) の作成 ---
        if show_legend:
            legend_handles = []
            # グループ1が存在するなら凡例に追加
            if has_any_g1:
                patch1 = mpatches.Patch(facecolor=color1, edgecolor='black', label=group1_name)
                legend_handles.append(patch1)
            # グループ2が存在するなら凡例に追加
            if has_any_g2:
                patch2 = mpatches.Patch(facecolor=color2, edgecolor='black', label=group2_name)
                legend_handles.append(patch2)
            
            # 図全体に対して凡例を追加（グラフの外側右に配置）
            # bbox_to_anchor=(1.05, 0.5) で「枠外の右側中央」を指定しています
            if legend_handles:
                fig.legend(handles=legend_handles, loc='center left', bbox_to_anchor=(0.92, 0.5), 
                          frameon=False, fontsize=12)

        st.pyplot(fig)

        img = io.BytesIO()
        # bbox_inches='tight' が重要で、これがあるとはみ出した凡例も含めて画像保存されます
        fig.savefig(img, format='png', bbox_inches='tight', dpi=300) 
        
        # --- ここが修正点：日本時間(JST)のファイル名を生成 ---
        now = datetime.datetime.now() + datetime.timedelta(hours=9)
        file_name = f"graph_{now.strftime('%Y%m%d_%H%M%S')}.png"
        
        st.download_button("画像をダウンロード", data=img, file_name=file_name, mime="image/png")

    except Exception as e:
        st.error(f"描画エラー: {e}")
else:
    st.info("データを入力してください")
