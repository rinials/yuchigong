#!/usr/bin/env python3
"""
Generate a PPT illustration for GNN + RL based network resource allocation.
Shows: Multi-layer heterogeneous graph -> GNN -> RL Agent -> Routing Strategy

Usage:
    python generate_diagram.py [output_path]

If output_path is omitted the image is saved next to this script as
gnn_rl_network_allocation.png.
"""

import os
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import FancyBboxPatch, Circle
import numpy as np

# ── Locate a CJK-capable font (cross-platform) ───────────────────────────────
_CJK_CANDIDATES = [
    # Linux (Noto CJK)
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
    # macOS
    '/System/Library/Fonts/PingFang.ttc',
    '/Library/Fonts/Arial Unicode.ttf',
    # Windows
    r'C:\Windows\Fonts\msyh.ttc',
]
_CJK_BOLD_CANDIDATES = [
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
    '/System/Library/Fonts/PingFang.ttc',
    r'C:\Windows\Fonts\msyhbd.ttc',
]

def _first_existing(paths):
    return next((p for p in paths if os.path.isfile(p)), None)

_cjk_reg_path  = _first_existing(_CJK_CANDIDATES)
_cjk_bold_path = _first_existing(_CJK_BOLD_CANDIDATES)

_fp_reg = _fp_bold = None
if _cjk_reg_path:
    try:
        fm.fontManager.addfont(_cjk_reg_path)
        _fp_reg = fm.FontProperties(fname=_cjk_reg_path)
    except Exception:
        pass
if _cjk_bold_path:
    try:
        fm.fontManager.addfont(_cjk_bold_path)
        _fp_bold = fm.FontProperties(fname=_cjk_bold_path)
    except Exception:
        pass

if _fp_reg:
    matplotlib.rcParams['font.family'] = _fp_reg.get_name()
    print(f"Using CJK font: {_fp_reg.get_name()}")
else:
    print("CJK font not found; Chinese characters may not render correctly.")
    _fp_reg  = fm.FontProperties(family='sans-serif')
    _fp_bold = fm.FontProperties(family='sans-serif', weight='bold')

fig = plt.figure(figsize=(22, 13), facecolor='#0d1117')
ax  = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 22)
ax.set_ylim(0, 13)
ax.axis('off')
ax.set_facecolor('#0d1117')

# ── helpers ──────────────────────────────────────────────────────────────────
def rbox(x, y, w, h, fc, alpha=0.88, radius=0.3, ec='white', lw=1.4, zorder=3):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0,rounding_size={radius}",
                       linewidth=lw, edgecolor=ec,
                       facecolor=fc, alpha=alpha, zorder=zorder)
    ax.add_patch(p)

def arr(x0, y0, x1, y1, color='white', lw=2.2, rad=0.0, zorder=5):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                connectionstyle=f'arc3,rad={rad}'), zorder=zorder)

def txt(x, y, s, fs=11, color='white', bold=False,
        ha='center', va='center', zorder=6, fp=None):
    if fp is None:
        fp = _fp_bold if bold else _fp_reg
    ax.text(x, y, s, fontsize=fs, color=color, ha=ha, va=va,
            fontproperties=fp, zorder=zorder)

# ══════════════════════════════════════════════════════════════════════════════
# 0. Title bar
# ══════════════════════════════════════════════════════════════════════════════
rbox(0.3, 12.3, 21.4, 0.65, '#1b2a4a', alpha=1.0, radius=0.25, ec='#3d5a80', lw=1.5)
txt(11.0, 12.63,
    '基于图神经网络与强化学习的复杂网络资源分配框架',
    fs=15, bold=True, color='#e0f0ff')
txt(11.0, 12.38,
    'GNN + Reinforcement Learning Framework for Complex Network Resource Allocation',
    fs=9.5, color='#8ab4cc')
ax.plot([0.3, 21.7], [12.28, 12.28], color='#3d5a80', lw=1.2, alpha=0.7)

# ══════════════════════════════════════════════════════════════════════════════
# 1. Multi-layer Heterogeneous Graph  (x: 0.4 – 6.0)
# ══════════════════════════════════════════════════════════════════════════════
rbox(0.4, 1.0, 5.5, 11.0, '#0e1e38', alpha=1.0, radius=0.4, ec='#3d6fa8', lw=1.8)
txt(3.15, 11.7, '多层异构网络图', fs=13, bold=True, color='#7ec8e3')
txt(3.15, 11.35, 'Multi-layer Heterogeneous Graph', fs=8.5, color='#8ab4cc')

