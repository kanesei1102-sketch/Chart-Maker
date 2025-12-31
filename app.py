import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import numpy as np
import datetime

# ---------------------------------------------------------
# ページ基本設定
# ---------------------------------------------------------
st.set_page_config(page_title="Sci-Graph Maker Pro Max (Hybrid)", layout="wide")
st.title("📊 Sci-Graph Maker: ハイブリッド・ワークフロー")
st.markdown("""
**ハイブリッド仕様:** 解析ツールのCSVを読み込みつつ、不足している条件を手動で自由に追加できます。
""")

# セッション状態（手動入力の列数管理）
if 'cond_count' not in st.session_state:
    st.session_state.cond_count = 0 

def add_condition():
    st.session_state.cond_count += 1

def remove_condition():
    if st.session_state.cond_count > 0:
        st.session_state.cond_count -= 1

# ---------------------------------------------------------
# サイドバー設定
# ---------------------------------------------------------
with st.sidebar:
    st.header("1. グラフ全体設定")
    graph_type = st.selectbox("グラフの種類:", ["棒グラフ (Bar)", "箱ひげ図 (Box)", "バイオリン図 (Violin)"])
    
    if "棒グラフ" in graph_type:
        error_bar_type = st.radio("エラーバーの種類:", ["SD (標準偏差)", "SEM (標準誤差)"])
    
    fig_title = st.text_input("図のタイトル", value="Experimental Result")
    y_axis_label = st.text_input("Y軸のタイトル", value="Quantified Value")
    manual_y_max = st.number_input("Y軸の最大値を固定 (0で自動)", value=0.0)

    st.divider()
    st.header("2. デザインとスタイル")
    
    with st.expander("🎨 色と凡例の名前", expanded=True):
        # ★ここを修正：名前を自由に変えられるように復活させました
        group1_name = st.text_input("グループ1の名前", value="Control")
        color1 = st.color_picker("グループ1の色", "#999999") 
        
        st.divider()
        
        group2_name = st.text_input("グループ2の名前", value="Target")
        color2 = st.color_picker("グループ2の色", "#66c2a5") 
        
        st.divider()
        show_legend = st.checkbox("凡例を表示する", value=True)

    with st.expander("✨ プロット(点)の微調整"):
        show_points = st.checkbox("個別データ点を表示する", value=True)
        dot_size = st.slider("点のサイズ", 1, 100, 20) 
        dot_alpha = st.slider("点の透明度 (Alpha)", 0.1, 1.0, 0.6)
        jitter_strength = st.slider("散らばり具合 (Jitter)", 0.0, 0.3, 0.04)

# ---------------------------------------------------------
# メイン：データ入力セクション
# ---------------------------------------------------------
cond_data_list = [] 

# --- A. CSVアップロードセクション ---
st.header("📂 Step 1: CSVデータの読み込み (任意)")
uploaded_csv = st.file_uploader("解析ツールから出力したCSVを選択してください", type="csv")

if uploaded_csv:
    ext_df = pd.read_csv(uploaded_csv)
    for g_name in ext_df['Group'].unique():
        g_data = ext_df[ext_df['Group'] == g_name]['Value'].tolist()
        cond_data_list.append({
            'name': g_name,
            'g1': g_data, 
            'g2': [], 
            'sig': "",
            'source': 'csv'
        })
    st.success(f"CSVから {len(ext_df['Group'].unique())} グループのデータを読み込みました。")

st.divider()

# --- B. 手動入力セクション ---
st.header("✍️ Step 2: 手動データの追加")
col_btn1, col_btn2, _ = st.columns([1, 1, 3])
with col_btn1:
    st.button("＋ 条件を追加", on_click=add_condition)
with col_btn2:
    st.button("－ 条件を削除", on_click=remove_condition)

for i in range(st.session_state.cond_count):
    with st.container():
        st.markdown(f"**追加条件 {i+1}**")
        c_meta, c_g1, c_g2 = st.columns([1.5, 2, 2])
        with c_meta:
            cond_name = st.text_input("条件名", value=f"Manual_{i+1}", key=f"name_{i}")
            sig_label = st.text_input("有意差", placeholder="e.g. **", key=f"sig_{i}")
        with c_g1:
            input1 = st.text_area(f"{group1_name} のデータ", key=f"d1_{i}", help="改行区切りで入力")
        with c_g2:
            input2 = st.text_area(f"{group2_name} のデータ", key=f"d2_{i}", help="比較対象がある場合のみ入力")

        vals1, vals2 = [], []
        try:
            if input1: vals1 = [float(x.strip()) for x in input1.strip().split('\n') if x.strip()]
            if input2: vals2 = [float(x.strip()) for x in input2.strip().split('\n') if x.strip()]
        except:
            st.error(f"追加条件 {i+1} に数値以外の文字が含まれています。")
            
        if vals1 or vals2:
            cond_data_list.append({
                'name': cond_name, 
                'g1': vals1, 
                'g2': vals2, 
                'sig': sig_label,
                'source': 'manual'
            })

