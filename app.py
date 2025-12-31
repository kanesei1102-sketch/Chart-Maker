import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import numpy as np
import datetime

# ---------------------------------------------------------
# 1. ページ構成とセッション管理
# ---------------------------------------------------------
st.set_page_config(page_title="Sci-Graph Maker Pro", layout="wide")
st.title("📊 Sci-Graph Maker Pro (日本語版)")
st.markdown("""
**データの完全性と専門的な可視化:** 画像解析ツールのCSV連携、ハイブリッド入力、そして論文投稿クオリティのレイアウト制御を統合。
""")

# セッション管理（動的な条件追加用）
if 'cond_count' not in st.session_state:
    st.session_state.cond_count = 3

def add_condition():
    st.session_state.cond_count += 1

def remove_condition():
    if st.session_state.cond_count > 1:
        st.session_state.cond_count -= 1

# ---------------------------------------------------------
# 2. サイドバー：プロフェッショナル・コントロールパネル
# ---------------------------------------------------------
with st.sidebar:
    st.header("🛠️ 全体設定")
    
    with st.expander("📈 グラフ種類と統計", expanded=True):
        graph_type = st.selectbox("グラフの種類", ["棒グラフ (平均値)", "箱ひげ図 (中央値)", "バイオリン図 (分布)"])
        if "棒" in graph_type:
            error_type = st.radio("エラーバーの種類", ["SD (標準偏差)", "SEM (標準誤差)"])
        
        fig_title = st.text_input("図のタイトル", value="Experimental Result")
        y_axis_label = st.text_input("Y軸のラベル", value="Relative Intensity (%)")
        manual_y_max = st.number_input("Y軸の最大値を固定 (0で自動)", value=0.0)

    st.divider()
    st.header("📂 データソース")
    # CSVインテグリティ・モジュール
    uploaded_csv = st.file_uploader("解析ツールから出力したCSVをアップロード", type="csv")
    
    st.subheader("手動データ入力")
    st.button("＋ 条件を追加", on_click=add_condition)
    if st.session_state.cond_count > 1:
        st.button("－ 条件を削除", on_click=remove_condition)

    st.divider()
    st.header("🎨 デザインと配色")
    
    with st.expander("ラベルと色", expanded=True):
        group1_name = st.text_input("グループ1の名前", value="Control")
        color1 = st.color_picker("グループ1の色", "#999999")
        group2_name = st.text_input("グループ2の名前", value="Target")
        color2 = st.color_picker("グループ2の色", "#66c2a5")
        show_legend = st.checkbox("凡例を表示する", value=True)

    with st.expander("📏 レイアウト微調整 (幅連動)", expanded=True):
        bar_width = st.slider("要素の太さ (棒/箱)", 0.1, 1.5, 0.6, 0.1)
        bar_gap = st.slider("グループ間の隙間", 0.0, 1.0, 0.05, 0.01)
        cap_size = st.slider("エラーバーの横線幅", 0.0, 15.0, 5.0, 0.5)
        st.divider()
        fig_height = st.slider("グラフ全体の高さ", 3.0, 15.0, 5.0, 0.5)
        # 軸を繋げるためのwspace（0推奨）
        wspace_val = st.slider("条件間の余白 (wspace)", 0.0, 1.0, 0.0, 0.05)

    with st.expander("✨ 個別プロット (点) の微調整"):
        show_points = st.checkbox("個別データ点を表示", value=True)
        dot_size = st.slider("点のサイズ", 1, 200, 20) 
        dot_alpha = st.slider("点の透明度 (Alpha)", 0.1, 1.0, 0.6, 0.1)
        jitter_strength = st.slider("散らばり具合 (Jitter)", 0.0, 0.5, 0.04, 0.01)
        # --- サイドバーの最後の方に追加 ---
    with st.sidebar:
        st.divider()
        st.caption("【免責事項 / Disclaimer】")
        st.caption("""
        本ツールは統計データの可視化を目的としています。
        表示される有意差ラベルやグラフの形状は、入力された数値に基づいて自動生成されるものであり、
        その生物学的・科学的な妥当性については、利用者が専門的知見に基づいて判断してください。
    
        This tool is for data visualization purposes. Final interpretations 
        should be made by the user based on professional expertise.
        """)

# ---------------------------------------------------------
# 3. データ処理パイプライン (ハイブリッド形式)
# ---------------------------------------------------------
cond_data_list = [] 

