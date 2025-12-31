import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
import numpy as np
import datetime

# ---------------------------------------------------------
# 1. Page Configuration & Aesthetics
# ---------------------------------------------------------
st.set_page_config(page_title="Sci-Graph Maker Pro Max", layout="wide")
st.title("📊 Sci-Graph Maker Pro (The Grand Master Edition)")
st.markdown("""
**Data Integrity & Professional Visualization:** Image Quantifier連携、ハイブリッド入力、そして論文クオリティの微調整機能を完備した最終形態です。
""")

# Session Management
if 'cond_count' not in st.session_state:
    st.session_state.cond_count = 3

def add_condition():
    st.session_state.cond_count += 1

def remove_condition():
    if st.session_state.cond_count > 1:
        st.session_state.cond_count -= 1

# ---------------------------------------------------------
# 2. Sidebar: Professional Control Panel
# ---------------------------------------------------------
with st.sidebar:
    st.header("🛠️ Global Configuration")
    
    with st.expander("📈 Plot Type & Statistics", expanded=True):
        graph_type = st.selectbox("Graph Type", ["Bar Plot (Mean)", "Box Plot (Median)", "Violin Plot (Distribution)"])
        if "Bar" in graph_type:
            error_type = st.radio("Error Bar", ["SD (Standard Deviation)", "SEM (Standard Error)"])
        
        fig_title = st.text_input("Figure Title", value="Experimental Result")
        y_axis_label = st.text_input("Y-axis Label", value="Relative Intensity (%)")
        manual_y_max = st.number_input("Y-axis Max (0 for Auto)", value=0.0)

    st.divider()
    st.header("📂 Data Source")
    # CSV Integrity Module
    uploaded_csv = st.file_uploader("Upload CSV from Image Quantifier", type="csv")
    
    st.subheader("Manual Controls")
    st.button("＋ Add Condition", on_click=add_condition)
    if st.session_state.cond_count > 1:
        st.button("－ Remove Condition", on_click=remove_condition)

    st.divider()
    st.header("🎨 Aesthetics & Design")
    
    with st.expander("Colors & Labels", expanded=True):
        group1_name = st.text_input("Group 1 Label", value="Control")
        color1 = st.color_picker("Group 1 Color", "#999999")
        group2_name = st.text_input("Group 2 Label", value="Target")
        color2 = st.color_picker("Group 2 Color", "#66c2a5")
        show_legend = st.checkbox("Show Legend", value=True)

    with st.expander("📏 Precise Layout (Width Linkage)", expanded=True):
        # 元コードの「完璧な幅」ロジックをスライダー化
        bar_width = st.slider("Element Width (Bar/Box)", 0.1, 1.5, 0.6, 0.1)
        bar_gap = st.slider("Group Gap", 0.0, 1.0, 0.05, 0.01)
        cap_size = st.slider("Error Bar Capsize", 0.0, 15.0, 5.0, 0.5)
        st.divider()
        fig_height = st.slider("Figure Height", 3.0, 15.0, 5.0, 0.5)
        wspace_val = st.slider("Subplot Spacing (wspace)", 0.0, 1.0, 0.1, 0.05)

    with st.expander("✨ Individual Data Points (N)"):
        show_points = st.checkbox("Overlay Data Points", value=True)
        dot_size = st.slider("Dot Size", 1, 200, 20) 
        dot_alpha = st.slider("Dot Alpha", 0.1, 1.0, 0.6, 0.1)
        jitter_strength = st.slider("Jitter Strength", 0.0, 0.5, 0.04, 0.01)

# ---------------------------------------------------------
# 3. Data Processing Pipeline (Hybrid)
# ---------------------------------------------------------
cond_data_list = [] 

# A. CSV Import (Automated)
if uploaded_csv:
    try:
        csv_df = pd.read_csv(uploaded_csv)
        if 'Group' in csv_df.columns and 'Value' in csv_df.columns:
            for g_name in csv_df['Group'].unique():
                g_vals = csv_df[csv_df['Group'] == g_name]['Value'].dropna().tolist()
                cond_data_list.append({'name': g_name, 'g1': g_vals, 'g2': [], 'sig': ""})
            st.sidebar.success(f"Imported {len(csv_df['Group'].unique())} groups")
    except Exception as e:
        st.sidebar.error(f"CSV Error: {e}")