layer_cfg = [
    ('#e74c3c', '#ff8a80', '物理层  Physical Layer',   9.8),
    ('#2ecc71', '#69f0ae', '链路层  Link Layer',        7.4),
    ('#3498db', '#82b1ff', '网络层  Network Layer',     5.0),
    ('#f39c12', '#ffd180', '应用层  Application Layer', 2.6),
]
node_xy = [
    [(1.1, 0.8), (2.5, 1.1), (3.9, 0.7), (2.0, 0.0), (3.3, 0.1)],
    [(1.1, 0.9), (2.5, 1.0), (3.9, 0.6), (3.0, 0.0)],
    [(1.2, 0.7), (2.5, 0.9), (3.8, 0.7), (2.2, 0.1)],
    [(1.4, 0.6), (2.7, 0.8), (3.6, 0.5)],
]
edge_idx = [
    [(0,1),(1,2),(0,3),(1,3),(2,4),(3,4),(1,4)],
    [(0,1),(1,2),(1,3),(2,3)],
    [(0,1),(1,2),(0,3),(1,3)],
    [(0,1),(1,2)],
]
node_shapes = [['■','▲','■','▲','■'], ['◆','●','◆','●'],
               ['★','◉','★','◉'],    ['●','●','●']]

for li, (ec, nc, lname, base_y) in enumerate(layer_cfg):
    coords = [(bx + 0.5, by + base_y) for bx, by in node_xy[li]]
    for a, b in edge_idx[li]:
        ax.plot([coords[a][0], coords[b][0]],
                [coords[a][1], coords[b][1]],
                color=ec, lw=1.2, alpha=0.55, zorder=3)
    for idx, (nx_, ny_) in enumerate(coords):
        ax.add_patch(Circle((nx_, ny_), 0.20, color=nc, zorder=5))
        ax.text(nx_, ny_, node_shapes[li][idx], fontsize=6.5,
                ha='center', va='center', color='#0d1117', zorder=6)
    # inter-layer dashed lines
    if li < len(layer_cfg) - 1:
        next_coords = [(bx + 0.5, by + layer_cfg[li+1][3]) for bx, by in node_xy[li+1]]
        for i in range(min(2, len(coords), len(next_coords))):
            ax.plot([coords[i][0], next_coords[i][0]],
                    [coords[i][1], next_coords[i][1]],
                    color='#607d8b', lw=0.9, linestyle='--', alpha=0.45, zorder=2)
    txt(0.65, base_y + 1.55, lname, fs=8.5, color=nc, bold=True, ha='left')

# legend
legend_items = [('■ 路由器 Router', '#ff8a80'), ('◆ 交换机 Switch', '#69f0ae'),
                ('★ 服务器 Server', '#82b1ff'), ('● 用户   User',   '#ffd180')]
for i, (lt, lc) in enumerate(legend_items):
    txt(0.75, 1.85 - i*0.28, lt, fs=7.5, color=lc, ha='left')

# ══════════════════════════════════════════════════════════════════════════════
# 2. GNN Encoder  (x: 6.7 – 10.9)
# ══════════════════════════════════════════════════════════════════════════════
rbox(6.7, 1.0, 4.2, 11.0, '#0e2a1e', alpha=1.0, radius=0.4, ec='#2e7d50', lw=1.8)
txt(8.8, 11.7, 'GNN 编码器', fs=13, bold=True, color='#69f0ae')
txt(8.8, 11.35, 'Graph Neural Network Encoder', fs=8.5, color='#8ab4cc')

gnn_blocks = [
    ('#1b5e20', '#a5d6a7', '异构卷积层\nHeteroConv Layer',        10.1),
    ('#00695c', '#80cbc4', '图注意力机制\nGraph Attention (GAT)',  8.5),
    ('#01579b', '#81d4fa', '消息传递网络\nMessage Passing Network', 6.9),
    ('#4a148c', '#ce93d8', '节点嵌入表示\nNode Embedding',          5.3),
    ('#bf360c', '#ffcc80', '全局图池化\nGlobal Graph Pooling',       3.7),
    ('#37474f', '#b0bec5', '状态向量输出\nState Vector Output',       2.1),
]
for i, (fc, nc, label_, cy) in enumerate(gnn_blocks):
    rbox(6.95, cy, 3.7, 1.1, fc, alpha=0.85, radius=0.22)
    txt(8.8, cy + 0.55, label_, fs=9, color=nc, bold=(i == 0))
    if i < len(gnn_blocks) - 1:
        arr(8.8, cy, 8.8, gnn_blocks[i+1][3] + 1.1, color='#a5d6a7', lw=1.6)