# ---------------------------------------------------------
# 描画セクション
# ---------------------------------------------------------
if cond_data_list:
    st.divider()
    st.subheader("📊 最終グラフプレビュー")
    try:
        n_plots = len(cond_data_list)
        fig, axes = plt.subplots(1, n_plots, figsize=(max(n_plots * 3, 5), 5), sharey=True)
        if n_plots == 1: axes = [axes]
        
        plt.subplots_adjust(wspace=0.1)
        fig.suptitle(fig_title, fontsize=16, y=1.08)

        all_vals = []
        for d in cond_data_list: all_vals.extend(d['g1'] + d['g2'])
        y_limit = manual_y_max if manual_y_max > 0 else max(all_vals) * 1.35

        for i, ax in enumerate(axes):
            data = cond_data_list[i]
            g1, g2 = np.array(data['g1']), np.array(data['g2'])
            
            w, gap_val = 0.6, 0.05
            pos1, pos2 = (-(w/2 + gap_val/2), +(w/2 + gap_val/2)) if len(g1)>0 and len(g2)>0 else (0, 0)

            def draw_element(ax, pos, vals, color):
                if len(vals) == 0: return
                if "棒グラフ" in graph_type:
                    mean = np.mean(vals)
                    err = np.std(vals, ddof=1)
                    if error_bar_type == "SEM (標準誤差)":
                        err = err / np.sqrt(len(vals))
                    ax.bar(pos, mean, width=w, color=color, edgecolor='black', zorder=1)
                    ax.errorbar(pos, mean, yerr=err, fmt='none', color='black', capsize=5, zorder=2)
                elif "箱ひげ図" in graph_type:
                    ax.boxplot(vals, positions=[pos], widths=w, patch_artist=True, showfliers=False,
                               boxprops=dict(facecolor=color), medianprops=dict(color="black"), zorder=1)
                elif "バイオリン図" in graph_type:
                    vp = ax.violinplot(vals, positions=[pos], widths=w, showextrema=False)
                    for pc in vp['bodies']: pc.set_facecolor(color); pc.set_alpha(0.7); pc.set_zorder(1)

                if show_points:
                    noise = np.random.normal(0, jitter_strength * w, len(vals))
                    ax.scatter(pos + noise, vals, color='white', edgecolor='gray', s=dot_size, alpha=dot_alpha, zorder=3)

            draw_element(ax, pos1, g1, color1)
            draw_element(ax, pos2, g2, color2)

            # ★ここも修正：軸ラベルをサイドバーの名前に連動
            if len(g1)>0 and len(g2)>0:
                ax.set_xticks([pos1, pos2])
                ax.set_xticklabels([group1_name, group2_name], fontsize=9)
            else:
                ax.set_xticks([0])
                ax.set_xticklabels([""], fontsize=9)
            
            ax.set_title(data['name'], fontsize=11, pad=10)
            ax.set_ylim(0, y_limit)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            if i == 0: ax.set_ylabel(y_axis_label, fontsize=12)
            else: ax.spines['left'].set_visible(False); ax.tick_params(axis='y', left=False)

        # ★凡例のラベルをサイドバーの名前に連動
        if show_legend:
            handles = [mpatches.Patch(facecolor=color1, label=group1_name), 
                       mpatches.Patch(facecolor=color2, label=group2_name)]
            fig.legend(handles=handles, loc='center left', bbox_to_anchor=(0.98, 0.5), frameon=False)

        st.pyplot(fig)
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=300)
        now = datetime.datetime.now() + datetime.timedelta(hours=9)
        st.download_button("グラフ画像を保存", buf, f"hybrid_graph_{now.strftime('%Y%m%d_%H%M%S')}.png")

    except Exception as e:
        st.error(f"描画エラー: {e}")
else:
    st.info("CSVをアップロードするか、手動入力で条件を追加してください。")