# B. Manual Entry (Dynamic)
for i in range(st.session_state.cond_count):
    with st.container():
        st.markdown("---")
        def_name = ["DMSO", "Drug A", "Drug B", "Drug C"][i] if i < 4 else f"Cond_{i+1}"
        c_meta, c_g1, c_g2 = st.columns([1.5, 2, 2])
        
        with c_meta:
            st.markdown(f"#### Condition {i+1}")
            cond_name = st.text_input("Name", value=def_name, key=f"name_{i}")
            sig_label = st.text_input("Sig.", placeholder="e.g. **", key=f"sig_{i}")
        
        with c_g1:
            st.write(f"▼ **{group1_name}**")
            def_v1 = "100\n105\n98\n102" if i == 0 and not uploaded_csv else ""
            input1 = st.text_area(f"Data 1", value=def_v1, height=100, key=f"d1_{i}", label_visibility="collapsed")
        
        with c_g2:
            st.write(f"▼ **{group2_name}**")
            def_v2 = "80\n75\n85\n82" if i == 0 and not uploaded_csv else ""
            input2 = st.text_area(f"Data 2", value=def_v2, height=100, key=f"d2_{i}", label_visibility="collapsed")

        # Parsing with robustness
        v1, v2 = [], []
        if input1:
            try: v1 = [float(x.strip()) for x in input1.replace(',', '\n').split('\n') if x.strip()]
            except: st.error(f"Format error in {cond_name} - {group1_name}")
        if input2:
            try: v2 = [float(x.strip()) for x in input2.replace(',', '\n').split('\n') if x.strip()]
            except: st.error(f"Format error in {cond_name} - {group2_name}")
        
        if v1 or v2:
            cond_data_list.append({'name': cond_name, 'g1': v1, 'g2': v2, 'sig': sig_label})