# A. CSVインポート（自動処理）
if uploaded_csv:
    try:
        csv_df = pd.read_csv(uploaded_csv)
        if 'Group' in csv_df.columns and 'Value' in csv_df.columns:
            for g_name in csv_df['Group'].unique():
                g_vals = csv_df[csv_df['Group'] == g_name]['Value'].dropna().tolist()
                cond_data_list.append({'name': g_name, 'g1': g_vals, 'g2': [], 'sig': ""})
            st.sidebar.success(f"CSVから {len(csv_df['Group'].unique())} グループを読み込みました")
    except Exception as e:
        st.sidebar.error(f"CSV読み込みエラー: {e}")

# B. 手動入力（動的処理）
for i in range(st.session_state.cond_count):
    with st.container():
        st.markdown("---")
        def_name = ["DMSO", "Drug A", "Drug B", "Drug C"][i] if i < 4 else f"条件_{i+1}"
        c_meta, c_g1, c_g2 = st.columns([1.5, 2, 2])
        
        with c_meta:
            st.markdown(f"#### 条件 {i+1}")
            cond_name = st.text_input("条件名", value=def_name, key=f"name_{i}")
            sig_label = st.text_input("有意差ラベル", placeholder="例: **", key=f"sig_{i}")
        
        with c_g1:
            st.write(f"▼ **{group1_name}**")
            def_v1 = "100\n105\n98\n102" if i == 0 and not uploaded_csv else ""
            input1 = st.text_area(f"データ1", value=def_v1, height=100, key=f"d1_{i}", label_visibility="collapsed")
        
        with c_g2:
            st.write(f"▼ **{group2_name}**")
            def_v2 = "80\n75\n85\n82" if i == 0 and not uploaded_csv else ""
            input2 = st.text_area(f"データ2", value=def_v2, height=100, key=f"d2_{i}", label_visibility="collapsed")

        # パース処理（カンマや改行に対応）
        v1, v2 = [], []
        if input1:
            try: v1 = [float(x.strip()) for x in input1.replace(',', '\n').split('\n') if x.strip()]
            except: st.error(f"形式エラー: {cond_name} - {group1_name}")
        if input2:
            try: v2 = [float(x.strip()) for x in input2.replace(',', '\n').split('\n') if x.strip()]
            except: st.error(f"形式エラー: {cond_name} - {group2_name}")
        
        if v1 or v2:
            cond_data_list.append({'name': cond_name, 'g1': v1, 'g2': v2, 'sig': sig_label})

