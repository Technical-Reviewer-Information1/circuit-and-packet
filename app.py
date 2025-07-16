import streamlit as st
import time
import random
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import threading
import queue

# ページ設定
st.set_page_config(
    page_title="ネットワーク通信方式体験アプリ",
    page_icon="📡",
    layout="wide"
)

# CSSスタイル
st.markdown("""
<style>
.big-font {
    font-size:30px !important;
    font-weight: bold;
}
.medium-font {
    font-size:20px !important;
    font-weight: bold;
}
.success-box {
    padding: 10px;
    border-radius: 5px;
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}
.error-box {
    padding: 10px;
    border-radius: 5px;
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
}
.info-box {
    padding: 10px;
    border-radius: 5px;
    background-color: #d1ecf1;
    border: 1px solid #bee5eb;
    color: #0c5460;
}
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'circuit_messages' not in st.session_state:
    st.session_state.circuit_messages = []
if 'packet_messages' not in st.session_state:
    st.session_state.packet_messages = []
if 'network_load' not in st.session_state:
    st.session_state.network_load = 50
if 'simulation_running' not in st.session_state:
    st.session_state.simulation_running = False

def create_network_topology():
    """ネットワーク構成図を作成"""
    fig = go.Figure()
    
    # ノード位置
    nodes = {
        'A': (0, 1),
        'B': (2, 2),
        'C': (4, 1),
        'D': (1, 0),
        'E': (3, 0)
    }
    
    # エッジ（接続）
    edges = [
        ('A', 'B'), ('A', 'D'),
        ('B', 'C'), ('B', 'E'),
        ('C', 'E'), ('D', 'E')
    ]
    
    # エッジを描画
    for edge in edges:
        x0, y0 = nodes[edge[0]]
        x1, y1 = nodes[edge[1]]
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode='lines',
            line=dict(color='gray', width=2),
            showlegend=False,
            hoverinfo='none'
        ))
    
    # ノードを描画
    for node, (x, y) in nodes.items():
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(size=30, color='lightblue', line=dict(width=2, color='darkblue')),
            text=node,
            textposition='middle center',
            showlegend=False,
            name=f'ノード {node}'
        ))
    
    fig.update_layout(
        title="ネットワーク構成図",
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        height=300,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    return fig

def simulate_circuit_switching(source, destination, message_size, network_load):
    """回線交換方式のシミュレーション"""
    # 接続確立時間（ネットワーク負荷に依存）
    connection_time = random.uniform(1, 3) * (network_load / 50)
    
    # 帯域幅確保の成否判定
    success_rate = max(0.3, 1 - (network_load - 50) / 100)
    connection_success = random.random() < success_rate
    
    if not connection_success:
        return {
            'success': False,
            'total_time': connection_time,
            'message': '回線が混雑しており、接続できませんでした',
            'steps': ['接続要求', '回線混雑により失敗']
        }
    
    # 専用回線でのデータ転送
    transfer_time = message_size / 10  # 10Mbpsと仮定
    total_time = connection_time + transfer_time
    
    return {
        'success': True,
        'total_time': total_time,
        'connection_time': connection_time,
        'transfer_time': transfer_time,
        'message': f'専用回線で高速転送完了（{total_time:.2f}秒）',
        'steps': [
            '接続要求',
            f'回線確保（{connection_time:.1f}秒）',
            f'専用回線でデータ転送（{transfer_time:.1f}秒）',
            '接続切断'
        ]
    }

def simulate_packet_switching(source, destination, message_size, network_load):
    """パケット交換方式のシミュレーション"""
    # パケットサイズ（KB）
    packet_size = 1.5
    num_packets = max(1, int(message_size / packet_size))
    
    # 各パケットの転送をシミュレート
    packet_times = []
    failed_packets = 0
    
    for i in range(num_packets):
        # ホップ数（経由ルータ数）
        hops = random.randint(2, 5)
        
        # 各ホップでの遅延（ネットワーク負荷に依存）
        hop_delay = 0.05 * (1 + network_load / 100)
        
        # パケット転送時間
        transfer_time = packet_size / 5  # 5Mbpsと仮定（共有帯域）
        
        # パケット損失の可能性
        loss_rate = min(0.1, network_load / 1000)
        packet_lost = random.random() < loss_rate
        
        if packet_lost:
            failed_packets += 1
            # 再送時間
            packet_time = (hop_delay * hops + transfer_time) * 2
        else:
            packet_time = hop_delay * hops + transfer_time
        
        packet_times.append(packet_time)
    
    total_time = max(packet_times)  # 最後のパケットが到着するまでの時間
    
    return {
        'success': True,
        'total_time': total_time,
        'num_packets': num_packets,
        'failed_packets': failed_packets,
        'packet_loss_rate': failed_packets / num_packets * 100,
        'message': f'パケット分割して転送完了（{total_time:.2f}秒、{failed_packets}個再送）',
        'steps': [
            f'データを{num_packets}個のパケットに分割',
            f'各パケットを個別にルーティング',
            f'一部パケットロス発生（{failed_packets}個）',
            '宛先で元のデータに復元'
        ]
    }

def create_comparison_chart(circuit_results, packet_results):
    """比較チャートを作成"""
    if not circuit_results or not packet_results:
        return None
    
    categories = ['転送時間', '信頼性', 'リソース効率']
    
    # スコア計算（0-100）
    circuit_scores = [
        max(0, 100 - circuit_results[-1]['total_time'] * 10),  # 転送時間
        100 if circuit_results[-1]['success'] else 0,  # 信頼性
        30  # リソース効率（専用回線なので低い）
    ]
    
    packet_scores = [
        max(0, 100 - packet_results[-1]['total_time'] * 10),  # 転送時間
        max(0, 100 - packet_results[-1]['packet_loss_rate'] * 5),  # 信頼性
        80  # リソース効率（共有なので高い）
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=circuit_scores,
        theta=categories,
        fill='toself',
        name='回線交換方式',
        line_color='red'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=packet_scores,
        theta=categories,
        fill='toself',
        name='パケット交換方式',
        line_color='blue'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="性能比較"
    )
    
    return fig

# メインアプリケーション
st.markdown('<p class="big-font">📡 ネットワーク通信方式体験アプリ</p>', unsafe_allow_html=True)
st.markdown("**回線交換方式**と**パケット交換方式**の違いを体験してみよう！")

# サイドバー
st.sidebar.markdown("### 🎛️ シミュレーション設定")
network_load = st.sidebar.slider("ネットワーク負荷 (%)", 0, 100, 50)
st.session_state.network_load = network_load

message_size = st.sidebar.selectbox(
    "送信データサイズ",
    [1, 5, 10, 50, 100],
    index=2,
    format_func=lambda x: f"{x} MB"
)

# 理論説明タブ
tab1, tab2, tab3 = st.tabs(["📚 基礎知識", "🧪 シミュレーション", "📊 結果比較"])

with tab1:
    st.markdown("### 🔄 回線交換方式 vs パケット交換方式")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📞 回線交換方式（電話のような方式）")
        st.markdown("""
        <div class="info-box">
        <strong>特徴：</strong><br>
        • 通信前に専用の回線を確保<br>
        • 一度接続すれば安定した通信<br>
        • 使用中は他の人は使えない<br>
        • 電話やビデオ通話に適している
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**メリット：**")
        st.write("✅ 安定した通信品質")
        st.write("✅ 遅延が少ない")
        st.write("✅ データ順序が保証される")
        
        st.markdown("**デメリット：**")
        st.write("❌ 回線が無駄になることがある")
        st.write("❌ 混雑時は接続できない")
        st.write("❌ 費用が高い")
    
    with col2:
        st.markdown("#### 📦 パケット交換方式（インターネットの方式）")
        st.markdown("""
        <div class="info-box">
        <strong>特徴：</strong><br>
        • データを小さなパケットに分割<br>
        • 各パケットが個別に最適ルートを選択<br>
        • 回線を複数の通信で共有<br>
        • インターネット通信の基本方式
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**メリット：**")
        st.write("✅ 回線を効率的に共有")
        st.write("✅ ネットワーク障害に強い")
        st.write("✅ 費用が安い")
        st.write("✅ 多くの人が同時利用可能")
        
        st.markdown("**デメリット：**")
        st.write("❌ パケットロスの可能性")
        st.write("❌ 遅延が変動する")
        st.write("❌ 混雑時は速度低下")

    # ネットワーク構成図
    st.markdown("### 🌐 ネットワーク構成")
    fig_network = create_network_topology()
    st.plotly_chart(fig_network, use_container_width=True)

with tab2:
    st.markdown("### 🧪 通信シミュレーション")
    
    col1, col2 = st.columns(2)
    
    with col1:
        source_node = st.selectbox("送信元ノード", ["A", "B", "C", "D", "E"], index=0)
    
    with col2:
        destination_node = st.selectbox("宛先ノード", ["A", "B", "C", "D", "E"], index=2)
    
    if source_node == destination_node:
        st.warning("送信元と宛先は異なるノードを選択してください")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📞 回線交換方式で送信", use_container_width=True):
                with st.spinner("回線確保中..."):
                    result = simulate_circuit_switching(source_node, destination_node, message_size, network_load)
                    st.session_state.circuit_messages.append(result)
                    
                if result['success']:
                    st.markdown(f"""
                    <div class="success-box">
                    ✅ {result['message']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="error-box">
                    ❌ {result['message']}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("**処理ステップ：**")
                for i, step in enumerate(result['steps'], 1):
                    st.write(f"{i}. {step}")
        
        with col2:
            if st.button("📦 パケット交換方式で送信", use_container_width=True):
                with st.spinner("パケット送信中..."):
                    result = simulate_packet_switching(source_node, destination_node, message_size, network_load)
                    st.session_state.packet_messages.append(result)
                
                st.markdown(f"""
                <div class="success-box">
                ✅ {result['message']}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("**処理ステップ：**")
                for i, step in enumerate(result['steps'], 1):
                    st.write(f"{i}. {step}")
    
    # ネットワーク状況表示
    st.markdown("### 📊 現在のネットワーク状況")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("ネットワーク負荷", f"{network_load}%")
    
    with col2:
        if network_load < 30:
            status = "🟢 快適"
        elif network_load < 70:
            status = "🟡 普通"
        else:
            status = "🔴 混雑"
        st.metric("通信状況", status)
    
    with col3:
        expected_success = max(30, 100 - network_load)
        st.metric("回線交換成功率", f"{expected_success:.0f}%")

with tab3:
    st.markdown("### 📊 シミュレーション結果比較")
    
    if st.session_state.circuit_messages or st.session_state.packet_messages:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📞 回線交換方式の結果")
            if st.session_state.circuit_messages:
                for i, msg in enumerate(st.session_state.circuit_messages[-5:], 1):
                    if msg['success']:
                        st.write(f"{i}. ✅ {msg['total_time']:.2f}秒で完了")
                    else:
                        st.write(f"{i}. ❌ 接続失敗")
            else:
                st.write("まだシミュレーションを実行していません")
        
        with col2:
            st.markdown("#### 📦 パケット交換方式の結果")
            if st.session_state.packet_messages:
                for i, msg in enumerate(st.session_state.packet_messages[-5:], 1):
                    st.write(f"{i}. ✅ {msg['total_time']:.2f}秒、再送{msg['failed_packets']}個")
            else:
                st.write("まだシミュレーションを実行していません")
        
        # 性能比較チャート
        if st.session_state.circuit_messages and st.session_state.packet_messages:
            st.markdown("### 📈 性能比較チャート")
            comparison_chart = create_comparison_chart(
                st.session_state.circuit_messages,
                st.session_state.packet_messages
            )
            if comparison_chart:
                st.plotly_chart(comparison_chart, use_container_width=True)
        
        # 統計情報
        if len(st.session_state.circuit_messages) > 0 and len(st.session_state.packet_messages) > 0:
            st.markdown("### 📋 統計サマリー")
            
            # 成功率計算
            circuit_success_rate = sum(1 for msg in st.session_state.circuit_messages if msg['success']) / len(st.session_state.circuit_messages) * 100
            packet_success_rate = 100  # パケット交換は基本的に成功
            
            # 平均時間計算
            successful_circuit = [msg for msg in st.session_state.circuit_messages if msg['success']]
            avg_circuit_time = sum(msg['total_time'] for msg in successful_circuit) / len(successful_circuit) if successful_circuit else 0
            avg_packet_time = sum(msg['total_time'] for msg in st.session_state.packet_messages) / len(st.session_state.packet_messages)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("回線交換成功率", f"{circuit_success_rate:.1f}%")
            with col2:
                st.metric("パケット交換成功率", f"{packet_success_rate:.1f}%")
            with col3:
                st.metric("回線交換平均時間", f"{avg_circuit_time:.2f}秒")
            with col4:
                st.metric("パケット交換平均時間", f"{avg_packet_time:.2f}秒")
        
        # 結果クリアボタン
        if st.button("🗑️ 結果をクリア"):
            st.session_state.circuit_messages = []
            st.session_state.packet_messages = []
            st.rerun()
    
    else:
        st.info("シミュレーションタブで通信を実行してから結果を確認できます")

# フッター
st.markdown("---")
st.markdown("""
### 💡 学習のポイント

**回線交換方式**は電話のように専用回線を確保するため、安定していますが効率が悪い場合があります。

**パケット交換方式**はデータを小分けにして送るため、効率的ですが混雑時には影響を受けやすくなります。

実際のインターネットはパケット交換方式を使用しており、この柔軟性により世界中の人々が同時にネットワークを利用できています！
""")