# ══════════════════════════════════════════════════════════════════════════════
# 3. RL Agent  (x: 11.6 – 16.3)
# ══════════════════════════════════════════════════════════════════════════════
rbox(11.6, 1.0, 4.6, 11.0, '#1a0e38', alpha=1.0, radius=0.4, ec='#5e35b1', lw=1.8)
txt(13.9, 11.7, '强化学习智能体', fs=13, bold=True, color='#ce93d8')
txt(13.9, 11.35, 'Reinforcement Learning Agent', fs=8.5, color='#8ab4cc')

rl_blocks = [
    ('#4a148c', '#e1bee7', '状态空间  State Space\n异构图嵌入 Graph Embedding',      10.0),
    ('#1a237e', '#c5cae9', 'Actor 策略网络  Policy Network\nPPO / Actor-Critic',     8.4),
    ('#006064', '#b2ebf2', 'Critic 价值网络  Value Network\n状态价值估计 V(s)',         6.8),
    ('#e65100', '#ffe0b2', '奖励函数  Reward Function\nR = 资源利用率 Utilization',    5.2),
    ('#1b5e20', '#dcedc8', '动作选择  Action Selection\nε-greedy / 软化策略',          3.6),
    ('#37474f', '#cfd8dc', '经验回放  Experience Replay\n路由决策记忆库 Buffer',         2.0),
]
for i, (fc, nc, label_, cy) in enumerate(rl_blocks):
    rbox(11.85, cy, 4.1, 1.1, fc, alpha=0.85, radius=0.22)
    txt(13.9, cy + 0.55, label_, fs=8.8, color=nc, bold=(i == 0))
    if i < len(rl_blocks) - 1:
        arr(13.9, cy, 13.9, rl_blocks[i+1][3] + 1.1, color='#bb86fc', lw=1.6)

# RL feedback loop arc
theta = np.linspace(-np.pi*0.6, np.pi*0.6, 200)
lx, cx_rl, cy_rl = 16.1, 16.3, 6.5
ax.plot(lx + 0.35*np.cos(theta), cy_rl + 4.2*np.sin(theta),
        color='#bb86fc', lw=1.3, linestyle=':', alpha=0.6, zorder=4)
ax.annotate('', xy=(lx, 2.6), xytext=(lx, 2.4),
             arrowprops=dict(arrowstyle='->', color='#bb86fc', lw=1.5), zorder=5)
txt(16.6, 6.5, 'RL\nLoop', fs=8, color='#bb86fc')

# ══════════════════════════════════════════════════════════════════════════════
# 4. Action Space  (x: 17.0 – 21.6)
# ══════════════════════════════════════════════════════════════════════════════
rbox(17.0, 7.2, 4.6, 4.8, '#0e1e38', alpha=1.0, radius=0.4, ec='#1565c0', lw=1.8)
txt(19.3, 11.7, '动作空间', fs=13, bold=True, color='#82b1ff')
txt(19.3, 11.35, 'Action Space: Routing Strategies', fs=8.5, color='#8ab4cc')

strategies = [
    ('#0d47a1', '#90caf9', '① 最短路径  Shortest Path Routing'),
    ('#004d40', '#80cbc4', '② 负载均衡  Load-balanced Routing'),
    ('#4a148c', '#ce93d8', '③ QoS 感知  QoS-aware Routing'),
    ('#bf360c', '#ffab91', '④ 多路径    Multi-path Routing'),
]
for i, (fc, nc, stxt) in enumerate(strategies):
    rbox(17.2, 10.8 - i*0.95, 4.2, 0.82, fc, alpha=0.85, radius=0.2)
    txt(19.3, 11.21 - i*0.95, stxt, fs=9, color=nc)