# ---------------------------------------------------------
# 4. 最終グラフ描画モジュール
# ---------------------------------------------------------
if cond_data_list:
    st.subheader("グラフ・プレビュー")
    try:
        n_plots = len(cond_data_list)
        # 条件数に応じてキャンバス幅を動的に決定
        fig, axes = plt.subplots(1, n_plots, figsize=(n_plots * 3.5, fig_height), sharey=True)
        if n_plots == 1: axes = [axes]
        
        plt.subplots_adjust(wspace=0)
        plt.rcParams['font.family'] = 'sans-serif'
        fig.suptitle(fig_title, fontsize=16, y=1.05)

        # 全体のスケール計算
        all_vals = []
        has_any_g1, has_any_g2 = False, False
        for d in cond_data_list:
            all_vals.extend(d['g1'] + d['g2'])
            if d['g1']: has_any_g1 = True
            if d['g2']: has_any_g2 = True
        
        y_max_limit = manual_y_max if manual_y_max > 0 else (max(all_vals) * 1.35 if all_vals else 100)

        # 描画ループ
        for i, ax in enumerate(axes):
            data = cond_data_list[i]
            g1, g2 = np.array(data['g1']), np.array(data['g2'])
            h_g1, h_g2 = len(g1) > 0, len(g2) > 0
            
            # 要素の太さと隙間に基づく座標マッピング
            pos1, pos2 = (-(bar_width/2 + bar_gap/2), +(bar_width/2 + bar_gap/2)) if h_g1 and h_g2 else (0, 0)

            def plot_core_internal(ax, pos, vals, color):
                if len(vals) == 0: return
                
                mean_v = np.mean(vals)
                std_v = np.std(vals, ddof=1) if len(vals) > 1 else 0
                
                # 統計オプションの分岐
                if "棒グラフ" in graph_type and "SEM" in error_type:
                    err_v = std_v / np.sqrt(len(vals))
                else:
                    err_v = std_v

                # 形状別の描画
                if "棒グラフ" in graph_type:
                    ax.bar(pos, mean_v, width=bar_width, color=color, edgecolor='black', linewidth=1.2, zorder=1)
                    ax.errorbar(pos, mean_v, yerr=err_v, fmt='none', color='black', capsize=cap_size, elinewidth=1.5, zorder=2)
                elif "箱ひげ図" in graph_type:
                    ax.boxplot(vals, positions=[pos], widths=bar_width, patch_artist=True, showfliers=False,
                               boxprops=dict(facecolor=color, color='black', linewidth=1.2),
                               medianprops=dict(color='black', linewidth=1.5),
                               whiskerprops=dict(linewidth=1.2), capprops=dict(linewidth=1.2), zorder=1)
                elif "バイオリン図" in graph_type:
                    v_parts = ax.violinplot(vals, positions=[pos], widths=bar_width, showextrema=False)
                    for pc in v_parts['bodies']:
                        pc.set_facecolor(color); pc.set_edgecolor('black'); pc.set_alpha(0.7); pc.set_zorder(1)

                # 個別ドット（ユニバーサル・オーバーレイ）
                if show_points:
                    noise = np.random.normal(0, jitter_strength * bar_width, len(vals))
                    edge_c = 'gray' if dot_size > 15 else 'none'
                    ax.scatter(pos + noise, vals, color='white', edgecolor=edge_c, s=dot_size, alpha=dot_alpha, zorder=3)

            # 実行
            plot_core_internal(ax, pos1, g1, color1)
            plot_core_internal(ax, pos2, g2, color2)

            # 軸と目盛りの設定
            tks, lbs = [], []
            if h_g1: tks.append(pos1); lbs.append(group1_name)
            if h_g2: tks.append(pos2); lbs.append(group2_name)
            ax.set_xticks(tks)
            ax.set_xticklabels(lbs, fontsize=11)
            ax.set_title(data['name'], fontsize=12, pad=12)
            ax.set_ylim(0, y_max_limit)

            # 有意差ラベルの動的配置
            if data['sig']:
                c_max = max([max(g1) if h_g1 else 0, max(g2) if h_g2 else 0])
                y_bracket = c_max * 1.15
                bracket_h = c_max * 0.03
                lx_s, lx_e = (pos1, pos2) if h_g1 and h_g2 else (pos1-0.2, pos1+0.2)
                ax.plot([lx_s, lx_s, lx_e, lx_e], [y_bracket-bracket_h, y_bracket, y_bracket, y_bracket-bracket_h], lw=1.5, c='k')
                ax.text((lx_s+lx_e)/2, y_bracket + c_max*0.02, data['sig'], ha='center', va='bottom', fontsize=14)

            # 枠線（Spines）のスタイリング
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_linewidth(1.5)
            ax.spines['bottom'].set_visible(True)
            ax.spines['bottom'].set_color('black')
            if i == 0:
                ax.set_ylabel(y_axis_label, fontsize=14)
                ax.spines['left'].set_linewidth(1.2)
            else:
                ax.spines['left'].set_visible(False)
                ax.tick_params(axis='y', left=False)
            if i > 0:
                ax.spines['left'].set_visible(False)
                ax.tick_params(axis='y', left=False) 

            # 表示範囲の自動調整（要素の切見防止）
            view_margin = 0.5
            edge_coord = (bar_width/2 + bar_gap/2) + bar_width/2
            ax.set_xlim(-(edge_coord + view_margin), (edge_coord + view_margin))

        # 凡例モジュール
        if show_legend:
            lh = []
            if has_any_g1: lh.append(mpatches.Patch(facecolor=color1, edgecolor='black', label=group1_name))
            if has_any_g2: lh.append(mpatches.Patch(facecolor=color2, edgecolor='black', label=group2_name))
            if lh: fig.legend(handles=lh, loc='center left', bbox_to_anchor=(0.93, 0.5), frameon=False, fontsize=12)

        st.pyplot(fig)

        # 日本時間（JST）タイムスタンプによる画像保存
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
        now_jst = datetime.datetime.now() + datetime.timedelta(hours=9)
        st.download_button("📥 高品質画像をダウンロード", data=img_buf, 
                           file_name=f"sci_graph_{now_jst.strftime('%Y%m%d_%H%M%S')}.png", mime="image/png")

    except Exception as e:
        st.error(f"描画エラー: {e}")
else:
    st.info("データ待機中: CSVをアップロードするか、手動でデータを入力してグラフを生成してください。")
