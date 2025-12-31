import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import numpy as np
import datetime

# ---------------------------------------------------------
# 基本設定
# ---------------------------------------------------------
st.set_page_config(page_title="Sci-Graph Maker Pro", layout="wide")
st.title("📊 Sci-Graph Maker Pro (多機能版)")
st.markdown("""
**概要:** 論文投稿クオリティのグラフを作成します。  
**対応:** 棒グラフ(平均値)、箱ひげ図(中央値)、バイオリン図(分布密度)の切り替えが可能です。
""")

# セッション状態の管理
if 'cond_count' not in st.session_state:
    st.session_state.cond_count = 3

def add_condition():
    st.session_state.cond_count += 1

def remove_condition():
    if st.session_state.cond_count > 1:
        st.session_state.cond_count -= 1

# ---------------------------------------------------------
# サイドバー設定
# ---------------------------------------------------------
with st.sidebar:
    st.header("データ設定")
    st.button("＋ 条件（列）を増やす", on_click=add_condition)
    if st.session_state.cond_count > 1:
        st.button("－ 条件（列）を減らす", on_click=remove_condition)
    
    st.divider()
    st.subheader("グループ設定")
    group1_name = st.text_input("グループ1の名称", value="Control")
    group2_name = st.text_input("グループ2の名称", value="Target")
    
    st.divider()
    st.header("グラフ表示設定")
    
    # ★グラフ種類の選択（デフォルトは棒グラフ）
    graph_type = st.selectbox("グラフの種類を選択", 
                              ["棒グラフ (平均値 ± 標準偏差)", 
                               "箱ひげ図 (中央値 + 四分位範囲)", 
                               "バイオリン図 (データ分布密度)"])
    
    y_axis_label = st.text_input("Y軸のタイトル", value="Relative Intensity (%)")
    
    st.divider()
    st.header("デザインとスタイル")
    
    with st.expander("🎨 色と凡例", expanded=True):
        color1 = st.color_picker("グループ1の色", "#999999") 
        color2 = st.color_picker("グループ2の色", "#66c2a5") 
        show_legend = st.checkbox("凡例を表示する", value=True)

    with st.expander("📏 レイアウト調整", expanded=True):
        width = st.slider("要素（棒/箱）の幅", 0.2, 1.0, 0.6, 0.1)
        gap = st.slider("グループ間の隙間", 0.0, 0.5, 0.05, 0.01)
        if "棒グラフ" in graph_type:
            cap_size = st.slider("エラーバーの横線幅", 0.0, 10.0, 5.0, 0.5)

    with st.expander("✨ プロット(点)の微調整", expanded=True):
        show_points = st.checkbox("個別データ点を表示する", value=True)
        st.caption("データ数が多い(N>1000)場合は、サイズを小さく、透明度を上げてください。")
        dot_size = st.slider("点のサイズ", 1, 100, 20) 
        dot_alpha = st.slider("点の透明度 (Alpha)", 0.1, 1.0, 0.6, 0.1)
        jitter_strength = st.slider("散らばり具合 (Jitter)", 0.0, 0.3, 0.04, 0.01)

# ---------------------------------------------------------
# データ入力セクション
# ---------------------------------------------------------
cond_data_list = [] 

for i in range(st.session_state.cond_count):
    with st.container():
        st.markdown("---")
        def_name = ["Day 0", "Day 3", "Day 7", "Day 14"][i] if i < 4 else f"条件_{i+1}"
        
        c_meta, c_g1, c_g2 = st.columns([1.5, 2, 2])
        
        with c_meta:
            st.markdown(f"#### 条件 {i+1}")
            cond_name = st.text_input("条件名を入力", value=def_name, key=f"name_{i}")
            sig_label = st.text_input("有意差ラベル", placeholder="例: **", key=f"sig_{i}")
        
        with c_g1:
            st.write(f"▼ **{group1_name}**")
            # デモ用データ
            def_val1 = "100\n105\n98\n102" if i == 0 else ""
            input1 = st.text_area(f"データ1", value=def_val1, height=100, key=f"d1_{i}", label_visibility="collapsed")

        with c_g2:
            st.write(f"▼ **{group2_name}**")
            def_val2 = "140\n135\n150\n145" if i == 0 else ""
            input2 = st.text_area(f"データ2", value=def_val2, height=100, key=f"d2_{i}", label_visibility="collapsed")

        vals1, vals2 = [], []
        if input1:
            try: vals1 = [float(x.strip()) for x in input1.strip().split('\n') if x.strip()]
            except: pass
        if input2:
            try: vals2 = [float(x.strip()) for x in input2.strip().split('\n') if x.strip()]
            except: pass
        
        if vals1 or vals2:
            cond_data_list.append({'name': cond_name, 'g1': vals1, 'g2': vals2, 'sig': sig_label})

