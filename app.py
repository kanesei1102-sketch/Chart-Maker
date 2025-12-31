import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import numpy as np
import datetime

# ---------------------------------------------------------
# 1. ページ基本設定
# ---------------------------------------------------------
st.set_page_config(page_title="Sci-Graph Maker Pro Max", layout="wide")
st.title("📊 Sci-Graph Maker: 要素幅・完全制御版")
st.markdown("""
**正確なレイアウト制御:** 棒や箱の「太さ」、グループ間の「距離」、グラフ同士の「間隔」をすべて個別に調整可能です。
""")

# セッション状態（手動入力の管理）
if 'cond_count' not in st.session_state:
    st.session_state.cond_count = 0 

def add_condition():
    st.session_state.cond_count += 1

def remove_condition():
    if st.session_state.cond_count > 0:
        st.session_state.cond_count -= 1

# ---------------------------------------------------------
# 2. サイドバー設定（コントロールパネル）
# ---------------------------------------------------------
with st.sidebar:
    st.header("1. グラフ・統計設定")
    graph_type = st.selectbox("グラフの種類:", ["棒グラフ (Bar)", "箱ひげ図 (Box)", "バイオリン図 (Violin)"])
    if "棒グラフ" in graph_type:
        error_bar_type = st.radio("エラーバーの種類:", ["SD (標準偏差)", "SEM (標準誤差)"])
    
    fig_title = st.text_input("図のタイトル", value="Experimental Result")
    y_axis_label = st.text_input("Y軸のタイトル", value="Quantified Value")
    manual_y_max = st.number_input("Y軸の最大値 (0で自動)", value=0.0)

    st.divider()
    st.header("2. 🎨 デザインと凡例")
    with st.expander("グループ名と色", expanded=True):
        group1_name = st.text_input("グループ1の名前", value="Control")
        color1 = st.color_picker("グループ1の色", "#999999") 
        st.divider()
        group2_name = st.text_input("グループ2の名前", value="Target")
        color2 = st.color_picker("グループ2の色", "#66c2a5") 
        st.divider()
        show_legend = st.checkbox("凡例を表示する", value=True)

    # --- ここが最重要：レイアウト微調整セクション ---
    st.divider()
    st.header("3. 📏 レイアウト微調整")
    with st.expander("サイズと間隔の制御", expanded=True):
        st.markdown("**【箱・棒の太さ設定】**")
        # ★ 箱そのものの太さを変えるスライダー
        element_width = st.slider("棒・箱の太さ (Width)", 0.1, 2.0, 0.6, 0.05)
        
        st.markdown("**【グループ内の距離】**")
        # ★ G1とG2がどのくらい離れるか
        group_gap = st.slider("グループ間の隙間 (Gap)", 0.0, 1.0, 0.1, 0.05)
        
        st.divider()
        st.markdown("**【図全体のスケール】**")
        fig_height = st.slider("グラフの高さ", 3.0, 15.0, 6.0, 0.5)
        fig_width_scale = st.slider("1条件あたりの横幅", 1.0, 10.0, 4.0, 0.5)
        
        st.divider()
        st.markdown("**【条件（グラフ）同士の距離】**")
        wspace_val = st.slider("グラフ間の余白 (wspace)", 0.0, 1.0, 0.2, 0.05)

        if "棒グラフ" in graph_type:
            cap_size = st.slider("エラーバー横線 (Cap)", 0.0, 15.0, 5.0, 1.0)

    with st.expander("✨ ドット(N)の調整"):
        show_points = st.checkbox("データ点を表示", value=True)
        dot_size = st.slider("点サイズ", 1, 100, 20) 
        dot_alpha = st.slider("透明度", 0.1, 1.0, 0.6)
        jitter = st.slider("散らばり幅", 0.0, 0.5, 0.05)

# ---------------------------------------------------------
# 3. データ入力処理
# ---------------------------------------------------------
cond_data_list = [] 
st.header("📂 Step 1: CSVデータの読み込み")
uploaded_csv = st.file_uploader("解析ツールのCSVをアップロード", type="csv")
if uploaded_csv:
    ext_df = pd.read_csv(uploaded_csv)
    for g_name in ext_df['Group'].unique():
        g_data = ext_df[ext_df['Group'] == g_name]['Value'].tolist()
        cond_data_list.append({'name': g_name, 'g1': g_data, 'g2': [], 'sig': ""})

st.divider()
st.header("✍️ Step 2: 手動データの追加")
c_btn1, c_btn2, _ = st.columns([1, 1, 3])
with c_btn1: st.button("＋ 条件追加", on_click=add_condition)
with c_btn2: st.button("－ 条件削除", on_click=remove_condition)

