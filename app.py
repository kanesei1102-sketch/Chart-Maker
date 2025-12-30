import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
import numpy as np

# ---------------------------------------------------------
# 設定
# ---------------------------------------------------------
st.set_page_config(page_title="Bar Plot Maker (Manual Layout)", layout="wide")
st.title("📊 棒グラフ作成ツール（完全位置制御版）")
st.markdown("""
**修正:** 棒グラフの位置を完全に固定しました。
太さを変えても、棒同士が離れていくことはありません。プロットも常に中央に来ます。
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
    
    st.subheader("形状と配置")
    # ★ここがポイント: 棒の太さと隙間を直接指定
    bar_width = st.slider("棒グラフの幅 (Width)", min_value=0.2, max_value=1.0, value=0.6, step=0.1)
    bar_gap = st.slider("棒の間の隙間 (Gap)", min_value=0.0, max_value=0.5, value=0.05, step=0.01)
    
    cap_size = st.slider("エラーバーの横線 (Capsize)", min_value=0.0, max_value=10.0, value=5.0, step=1.0)
    
    # ドットのサイズ
    dot_size = st.slider("プロットのサイズ", 10, 100, 40)

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

        # データをリスト化して保存
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
        
        # 少なくともどちらかにデータがあれば追加
        if vals1 or vals2:
            cond_data_list.append({
                'name': cond_name,
                'g1': vals1,
                'g2': vals2,
                'sig': sig_label
            })

# ---------------------------------------------------------
# グラフ描画 (Matplotlibによる完全手動描画)
# ---------------------------------------------------------
if cond_data_list:
    st.subheader("プレビュー")
    
    try:
        # 全データの最大値を見つけてY軸範囲を決める
        all_vals = []
        for item in cond_data_list:
            all_vals.extend(item['g1'])
            all_vals.extend(item['g2'])
        
        if not all_vals:
            st.warning("有効な数値データがありません")
            st.stop()
            
        global_max = max(all_vals)
        y_limit = global_max * 1.35
        
        # キャンバスの準備
        n_plots = len(cond_data_list)
        # グラフの数は可変、縦軸共有(sharey=True)
        fig, axes = plt.subplots(1, n_plots, figsize=(n_plots * 3, 5), sharey=True)
        
        # 1つだけの場合axesはリストではないのでリスト化
        if n_plots == 1:
            axes = [axes]
            
        plt.subplots_adjust(wspace=0) # グラフ間の隙間をゼロにする
        plt.rcParams['font.family'] = 'sans-serif'

        # --- 各条件ごとのループ ---
        for i, ax in enumerate(axes):
            data = cond_data_list[i]
            g1 = np.array(data['g1'])
            g2 = np.array(data['g2'])
            
            # --- 座標の計算 ---
            # 中心を0として、左右に配置
            # 2群ある場合:
            # Group1: x = - (幅/2 + 隙間/2)
            # Group2: x = + (幅/2 + 隙間/2)
            
            has_g1 = len(g1) > 0
            has_g2 = len(g2) > 0
            
            # 位置決定ロジック
            if has_g1 and has_g2:
                pos1 = -(bar_width/2 + bar_gap/2)
                pos2 = +(bar_width/2 + bar_gap/2)
            else:
                # 1群しかない場合は真ん中(0)に配置
                pos1 = 0
                pos2 = 0

            # --- 棒グラフの描画 ---
            # Group 1
            if has_g1:
                mean1 = np.mean(g1)
                std1 = np.std(g1, ddof=1) if len(g1) > 1 else 0
                
                # 棒
                ax.bar(pos1, mean1, width=bar_width, color=color1, edgecolor='black', zorder=1)
                # エラーバー
                ax.errorbar(pos1, mean1, yerr=std1, fmt='none', color='black', capsize=cap_size, elinewidth=1.5, zorder=2)
                # 散布図 (Jitter処理)
                # x座標を少し散らす
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

            # --- X軸ラベルの設定 ---
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
            
            # 条件名（タイトル）
            ax.set_title(data['name'], fontsize=12, pad=10)
            
            # --- 有意差ライン ---
            sig_text = data['sig']
            if sig_text:
                # その条件内での最大値を探す
                current_max = 0
                if has_g1: current_max = max(current_max, np.max(g1))
                if has_g2: current_max = max(current_max, np.max(g2))
                
                y_line = current_max * 1.15
                h = current_max * 0.03
                
                # ラインを引くX座標
                if has_g1 and has_g2:
                    lx_start, lx_end = pos1, pos2
                elif has_g1:
                    lx_start, lx_end = pos1 - bar_width/3, pos1 + bar_width/3
                else: # g2 only
                    lx_start, lx_end = pos2 - bar_width/3, pos2 + bar_width/3
                
                ax.plot([lx_start, lx_start, lx_end, lx_end], [y_line-h, y_line, y_line, y_line-h], lw=1.5, c='k')
                ax.text((lx_start+lx_end)/2, y_line + current_max*0.02, sig_text, ha='center', va='bottom', fontsize=14, color='k')

            # --- 軸と枠線の整形 ---
            ax.set_ylim(0, y_limit)
            
            # 上と右の枠を消す
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # 下の枠（X軸）
            ax.spines['bottom'].set_visible(True)
            ax.spines['bottom'].set_color('black')
            ax.spines['bottom'].set_linewidth(1.2)
            
            # 左の枠（Y軸）
            if i == 0:
                ax.spines['left'].set_visible(True)
                ax.spines['left'].set_color('black')
                ax.spines['left'].set_linewidth(1.2)
                ax.set_ylabel("Number of cells", fontsize=14)
                ax.tick_params(axis='y', left=True, labelleft=True, width=1.2)
            else:
                ax.spines['left'].set_visible(False)
                ax.tick_params(axis='y', left=False, labelleft=False)

            # X軸の範囲を調整（棒が見切れないように）
            # 中心0から、棒の端まで + 余白
            margin = 0.5 # 適当な余白
            max_pos = (bar_width/2 + bar_gap/2) + bar_width/2
            ax.set_xlim(-(max_pos + margin), (max_pos + margin))

        st.pyplot(fig)

        img = io.BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight')
        st.download_button("画像をダウンロード", data=img, file_name="manual_fixed_plot.png", mime="image/png")

    except Exception as e:
        st.error(f"描画エラー: {e}")
else:
    st.info("データを入力してください")