# ---------------------------------------------------------
# グラフ描画ロジック
# ---------------------------------------------------------
if cond_data_list:
    st.subheader("プレビュー")
    
    try:
        all_vals = []
        for item in cond_data_list:
            all_vals.extend(item['g1'])
            all_vals.extend(item['g2'])
        
        if not all_vals:
            st.warning("有効な数値データが入力されていません。")
            st.stop()
            
        global_max = max(all_vals)
        y_limit = global_max * 1.35
        
        n_plots = len(cond_data_list)
        fig, axes = plt.subplots(1, n_plots, figsize=(n_plots * 3, 5), sharey=True)
        if n_plots == 1: axes = [axes]
            
        plt.subplots_adjust(wspace=0)
        plt.rcParams['font.family'] = 'sans-serif'

        for i, ax in enumerate(axes):
            data = cond_data_list[i]
            g1, g2 = np.array(data['g1']), np.array(data['g2'])
            has_g1, has_g2 = len(g1) > 0, len(g2) > 0
            
            if has_g1 and has_g2:
                pos1, pos2 = -(width/2 + gap/2), +(width/2 + gap/2)
            else:
                pos1, pos2 = 0, 0

            # 描画用サブ関数
            def plot_group(ax, pos, vals, color):
                if len(vals) == 0: return
                
                # A. 棒グラフ (元の完璧なロジック)
                if "棒グラフ" in graph_type:
                    mean = np.mean(vals)
                    std = np.std(vals, ddof=1) if len(vals) > 1 else 0
                    ax.bar(pos, mean, width=width, color=color, edgecolor='black', zorder=1, alpha=0.9)
                    ax.errorbar(pos, mean, yerr=std, fmt='none', color='black', capsize=cap_size, elinewidth=1.5, zorder=2)
                
                # B. 箱ひげ図
                elif "箱ひげ図" in graph_type:
                    ax.boxplot(vals, positions=[pos], widths=width, patch_artist=True, 
                               showfliers=False,
                               medianprops=dict(color="black", linewidth=1.5),
                               boxprops=dict(facecolor=color, color="black"),
                               whiskerprops=dict(color="black"),
                               capprops=dict(color="black"), zorder=1)
                
                # C. バイオリン図
                elif "バイオリン図" in graph_type:
                    parts = ax.violinplot(vals, positions=[pos], widths=width, showmeans=False, showextrema=False)
                    for pc in parts['bodies']:
                        pc.set_facecolor(color)
                        pc.set_edgecolor('black')
                        pc.set_alpha(0.8)
                        pc.set_zorder(1)

                # 個別データ点 (Strip Plot) - すべての種類で重ね書き可能
                if show_points:
                    noise = np.random.normal(0, jitter_strength * width, len(vals))
                    edge_c = 'gray' if dot_size > 10 else 'none'
                    ax.scatter(pos + noise, vals, color='white', edgecolor=edge_c, 
                               s=dot_size, alpha=dot_alpha, zorder=3)

            plot_group(ax, pos1, g1, color1)
            plot_group(ax, pos2, g2, color2)

            # X軸設定
            ticks, labels = [], []
            if has_g1: ticks.append(pos1); labels.append(group1_name)
            if has_g2: ticks.append(pos2); labels.append(group2_name)
            ax.set_xticks(ticks)
            ax.set_xticklabels(labels, fontsize=11)
            ax.set_title(data['name'], fontsize=12, pad=10)
            
            # 有意差表示
            sig_text = data['sig']
            if sig_text:
                current_max = 0
                if has_g1: current_max = max(current_max, np.max(g1))
                if has_g2: current_max = max(current_max, np.max(g2))
                y_line = current_max * 1.15
                h = current_max * 0.03
                lx_start, lx_end = (pos1, pos2) if has_g1 and has_g2 else (pos1-0.1, pos1+0.1)
                ax.plot([lx_start, lx_start, lx_end, lx_end], [y_line-h, y_line, y_line, y_line-h], lw=1.5, c='k')
                ax.text((lx_start+lx_end)/2, y_line + current_max*0.02, sig_text, ha='center', va='bottom', fontsize=14, color='k')

            # 軸装飾
            ax.set_ylim(0, y_limit)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            if i == 0:
                ax.set_ylabel(y_axis_label, fontsize=14)
            else:
                ax.spines['left'].set_visible(False)
                ax.tick_params(axis='y', left=False, labelleft=False)

        # 凡例
        if show_legend:
            handles = [mpatches.Patch(facecolor=color1, edgecolor='black', label=group1_name),
                       mpatches.Patch(facecolor=color2, edgecolor='black', label=group2_name)]
            fig.legend(handles=handles, loc='center left', bbox_to_anchor=(0.92, 0.5), frameon=False, fontsize=12)

        st.pyplot(fig)

        # ダウンロード設定 (JSTタイムスタンプ付き)
        img = io.BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight', dpi=300) 
        now = datetime.datetime.now() + datetime.timedelta(hours=9)
        st.download_button("画像をダウンロード", data=img, 
                           file_name=f"graph_{now.strftime('%Y%m%d_%H%M%S')}.png", 
                           mime="image/png")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
else:
    st.info("データを入力してください。自動的にプレビューが作成されます。")