for i in range(st.session_state.cond_count):
    with st.container():
        st.markdown(f"**追加条件 {i+1}**")
        col1, col2, col3 = st.columns([1.5, 2, 2])
        with col1:
            c_name = st.text_input("条件名", value=f"Exp_{i+1}", key=f"cn_{i}")
            sig_txt = st.text_input("有意差ラベル", key=f"sig_{i}")
        with col2: v1_in = st.text_area(f"{group1_name} データ", key=f"v1_{i}")
        with col3: v2_in = st.text_area(f"{group2_name} データ", key=f"v2_{i}")
        try:
            v1_list = [float(x) for x in v1_in.split() if x]
            v2_list = [float(x) for x in v2_in.split() if x]
            if v1_list or v2_list:
                cond_data_list.append({'name': c_name, 'g1': v1_list, 'g2': v2_list, 'sig': sig_txt})
        except: pass

# ---------------------------------------------------------
# 4. 描画セクション（レイアウト制御ロジック）
# ---------------------------------------------------------
if cond_data_list:
    st.divider()
    try:
        n = len(cond_data_list)
        # 全体の図の幅を「1条件あたりの幅 * 条件数」で計算
        fig, axes = plt.subplots(1, n, figsize=(n * fig_width_scale, fig_height), sharey=True)
        if n == 1: axes = [axes]
        
        plt.subplots_adjust(wspace=wspace_val)
        fig.suptitle(fig_title, fontsize=16, y=1.05)

        # Y軸の最大値設定
        all_vals = []
        for d in cond_data_list: all_vals.extend(d['g1'] + d['g2'])
        y_top = manual_y_max if manual_y_max > 0 else max(all_vals) * 1.35

        for i, ax in enumerate(axes):
            data = cond_data_list[i]
            g1, g2 = np.array(data['g1']), np.array(data['g2'])
            
            # ★ ここで element_width と group_gap を使って位置を正確に計算
            pos1, pos2 = (-(element_width/2 + group_gap/2), +(element_width/2 + group_gap/2)) if len(g1)>0 and len(g2)>0 else (0, 0)

            def draw_group(ax, pos, vals, col):
                if len(vals) == 0: return
                
                # --- A. 棒グラフ ---
                if "棒" in graph_type:
                    m = np.mean(vals)
                    e = np.std(vals, ddof=1)
                    if error_bar_type == "SEM (標準誤差)": e /= np.sqrt(len(vals))
                    ax.bar(pos, m, width=element_width, color=col, edgecolor='black', zorder=1)
                    ax.errorbar(pos, m, yerr=e, fmt='none', color='black', capsize=cap_size, zorder=2)
                
                # --- B. 箱ひげ図 ---
                elif "箱" in graph_type:
                    ax.boxplot(vals, positions=[pos], widths=element_width, patch_artist=True, showfliers=False,
                               boxprops=dict(facecolor=col, edgecolor='black'),
                               medianprops=dict(color="black", linewidth=1.5), zorder=1)
                
                # --- C. バイオリン図 ---
                elif "バイオリン" in graph_type:
                    vp = ax.violinplot(vals, positions=[pos], widths=element_width, showextrema=False)
                    for pc in vp['bodies']:
                        pc.set_facecolor(col)
                        pc.set_edgecolor('black')
                        pc.set_alpha(0.7)
                
                # --- 共通: 個別ドット ---
                if show_points:
                    nj = np.random.normal(0, jitter * element_width, len(vals))
                    ax.scatter(pos + nj, vals, color='white', edgecolor='gray', s=dot_size, alpha=dot_alpha, zorder=3)

            draw_group(ax, pos1, g1, color1)
            draw_group(ax, pos2, g2, color2)

            # X軸とタイトルの設定
            ax.set_xticks([pos1, pos2] if len(g1)>0 and len(g2)>0 else [0])
            ax.set_xticklabels([group1_name, group2_name] if len(g1)>0 and len(g2)>0 else [""], fontsize=10)
            ax.set_title(data['name'], fontsize=12, pad=10)
            ax.set_ylim(0, y_top)
            
            # 装飾
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            if i == 0:
                ax.set_ylabel(y_axis_label, fontsize=13)
            else:
                ax.spines['left'].set_visible(False)
                ax.tick_params(axis='y', left=False)

        # 凡例
        if show_legend:
            lh = [mpatches.Patch(facecolor=color1, edgecolor='black', label=group1_name),
                  mpatches.Patch(facecolor=color2, edgecolor='black', label=group2_name)]
            fig.legend(handles=lh, loc='center left', bbox_to_anchor=(1.0, 0.5), frameon=False)
        
        st.pyplot(fig)
        
        # 保存ボタン
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=300)
        now = datetime.datetime.now() + datetime.timedelta(hours=9)
        st.download_button("📸 グラフを保存", buf, f"graph_{now.strftime('%Y%m%d_%H%M%S')}.png")
        
    except Exception as e:
        st.error(f"描画中にエラーが発生しました: {e}")
else:
    st.info("CSVをアップロード、または手動で条件を追加してください。")
