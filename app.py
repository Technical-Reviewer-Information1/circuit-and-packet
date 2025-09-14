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
    page_title="回線交換方式・パケット交換方式",
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
    padding: 15px;
    border-radius: 8px;
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
    margin: 10px 0;
}
.error-box {
    padding: 15px;
    border-radius: 8px;
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
    margin: 10px 0;
}
.info-box {
    padding: 15px;
    border-radius: 8px;
    background-color: #d1ecf1;
    border: 1px solid #bee5eb;
    color: #0c5460;
    margin: 10px 0;
}
.simulation-explanation {
    padding: 15px;
    border-radius: 8px;
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
    margin: 15px 0;
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
    
    # 拠点（旧ノード）位置
    locations = {
        '東京': (0, 1),
        '大阪': (2, 2),
        '福岡': (4, 1),
        '名古屋': (1, 0),
        '札幌': (3, 0)
    }
    
    # 接続線
    connections = [
        ('東京', '大阪'), ('東京', '名古屋'),
        ('大阪', '福岡'), ('大阪', '札幌'),
        ('福岡', '札幌'), ('名古屋', '札幌')
    ]
    
    # 接続線を描画
    for connection in connections:
        x0, y0 = locations[connection[0]]
        x1, y1 = locations[connection[1]]
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode='lines',
            line=dict(color='gray', width=3),
            showlegend=False,
            hoverinfo='none'
        ))
    
    # 拠点を描画
    for location, (x, y) in locations.items():
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(size=40, color='lightblue', line=dict(width=3, color='darkblue')),
            text=location,
            textposition='middle center',
            textfont=dict(size=12, color='darkblue'),
            showlegend=False,
            name=f'{location}の通信拠点'
        ))
    
    fig.update_layout(
        title="日本全国の通信ネットワーク",
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        height=350,
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig

def simulate_circuit_switching(source, destination, message_size, network_load):
    """回線交換方式のシミュレーション"""
    # 回線確保の待ち時間（ネットワーク負荷に依存）
    connection_time = random.uniform(1, 3) * (network_load / 50)
    
    # 専用回線確保の成否判定
    success_rate = max(0.3, 1 - (network_load - 50) / 100)
    connection_success = random.random() < success_rate
    
    if not connection_success:
        return {
            'success': False,
            'total_time': connection_time,
            'message': '回線が混雑していて専用回線を確保できませんでした',
            'steps': [
                '📞 専用回線の確保を要求',
                '❌ ネットワークが混雑しており、空いている回線がありません',
                '🔄 しばらく待ってから再度お試しください'
            ]
        }
    
    # 専用回線でのデータ転送
    transfer_time = message_size / 10  # 10Mbpsの専用回線と仮定
    total_time = connection_time + transfer_time
    
    return {
        'success': True,
        'total_time': total_time,
        'connection_time': connection_time,
        'transfer_time': transfer_time,
        'message': f'専用回線で安定した高速通信が完了しました！（合計{total_time:.2f}秒）',
        'steps': [
            '📞 専用回線の確保を要求',
            f'🔗 専用回線を確保しました（{connection_time:.1f}秒かかりました）',
            f'📡 専用回線でデータを一気に送信（{transfer_time:.1f}秒）',
            '✅ 通信完了！回線を開放しました'
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
        # 経由する中継地点の数
        relay_points = random.randint(2, 5)
        
        # 各中継地点での処理時間（ネットワーク負荷に依存）
        relay_delay = 0.05 * (1 + network_load / 100)
        
        # パケット転送時間
        transfer_time = packet_size / 5  # 5Mbpsの共有回線と仮定
        
        # パケットが途中で失われる可能性
        loss_rate = min(0.1, network_load / 1000)
        packet_lost = random.random() < loss_rate
        
        if packet_lost:
            failed_packets += 1
            # 再送信のため時間が2倍かかる
            packet_time = (relay_delay * relay_points + transfer_time) * 2
        else:
            packet_time = relay_delay * relay_points + transfer_time
        
        packet_times.append(packet_time)
    
    total_time = max(packet_times)  # 最後のパケットが到着するまでの時間
    
    return {
        'success': True,
        'total_time': total_time,
        'num_packets': num_packets,
        'failed_packets': failed_packets,
        'packet_loss_rate': failed_packets / num_packets * 100,
        'message': f'データを分割して送信完了！（合計{total_time:.2f}秒、{failed_packets}個のパケットを再送信）',
        'steps': [
            f'📦 {message_size}MBのデータを{num_packets}個の小さなパケットに分割',
            f'🚀 各パケットが別々のルートで目的地へ出発',
            f'🔄 混雑により{failed_packets}個のパケットが途中で失われて再送信',
            f'🧩 目的地で全パケットを組み立てて元のデータに復元'
        ]
    }

def create_comparison_chart(circuit_results, packet_results):
    """比較チャートを作成"""
    if not circuit_results or not packet_results:
        return None
    
    categories = ['転送時間', '安定性', '効率性']
    
    # スコア計算（0-100）
    circuit_scores = [
        max(0, 100 - circuit_results[-1]['total_time'] * 10),  # 転送時間
        100 if circuit_results[-1]['success'] else 0,  # 安定性
        30  # 効率性（専用回線なので低い）
    ]
    
    packet_scores = [
        max(0, 100 - packet_results[-1]['total_time'] * 10),  # 転送時間
        max(0, 100 - packet_results[-1]['packet_loss_rate'] * 5),  # 安定性
        80  # 効率性（共有なので高い）
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=circuit_scores,
        theta=categories,
        fill='toself',
        name='📞 回線交換方式',
        line_color='red'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=packet_scores,
        theta=categories,
        fill='toself',
        name='📦 パケット交換方式',
        line_color='blue'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=True,
        title="どちらの方式が優秀？性能比較"
    )
    
    return fig

# メインアプリケーション
st.markdown('<p class="big-font">回線交換方式・パケット交換方式（pp.104-105）</p>', unsafe_allow_html=True)
st.caption("Created by Dit-Lab.(Daiki Ito)")
st.caption("Supported by Tomoaki ATSUMI")
st.markdown("**電話のような通信**と**インターネットのような通信**の違いを体験してみよう！")

# タブ設定
tab1, tab2, tab3 = st.tabs(["📚 基礎知識", "🧪 通信実験", "📊 結果比較"])

with tab1:
    st.markdown("### 🔄 2つの通信方式の違いを知ろう")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📞 回線交換方式（電話のような通信）")
        st.markdown("""
        <div class="info-box">
        <strong>どんな方式？</strong><br>
        • 通話を始める前に、あなた専用の「通信の道」を確保<br>
        • 一度つながれば、その道はあなただけのもの<br>
        • 通話中は他の人はその道を使えない<br>
        • 昔の電話や、今でもビデオ通話で使われている
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**良いところ：**")
        st.write("✅ 安定してクリアな通信ができる")
        st.write("✅ 遅れ（遅延）がほとんどない")
        st.write("✅ データが順番通りに届く")
        
        st.markdown("**困るところ：**")
        st.write("❌ 使わない時間も道を占領してしまう")
        st.write("❌ 混雑していると接続できない")
        st.write("❌ コストが高い")
    
    with col2:
        st.markdown("#### 📦 パケット交換方式（インターネットの通信）")
        st.markdown("""
        <div class="info-box">
        <strong>どんな方式？</strong><br>
        • 送りたいデータを小さな「荷物（パケット）」に分割<br>
        • 各荷物が別々のルートで目的地へ向かう<br>
        • みんなで道を譲り合いながら使う<br>
        • インターネット、メール、SNSの基本方式
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**良いところ：**")
        st.write("✅ みんなで効率よく道を共有できる")
        st.write("✅ 道が壊れても別ルートで迂回できる")
        st.write("✅ コストが安い")
        st.write("✅ たくさんの人が同時に使える")
        
        st.markdown("**困るところ：**")
        st.write("❌ 荷物が途中で失われることがある")
        st.write("❌ 到着時間にバラつきがある")
        st.write("❌ 混雑すると速度が遅くなる")

    # ネットワーク構成図
    st.markdown("### 🌐 日本の通信ネットワーク")
    st.markdown("実際の通信は、全国の拠点を結んだネットワークを通じて行われます")
    fig_network = create_network_topology()
    st.plotly_chart(fig_network, use_container_width=True)

with tab2:
    st.markdown("### 🧪 通信実験をしてみよう")
    
    # 実験の説明
    st.markdown("""
    <div class="simulation-explanation">
    <strong>🎯 実験の目的</strong><br>
    異なる条件で2つの通信方式を試して、どちらが速くて確実かを比べてみましょう！<br>
    ネットワークの混雑具合やデータの大きさを変えると、結果がどう変わるかな？
    </div>
    """, unsafe_allow_html=True)
    
    # 実験設定
    st.markdown("#### ⚙️ 実験条件を設定")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🌐 ネットワークの混雑度**")
        network_load = st.slider(
            "混雑度を選択", 
            0, 100, 50,
            help="0%=空いている、100%=大混雑"
        )
        if network_load < 30:
            st.success("🟢 空いている：快適に使えそう！")
        elif network_load < 70:
            st.warning("🟡 普通：まあまあ使える")
        else:
            st.error("🔴 混雑：重くなりそう...")
    
    with col2:
        st.markdown("**📁 送信するデータの大きさ**")
        message_size = st.selectbox(
            "データサイズを選択",
            [1, 5, 10, 50, 100],
            index=2,
            format_func=lambda x: f"{x} MB",
            help="写真1枚≈5MB、動画≈50MB"
        )
        
        # データサイズの説明
        if message_size == 1:
            st.info("📄 テキストファイル程度")
        elif message_size == 5:
            st.info("📸 写真1枚程度")
        elif message_size == 10:
            st.info("🎵 音楽ファイル程度")
        elif message_size == 50:
            st.info("🎬 短い動画程度")
        else:
            st.info("🎥 長い動画程度")
    
    with col3:
        st.markdown("**📍 通信ルート**")
        source_city = st.selectbox("送信元の都市", ["東京", "大阪", "福岡", "名古屋", "札幌"], index=0)
        destination_city = st.selectbox("宛先の都市", ["東京", "大阪", "福岡", "名古屋", "札幌"], index=2)
        
        if source_city == destination_city:
            st.warning("⚠️ 同じ都市は選べません")
    
    if source_city != destination_city:
        st.markdown("#### 🚀 実験開始！")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📞 回線交換方式で送信")
            st.markdown("電話のように専用の回線を確保してから通信します")
            
            if st.button("📞 回線交換で送信", use_container_width=True, type="primary"):
                with st.spinner("専用回線を確保しています..."):
                    time.sleep(1)  # リアル感のための待機
                    result = simulate_circuit_switching(source_city, destination_city, message_size, network_load)
                    st.session_state.circuit_messages.append(result)
                    
                if result['success']:
                    st.markdown(f"""
                    <div class="success-box">
                    <strong>✅ 成功！</strong><br>
                    {result['message']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="error-box">
                    <strong>❌ 失敗...</strong><br>
                    {result['message']}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("**📋 何が起こったか：**")
                for i, step in enumerate(result['steps'], 1):
                    st.write(f"{i}. {step}")
        
        with col2:
            st.markdown("##### 📦 パケット交換方式で送信")
            st.markdown("インターネットのようにデータを分割して通信します")
            
            if st.button("📦 パケット交換で送信", use_container_width=True, type="secondary"):
                with st.spinner("パケットを送信しています..."):
                    time.sleep(1)  # リアル感のための待機
                    result = simulate_packet_switching(source_city, destination_city, message_size, network_load)
                    st.session_state.packet_messages.append(result)
                
                st.markdown(f"""
                <div class="success-box">
                <strong>✅ 送信完了！</strong><br>
                {result['message']}
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("**📋 何が起こったか：**")
                for i, step in enumerate(result['steps'], 1):
                    st.write(f"{i}. {step}")
    
    # 現在の状況表示
    st.markdown("---")
    st.markdown("#### 📊 現在のネットワーク状況")
    
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
        st.metric("回線交換成功見込み", f"{expected_success:.0f}%")

with tab3:
    st.markdown("### 📊 実験結果を比較してみよう")
    
    if st.session_state.circuit_messages or st.session_state.packet_messages:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📞 回線交換方式の結果")
            if st.session_state.circuit_messages:
                st.markdown("**最近の実験結果：**")
                for i, msg in enumerate(st.session_state.circuit_messages[-5:], 1):
                    if msg['success']:
                        st.write(f"✅ 実験{i}: {msg['total_time']:.2f}秒で成功")
                    else:
                        st.write(f"❌ 実験{i}: 接続に失敗")
            else:
                st.info("まだ実験していません")
        
        with col2:
            st.markdown("#### 📦 パケット交換方式の結果")
            if st.session_state.packet_messages:
                st.markdown("**最近の実験結果：**")
                for i, msg in enumerate(st.session_state.packet_messages[-5:], 1):
                    st.write(f"✅ 実験{i}: {msg['total_time']:.2f}秒、{msg['failed_packets']}個再送")
            else:
                st.info("まだ実験していません")
        
        # 性能比較チャート
        if st.session_state.circuit_messages and st.session_state.packet_messages:
            st.markdown("### 📈 どちらが優秀？総合比較")
            comparison_chart = create_comparison_chart(
                st.session_state.circuit_messages,
                st.session_state.packet_messages
            )
            if comparison_chart:
                st.plotly_chart(comparison_chart, use_container_width=True)
                
                st.markdown("""
                <div class="info-box">
                <strong>📖 グラフの見方</strong><br>
                • <strong>転送時間</strong>: 短いほど良い（外側に近いほど速い）<br>
                • <strong>安定性</strong>: 高いほど良い（外側に近いほど安定）<br>
                • <strong>効率性</strong>: 高いほど良い（外側に近いほど効率的）
                </div>
                """, unsafe_allow_html=True)
        
        # 統計情報
        if len(st.session_state.circuit_messages) > 0 and len(st.session_state.packet_messages) > 0:
            st.markdown("### 📈 実験結果の統計")
            
            # 成功率計算
            circuit_success_rate = sum(1 for msg in st.session_state.circuit_messages if msg['success']) / len(st.session_state.circuit_messages) * 100
            packet_success_rate = 100  # パケット交換は基本的に成功
            
            # 平均時間計算
            successful_circuit = [msg for msg in st.session_state.circuit_messages if msg['success']]
            avg_circuit_time = sum(msg['total_time'] for msg in successful_circuit) / len(successful_circuit) if successful_circuit else 0
            avg_packet_time = sum(msg['total_time'] for msg in st.session_state.packet_messages) / len(st.session_state.packet_messages)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📞 回線交換成功率", f"{circuit_success_rate:.1f}%")
            with col2:
                st.metric("📦 パケット交換成功率", f"{packet_success_rate:.1f}%")
            with col3:
                st.metric("📞 平均通信時間", f"{avg_circuit_time:.2f}秒")
            with col4:
                st.metric("📦 平均通信時間", f"{avg_packet_time:.2f}秒")
        
        # 結果クリアボタン
        st.markdown("---")
        if st.button("🗑️ 実験結果をリセット", type="secondary"):
            st.session_state.circuit_messages = []
            st.session_state.packet_messages = []
            st.success("実験結果をリセットしました！")
            time.sleep(1)
            st.rerun()
    
    else:
        st.markdown("""
        <div class="info-box">
        <strong>🔬 実験結果はここに表示されます</strong><br>
        「通信実験」タブで実際に通信を試してから、ここで結果を比較してみましょう！
        </div>
        """, unsafe_allow_html=True)

# フッター
st.markdown("---")
st.markdown("### 💡 まとめ：どちらの方式が良い？")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **📞 回線交換方式が得意なこと**
    - 🎥 ビデオ通話（リアルタイム性が重要）
    - 📞 音声通話（途切れると困る）
    - 🏥 緊急通信（確実性が必要）
    """)

with col2:
    st.markdown("""
    **📦 パケット交換方式が得意なこと**
    - 🌐 ウェブサイト閲覧
    - 📧 メール送信
    - 📱 SNS、チャット
    - 🎮 オンラインゲーム
    """)

st.info("""
🎯 **結論**: どちらも大切な技術で、用途によって使い分けられています！
インターネットは主にパケット交換方式ですが、ビデオ通話などでは回線交換的な技術も使われています。
""")