# ---------------------------------------------------------
# 4. Final Graph Visualization Module
# ---------------------------------------------------------
if cond_data_list:
    st.subheader("Final Preview")
    try:
        n_plots = len(cond_data_list)
        # Dynamic Width Calculation based on Condition count
        fig, axes = plt.subplots(1, n_plots, figsize=(n_plots * 3.5, fig_height), sharey=True)
        if n_plots == 1: axes = [axes]
        
        plt.subplots_adjust(wspace=wspace_val)
        plt.rcParams['font.family'] = 'sans-serif'
        fig.suptitle(fig_title, fontsize=16, y=1.05)

        # Global scale calculation
        all_vals = []
        has_any_g1, has_any_g2 = False, False
        for d in cond_data_list:
            all_vals.extend(d['g1'] + d['g2'])
            if d['g1']: has_any_g1 = True
            if d['g2']: has_any_g2 = True
        
        y_max_limit = manual_y_max if manual_y_max > 0 else (max(all_vals) * 1.35 if all_vals else 100)

        # Rendering Loop
        for i, ax in enumerate(axes):
            data = cond_data_list[i]
            g1, g2 = np.array(data['g1']), np.array(data['g2'])
            h_g1, h_g2 = len(g1) > 0, len(g2) > 0
            
            # Linking element_width and bar_gap to coordinate mapping
            pos1, pos2 = (-(bar_width/2 + bar_gap/2), +(bar_width/2 + bar_gap/2)) if h_g1 and h_g2 else (0, 0)

            def plot_core(ax, pos, vals, color):
                if len(vals) == 0: return
                
                mean_v = np.mean(vals)
                std_v = np.std(vals, ddof=1) if len(vals) > 1 else 0
                
                # Statistics Branching
                if "Bar" in graph_type and "SEM" in error_type:
                    err_v = std_v / np.sqrt(len(vals))
                else:
                    err_v = std_v

                # Geometry Branching
                if "Bar" in graph_type:
                    ax.bar(pos, mean_v, width=bar_width, color=color, edgecolor='black', linewidth=1.2, zorder=1)
                    ax.errorbar(pos, mean_v, yerr=err_v, fmt='none', color='black', capsize=cap_size, elinewidth=1.5, zorder=2)
                elif "Box" in graph_type:
                    ax.boxplot(vals, positions=[pos], widths=bar_width, patch_artist=True, showfliers=False,
                               boxprops=dict(facecolor=color, color='black', linewidth=1.2),
                               medianprops=dict(color='black', linewidth=1.5),
                               whiskerprops=dict(linewidth=1.2), capprops=dict(linewidth=1.2), zorder=1)
                elif "Violin" in graph_type:
                    v_parts = ax.violinplot(vals, positions=[pos], widths=bar_width, showextrema=False)
                    for pc in v_parts['bodies']:
                        pc.set_facecolor(color); pc.set_edgecolor('black'); pc.set_alpha(0.7); pc.set_zorder(1)

                # Strip Plot Module (Universal Overlay)
                if show_points:
                    noise = np.random.normal(0, jitter_strength * bar_width, len(vals))
                    edge_c = 'gray' if dot_size > 15 else 'none'
                    ax.scatter(pos + noise, vals, color='white', edgecolor=edge_c, s=dot_size, alpha=dot_alpha, zorder=3)

            # Execution
            plot_core(ax, pos1, g1, color1)
            plot_core(ax, pos2, g2, color2)

            # Axis & Tick Integrity
            tks, lbs = [], []
            if h_g1: tks.append(pos1); lbs.append(group1_name)
            if h_g2: tks.append(pos2); lbs.append(group2_name)
            ax.set_xticks(tks)
            ax.set_xticklabels(lbs, fontsize=11)
            ax.set_title(data['name'], fontsize=12, pad=12)
            ax.set_ylim(0, y_max_limit)

            # Significance Bracket Module
            if data['sig']:
                c_max = max([max(g1) if h_g1 else 0, max(g2) if h_g2 else 0])
                y_l = c_max * 1.15
                h_b = c_max * 0.03
                lx_s, lx_e = (pos1, pos2) if h_g1 and h_g2 else (pos1-0.2, pos1+0.2)
                ax.plot([lx_s, lx_s, lx_e, lx_e], [y_l-h_b, y_l, y_l, y_l-h_b], lw=1.5, c='k')
                ax.text((lx_s+lx_e)/2, y_l + c_max*0.02, data['sig'], ha='center', va='bottom', fontsize=14)

            # Spines & Border Styling (The "Perfect" Look)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_linewidth(1.2)
            if i == 0:
                ax.set_ylabel(y_axis_label, fontsize=14)
                ax.spines['left'].set_linewidth(1.2)
            else:
                ax.spines['left'].set_visible(False)
                ax.tick_params(axis='y', left=False)

            # Dynamic Camera Limit to prevent element clipping
            mg = 0.8
            mx_c = (bar_width/2 + bar_gap/2) + bar_width/2
            ax.set_xlim(-(mx_c + mg), (mx_c + mg))

        # Legend Module
        if show_legend:
            lh = []
            if has_any_g1: lh.append(mpatches.Patch(facecolor=color1, edgecolor='black', label=group1_name))
            if has_any_g2: lh.append(mpatches.Patch(facecolor=color2, edgecolor='black', label=group2_name))
            if lh: fig.legend(handles=lh, loc='center left', bbox_to_anchor=(0.93, 0.5), frameon=False, fontsize=12)

        st.pyplot(fig)

        # Professional Export with JST Timestamp
        img_buf = io.BytesIO()
        fig.savefig(img_buf, format='png', bbox_inches='tight', dpi=300)
        now_jst = datetime.datetime.now() + datetime.timedelta(hours=9)
        st.download_button("📥 Download Publication Quality Image", data=img_buf, 
                           file_name=f"sci_graph_{now_jst.strftime('%Y%m%d_%H%M%S')}.png", mime="image/png")

    except Exception as e:
        st.error(f"Visualization Error: {e}")
else:
    st.info("Awaiting input: Please upload a CSV or enter data manually to generate the figure.")