# ══════════════════════════════════════════════════════════════════════════════
# 5. Output / Result  (x: 17.0 – 21.6)
# ══════════════════════════════════════════════════════════════════════════════
rbox(17.0, 1.0, 4.6, 5.9, '#0e2214', alpha=1.0, radius=0.4, ec='#2e7d32', lw=1.8)
txt(19.3, 6.6, '最优路由策略输出', fs=13, bold=True, color='#c8e6c9')
txt(19.3, 6.25, 'Optimal Routing Policy Output', fs=8.5, color='#8ab4cc')

# Small network diagram showing chosen path
out_n = [(17.7,5.7),(18.8,5.9),(20.3,5.8),(19.5,5.0),(20.6,4.6),
         (17.8,4.3),(19.0,4.1),(20.7,3.8)]
gray_edges = [(0,1),(1,2),(0,5),(3,4),(4,7),(2,3),(6,7)]
green_edges = [(1,3),(3,6),(6,7)]

for a, b in gray_edges:
    ax.plot([out_n[a][0], out_n[b][0]],
            [out_n[a][1], out_n[b][1]], color='#37474f', lw=1.4, zorder=3)
for a, b in green_edges:
    ax.annotate('', xy=(out_n[b][0], out_n[b][1]),
                xytext=(out_n[a][0], out_n[a][1]),
                arrowprops=dict(arrowstyle='->', color='#69f0ae', lw=2.6,
                                connectionstyle='arc3,rad=0.18'), zorder=5)
for i, (nx_, ny_) in enumerate(out_n):
    c = '#69f0ae' if i in [1, 3, 6, 7] else '#546e7a'
    ax.add_patch(Circle((nx_, ny_), 0.22, color=c, zorder=4))
    ax.text(nx_, ny_, str(i+1), fontsize=7, ha='center', va='center',
            color='#0d1117', fontweight='bold', zorder=6)

ax.text(18.5, 5.25, '最优路径', fontsize=7.5, color='#69f0ae', zorder=6,
        fontproperties=_fp_reg)

# Metrics
metrics = [
    ('资源利用率 Utilization', '↑ 94.7%',  '#69f0ae'),
    ('时延  Latency',           '↓ 18 ms',  '#82b1ff'),
    ('吞吐量 Throughput',       '↑ 10 Gbps','#ffcc80'),
]
for i, (mn, mv, mc) in enumerate(metrics):
    rbox(17.2, 3.0 - i*0.77, 4.2, 0.65, '#1a2a1a', alpha=0.8, radius=0.18, ec=mc, lw=1)
    txt(18.25, 3.33 - i*0.77, mn, fs=8.5, color=mc, ha='left')
    txt(21.0,  3.33 - i*0.77, mv, fs=9.5, color=mc, bold=True)

# ══════════════════════════════════════════════════════════════════════════════
# 6. Flow arrows between sections
# ══════════════════════════════════════════════════════════════════════════════
# Graph -> GNN
arr(5.95, 6.5, 6.7, 6.5, color='#7ec8e3', lw=2.5)
txt(6.32, 6.82, '状态输入\nState Input', fs=8, color='#7ec8e3')

# GNN -> RL
arr(10.9, 6.5, 11.6, 6.5, color='#a5d6a7', lw=2.5)
txt(11.25, 6.82, '嵌入向量\nEmbedding', fs=8, color='#a5d6a7')

# RL -> Action Space
arr(16.2, 9.6, 17.0, 9.6, color='#82b1ff', lw=2.5)
txt(16.6, 9.95, '选择动作\nAction', fs=8, color='#82b1ff')

# RL -> Output
arr(16.2, 4.8, 17.0, 4.8, color='#69f0ae', lw=2.5)
txt(16.6, 5.1, '最优策略\nPolicy', fs=8, color='#69f0ae')

# Reward feedback (output -> RL)
ax.annotate('', xy=(13.9, 2.1),
             xytext=(19.3, 2.1),
             arrowprops=dict(arrowstyle='->', color='#ffcc80', lw=1.8,
                             connectionstyle='arc3,rad=0.0'), zorder=5)
txt(16.6, 1.75, '奖励反馈  Reward Feedback', fs=8.5, color='#ffcc80')

plt.tight_layout(pad=0)
_default_out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'gnn_rl_network_allocation.png')
out_path = sys.argv[1] if len(sys.argv) > 1 else _default_out
fig.savefig(out_path, dpi=150, bbox_inches='tight',
            facecolor='#0d1117', edgecolor='none')
print(f'Saved: {out_path}')
plt.close(fig)
