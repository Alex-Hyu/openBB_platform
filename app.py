"""
OpenBB Streamlit Dashboard - Streamlit Cloud Compatible Version
解决Streamlit Cloud部署权限问题
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

# ==================== 关键修复：设置OpenBB环境变量 ====================
# 必须在import openbb之前设置
os.environ["OPENBB_HUB_BACKEND"] = "https://payments.openbb.co"
os.environ["HOME"] = "/tmp"  # Streamlit Cloud写入权限

# 页面配置
st.set_page_config(
    page_title="OpenBB 金融数据平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .module-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 初始化OpenBB（带错误处理）====================
@st.cache_resource
def init_openbb():
    """初始化OpenBB，处理Streamlit Cloud的权限问题"""
    try:
        # 尝试设置临时目录
        import tempfile
        temp_dir = tempfile.mkdtemp()
        os.environ["OPENBB_USER_DATA_DIRECTORY"] = temp_dir
        
        from openbb import obb
        return obb, None
    except Exception as e:
        return None, str(e)

# 备用方案：直接使用yfinance
@st.cache_resource
def init_yfinance():
    """备用方案：直接使用yfinance"""
    try:
        import yfinance as yf
        return yf
    except ImportError:
        return None

# 尝试初始化
obb, obb_error = init_openbb()
yf = init_yfinance()

# ==================== 数据获取函数（兼容两种方式）====================
@st.cache_data(ttl=300)
def get_price_data(symbol, days=365):
    """获取价格数据，优先使用OpenBB，失败则用yfinance"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 尝试OpenBB
    if obb is not None:
        try:
            data = obb.equity.price.historical(
                symbol,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                provider="yfinance"
            ).to_df()
            if not data.empty:
                return data, "openbb"
        except:
            pass
    
    # 备用yfinance
    if yf is not None:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            # 统一列名
            data.columns = [c.lower() for c in data.columns]
            return data, "yfinance"
        except:
            pass
    
    return pd.DataFrame(), None

@st.cache_data(ttl=300)
def get_options_chain(symbol):
    """获取期权链"""
    # 尝试OpenBB
    if obb is not None:
        try:
            chains = obb.derivatives.options.chains(symbol, provider="yfinance").to_df()
            if not chains.empty:
                return chains, "openbb"
        except:
            pass
    
    # 备用yfinance
    if yf is not None:
        try:
            ticker = yf.Ticker(symbol)
            expirations = ticker.options
            
            all_chains = []
            for exp in expirations[:5]:  # 只取前5个到期日
                try:
                    opt = ticker.option_chain(exp)
                    calls = opt.calls.copy()
                    calls['option_type'] = 'call'
                    calls['expiration'] = exp
                    puts = opt.puts.copy()
                    puts['option_type'] = 'put'
                    puts['expiration'] = exp
                    all_chains.append(calls)
                    all_chains.append(puts)
                except:
                    continue
            
            if all_chains:
                df = pd.concat(all_chains, ignore_index=True)
                # 统一列名
                col_map = {
                    'strike': 'strike',
                    'lastPrice': 'last_price',
                    'bid': 'bid',
                    'ask': 'ask',
                    'volume': 'volume',
                    'openInterest': 'open_interest',
                    'impliedVolatility': 'implied_volatility'
                }
                df = df.rename(columns=col_map)
                return df, "yfinance"
        except:
            pass
    
    return pd.DataFrame(), None

# ==================== Sidebar ====================
st.sidebar.markdown("## 🏦 OpenBB 数据平台")

# 显示数据源状态
if obb is not None:
    st.sidebar.success("✅ OpenBB 已连接")
elif yf is not None:
    st.sidebar.warning("⚠️ 使用备用数据源 (yfinance)")
else:
    st.sidebar.error("❌ 无可用数据源")

st.sidebar.markdown("---")

# 主模块选择
main_module = st.sidebar.selectbox(
    "📁 选择功能模块",
    [
        "🏠 首页概览",
        "📈 股票 (Equity)",
        "🎯 期权分析 (Options)", 
        "💰 ETF",
        "🔧 技术分析 (Technical)",
        "📐 量化分析 (Quantitative)",
        "💵 外汇 (Currency)",
        "💎 加密货币 (Crypto)",
    ]
)

# ==================== 首页概览 ====================
if main_module == "🏠 首页概览":
    st.markdown('<h1 class="main-header">📊 OpenBB 金融数据可视化平台</h1>', unsafe_allow_html=True)
    
    if obb is None and yf is None:
        st.error("⚠️ 数据源未就绪")
        st.code("pip install openbb yfinance", language="bash")
        st.stop()
    
    if obb_error:
        with st.expander("⚠️ OpenBB初始化警告（点击查看）"):
            st.warning(f"OpenBB初始化遇到问题，使用备用方案：{obb_error}")
    
    # 快速查询
    st.subheader("🚀 快速查询")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        quick_symbol = st.text_input("输入股票代码", value="QQQ", key="quick_symbol")
    with col2:
        quick_btn = st.button("查询", key="quick_query", type="primary")
    
    if quick_btn:
        with st.spinner("加载数据..."):
            data, source = get_price_data(quick_symbol)
            
            if not data.empty:
                st.caption(f"数据来源: {source}")
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=data.index,
                    open=data['open'],
                    high=data['high'],
                    low=data['low'],
                    close=data['close'],
                    name=quick_symbol
                ))
                fig.update_layout(
                    title=f"{quick_symbol} 价格走势",
                    xaxis_title="日期",
                    yaxis_title="价格",
                    height=500,
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 关键指标
                col1, col2, col3, col4 = st.columns(4)
                latest = data.iloc[-1]
                prev = data.iloc[-2] if len(data) > 1 else latest
                change = (latest['close'] - prev['close']) / prev['close'] * 100
                
                col1.metric("收盘价", f"${latest['close']:.2f}", f"{change:.2f}%")
                col2.metric("最高价", f"${latest['high']:.2f}")
                col3.metric("最低价", f"${latest['low']:.2f}")
                col4.metric("成交量", f"{latest['volume']:,.0f}")
            else:
                st.error(f"无法获取 {quick_symbol} 的数据")
    
    # 功能模块展示
    st.markdown("---")
    st.subheader("📋 可用功能模块")
    
    col1, col2, col3 = st.columns(3)
    
    modules = [
        ("📈 股票", "历史价格、K线图、基本面"),
        ("🎯 期权", "期权链、OI分布、Greeks"),
        ("💰 ETF", "持仓分析、业绩对比"),
        ("🔧 技术分析", "MA、RSI、MACD、布林带"),
        ("📐 量化", "夏普比率、VaR、相关性"),
        ("💵 外汇", "汇率查询、历史走势"),
    ]
    
    for i, (name, desc) in enumerate(modules):
        col = [col1, col2, col3][i % 3]
        with col:
            st.markdown(f"""
            <div class="module-card">
                <h4>{name}</h4>
                <p style="font-size:0.9rem">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

# ==================== 股票模块 ====================
elif main_module == "📈 股票 (Equity)":
    st.header("📈 股票数据分析")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        symbol = st.text_input("股票代码", value="QQQ", key="eq_symbol")
        
        date_range = st.selectbox("时间范围", 
            ["1个月", "3个月", "6个月", "1年", "2年"])
        
        days_map = {"1个月": 30, "3个月": 90, "6个月": 180, "1年": 365, "2年": 730}
        
        chart_type = st.selectbox("图表类型", ["K线图", "折线图", "面积图"])
        show_volume = st.checkbox("显示成交量", value=True)
        
        # 均线选项
        show_ma = st.checkbox("显示均线", value=True)
        if show_ma:
            ma_periods = st.multiselect("均线周期", [5, 10, 20, 50, 100, 200], default=[20, 50])
        
        fetch_btn = st.button("获取数据", key="eq_fetch", type="primary")
    
    with col2:
        if fetch_btn:
            with st.spinner("加载数据..."):
                data, source = get_price_data(symbol, days_map[date_range])
                
                if not data.empty:
                    st.caption(f"数据来源: {source}")
                    
                    # 创建图表
                    if show_volume:
                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            vertical_spacing=0.03, row_heights=[0.7, 0.3])
                    else:
                        fig = go.Figure()
                    
                    # 主图
                    if chart_type == "K线图":
                        trace = go.Candlestick(
                            x=data.index, open=data['open'],
                            high=data['high'], low=data['low'],
                            close=data['close'], name=symbol
                        )
                    elif chart_type == "折线图":
                        trace = go.Scatter(x=data.index, y=data['close'], mode='lines', name=symbol)
                    else:
                        trace = go.Scatter(x=data.index, y=data['close'], fill='tozeroy', name=symbol)
                    
                    if show_volume:
                        fig.add_trace(trace, row=1, col=1)
                        
                        # 添加均线
                        if show_ma:
                            for period in ma_periods:
                                ma = data['close'].rolling(window=period).mean()
                                fig.add_trace(go.Scatter(x=data.index, y=ma, 
                                    name=f'MA{period}', line=dict(width=1)), row=1, col=1)
                        
                        # 成交量
                        colors = ['red' if data['close'].iloc[i] < data['open'].iloc[i] 
                                 else 'green' for i in range(len(data))]
                        fig.add_trace(go.Bar(x=data.index, y=data['volume'],
                            marker_color=colors, name='成交量', showlegend=False), row=2, col=1)
                    else:
                        fig.add_trace(trace)
                        if show_ma:
                            for period in ma_periods:
                                ma = data['close'].rolling(window=period).mean()
                                fig.add_trace(go.Scatter(x=data.index, y=ma, 
                                    name=f'MA{period}', line=dict(width=1)))
                    
                    fig.update_layout(
                        title=f"{symbol} 价格走势",
                        height=600,
                        xaxis_rangeslider_visible=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 统计信息
                    st.subheader("📊 统计摘要")
                    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                    
                    returns = data['close'].pct_change().dropna()
                    
                    stats_col1.metric("区间收益率", 
                        f"{(data['close'].iloc[-1]/data['close'].iloc[0]-1)*100:.2f}%")
                    stats_col2.metric("日均波动率", f"{returns.std()*100:.2f}%")
                    stats_col3.metric("最高价", f"${data['high'].max():.2f}")
                    stats_col4.metric("最低价", f"${data['low'].min():.2f}")
                    
                    # 数据下载
                    with st.expander("📋 查看原始数据"):
                        st.dataframe(data.tail(50), use_container_width=True)
                        csv = data.to_csv()
                        st.download_button("下载CSV", csv, f"{symbol}_data.csv", "text/csv")
                else:
                    st.error(f"获取 {symbol} 数据失败")

# ==================== 期权分析模块 ====================
elif main_module == "🎯 期权分析 (Options)":
    st.header("🎯 期权分析")
    
    opt_tabs = st.tabs(["📊 期权链", "📈 OI分布", "🔧 Greeks计算器"])
    
    # 期权链
    with opt_tabs[0]:
        st.subheader("📊 期权链查询")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            opt_symbol = st.text_input("标的代码", value="QQQ", key="opt_symbol")
            fetch_opt = st.button("获取期权链", key="opt_fetch", type="primary")
        
        with col2:
            if fetch_opt:
                with st.spinner("加载期权链..."):
                    chains, source = get_options_chain(opt_symbol)
                    
                    if not chains.empty:
                        st.caption(f"数据来源: {source}")
                        
                        # 获取现价
                        price_data, _ = get_price_data(opt_symbol, 5)
                        spot_price = price_data['close'].iloc[-1] if not price_data.empty else 0
                        
                        st.metric(f"{opt_symbol} 现价", f"${spot_price:.2f}")
                        
                        # 到期日选择
                        if 'expiration' in chains.columns:
                            expirations = sorted(chains['expiration'].unique())
                            selected_exp = st.selectbox("选择到期日", expirations[:10])
                            
                            exp_data = chains[chains['expiration'] == selected_exp]
                            
                            # 分离Call/Put
                            if 'option_type' in exp_data.columns:
                                calls = exp_data[exp_data['option_type'] == 'call']
                                puts = exp_data[exp_data['option_type'] == 'put']
                            else:
                                calls = exp_data
                                puts = pd.DataFrame()
                            
                            tab1, tab2 = st.tabs(["📈 Calls", "📉 Puts"])
                            
                            display_cols = ['strike', 'last_price', 'bid', 'ask', 
                                           'volume', 'open_interest', 'implied_volatility']
                            
                            with tab1:
                                if not calls.empty:
                                    cols = [c for c in display_cols if c in calls.columns]
                                    st.dataframe(calls[cols].sort_values('strike'), 
                                                use_container_width=True)
                            
                            with tab2:
                                if not puts.empty:
                                    cols = [c for c in display_cols if c in puts.columns]
                                    st.dataframe(puts[cols].sort_values('strike'), 
                                                use_container_width=True)
                    else:
                        st.error(f"无法获取 {opt_symbol} 的期权数据")
    
    # OI分布
    with opt_tabs[1]:
        st.subheader("📈 持仓量(OI)分布")
        
        oi_symbol = st.text_input("标的代码", value="QQQ", key="oi_symbol")
        
        if st.button("分析OI", key="oi_fetch", type="primary"):
            with st.spinner("加载数据..."):
                chains, source = get_options_chain(oi_symbol)
                price_data, _ = get_price_data(oi_symbol, 5)
                
                if not chains.empty:
                    spot = price_data['close'].iloc[-1] if not price_data.empty else 0
                    
                    if 'expiration' in chains.columns:
                        expirations = sorted(chains['expiration'].unique())
                        selected_exp = st.selectbox("到期日", expirations[:5], key="oi_exp")
                        
                        exp_data = chains[chains['expiration'] == selected_exp]
                        
                        if 'option_type' in exp_data.columns and 'open_interest' in exp_data.columns:
                            calls = exp_data[exp_data['option_type'] == 'call']
                            puts = exp_data[exp_data['option_type'] == 'put']
                            
                            fig = go.Figure()
                            
                            if not calls.empty:
                                fig.add_trace(go.Bar(
                                    x=calls['strike'],
                                    y=calls['open_interest'],
                                    name='Calls OI',
                                    marker_color='rgba(0, 255, 0, 0.6)'
                                ))
                            
                            if not puts.empty:
                                fig.add_trace(go.Bar(
                                    x=puts['strike'],
                                    y=-puts['open_interest'],
                                    name='Puts OI',
                                    marker_color='rgba(255, 0, 0, 0.6)'
                                ))
                            
                            if spot > 0:
                                fig.add_vline(x=spot, line_dash="dash", line_color="yellow",
                                             annotation_text=f"现价: ${spot:.2f}")
                            
                            fig.update_layout(
                                title=f"{oi_symbol} 期权OI分布",
                                xaxis_title="行权价",
                                yaxis_title="持仓量 (Calls↑ / Puts↓)",
                                barmode='relative',
                                height=500
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # 关键位置
                            col1, col2, col3 = st.columns(3)
                            col1.metric("现价", f"${spot:.2f}")
                            
                            if not calls.empty and calls['open_interest'].max() > 0:
                                call_wall = calls.loc[calls['open_interest'].idxmax(), 'strike']
                                col2.metric("Call Wall", f"${call_wall:.2f}",
                                           f"{((call_wall-spot)/spot*100):.1f}%")
                            
                            if not puts.empty and puts['open_interest'].max() > 0:
                                put_wall = puts.loc[puts['open_interest'].idxmax(), 'strike']
                                col3.metric("Put Wall", f"${put_wall:.2f}",
                                           f"{((put_wall-spot)/spot*100):.1f}%")
    
    # Greeks计算器
    with opt_tabs[2]:
        st.subheader("🔧 Greeks计算器")
        
        from scipy.stats import norm
        
        def calc_greeks(S, K, T, r, sigma, opt_type='call'):
            if T <= 0:
                T = 0.001
            d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
            d2 = d1 - sigma*np.sqrt(T)
            
            if opt_type == 'call':
                delta = norm.cdf(d1)
                theta = (-S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) - r*K*np.exp(-r*T)*norm.cdf(d2)) / 365
            else:
                delta = norm.cdf(d1) - 1
                theta = (-S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) + r*K*np.exp(-r*T)*norm.cdf(-d2)) / 365
            
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            vega = S * norm.pdf(d1) * np.sqrt(T) / 100
            
            return {'delta': delta, 'gamma': gamma, 'theta': theta, 'vega': vega}
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            S = st.number_input("标的价格", value=500.0, step=1.0)
            K = st.number_input("行权价", value=500.0, step=1.0)
            T_days = st.number_input("剩余天数", value=30, step=1)
            r = st.number_input("无风险利率 (%)", value=5.0) / 100
            sigma = st.number_input("IV (%)", value=20.0) / 100
            opt_type = st.selectbox("类型", ["call", "put"])
        
        with col2:
            if st.button("计算", type="primary"):
                greeks = calc_greeks(S, K, T_days/365, r, sigma, opt_type)
                
                c1, c2 = st.columns(2)
                c1.metric("Delta (Δ)", f"{greeks['delta']:.4f}")
                c1.metric("Gamma (Γ)", f"{greeks['gamma']:.6f}")
                c2.metric("Theta (Θ)", f"{greeks['theta']:.4f}")
                c2.metric("Vega (ν)", f"{greeks['vega']:.4f}")
                
                # Delta曲线
                prices = np.linspace(S * 0.8, S * 1.2, 50)
                deltas = [calc_greeks(p, K, T_days/365, r, sigma, opt_type)['delta'] for p in prices]
                gammas = [calc_greeks(p, K, T_days/365, r, sigma, opt_type)['gamma'] for p in prices]
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                   subplot_titles=('Delta', 'Gamma'))
                fig.add_trace(go.Scatter(x=prices, y=deltas, name='Delta'), row=1, col=1)
                fig.add_trace(go.Scatter(x=prices, y=gammas, name='Gamma'), row=2, col=1)
                fig.add_vline(x=S, line_dash="dash", line_color="yellow")
                fig.add_vline(x=K, line_dash="dot", line_color="gray")
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)

# ==================== ETF模块 ====================
elif main_module == "💰 ETF":
    st.header("💰 ETF分析")
    
    etf_tabs = st.tabs(["📈 业绩对比", "📊 ETF查询"])
    
    with etf_tabs[0]:
        st.subheader("📈 ETF业绩对比")
        
        compare_symbols = st.text_input("输入ETF代码(逗号分隔)", value="SPY,QQQ,IWM,DIA,TLT")
        period = st.selectbox("对比周期", ["1个月", "3个月", "6个月", "1年"])
        
        days_map = {"1个月": 30, "3个月": 90, "6个月": 180, "1年": 365}
        
        if st.button("对比", type="primary"):
            symbols = [s.strip() for s in compare_symbols.split(",")]
            
            fig = go.Figure()
            
            for sym in symbols:
                data, _ = get_price_data(sym, days_map[period])
                if not data.empty:
                    normalized = data['close'] / data['close'].iloc[0] * 100
                    fig.add_trace(go.Scatter(x=data.index, y=normalized, name=sym))
            
            fig.update_layout(
                title="ETF业绩对比 (标准化到100)",
                yaxis_title="相对表现",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with etf_tabs[1]:
        st.subheader("📊 ETF查询")
        
        etf_symbol = st.text_input("ETF代码", value="QQQ", key="etf_query")
        
        if st.button("查询", key="etf_fetch"):
            data, source = get_price_data(etf_symbol)
            if not data.empty:
                st.caption(f"数据来源: {source}")
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=data.index, open=data['open'], high=data['high'],
                    low=data['low'], close=data['close'], name=etf_symbol
                ))
                fig.update_layout(title=f"{etf_symbol} 走势", height=500,
                                 xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

# ==================== 技术分析模块 ====================
elif main_module == "🔧 技术分析 (Technical)":
    st.header("🔧 技术分析")
    
    tech_symbol = st.text_input("分析标的", value="QQQ", key="tech_symbol")
    tech_period = st.selectbox("时间范围", ["3个月", "6个月", "1年"])
    
    days_map = {"3个月": 90, "6个月": 180, "1年": 365}
    
    if st.button("分析", type="primary"):
        data, source = get_price_data(tech_symbol, days_map[tech_period])
        
        if not data.empty:
            st.caption(f"数据来源: {source}")
            
            tech_tabs = st.tabs(["📈 均线", "📊 RSI", "📉 MACD", "🎯 布林带"])
            
            with tech_tabs[0]:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=data.index, open=data['open'], high=data['high'],
                    low=data['low'], close=data['close'], name='价格'
                ))
                
                for period in [20, 50, 200]:
                    ma = data['close'].rolling(window=period).mean()
                    fig.add_trace(go.Scatter(x=data.index, y=ma, name=f'MA{period}'))
                
                fig.update_layout(title=f"{tech_symbol} 均线分析", height=500,
                                 xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with tech_tabs[1]:
                # RSI计算
                delta = data['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = 100 - (100 / (1 + gain / loss))
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    vertical_spacing=0.1, row_heights=[0.6, 0.4])
                
                fig.add_trace(go.Candlestick(
                    x=data.index, open=data['open'], high=data['high'],
                    low=data['low'], close=data['close']), row=1, col=1)
                fig.add_trace(go.Scatter(x=data.index, y=rsi, name='RSI'), row=2, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                
                fig.update_layout(title=f"{tech_symbol} RSI分析", height=600,
                                 xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
                
                # RSI信号
                latest_rsi = rsi.iloc[-1]
                if latest_rsi > 70:
                    st.warning(f"⚠️ RSI = {latest_rsi:.1f} - 超买区域")
                elif latest_rsi < 30:
                    st.success(f"✅ RSI = {latest_rsi:.1f} - 超卖区域")
                else:
                    st.info(f"ℹ️ RSI = {latest_rsi:.1f} - 中性区域")
            
            with tech_tabs[2]:
                # MACD计算
                ema12 = data['close'].ewm(span=12).mean()
                ema26 = data['close'].ewm(span=26).mean()
                macd_line = ema12 - ema26
                signal_line = macd_line.ewm(span=9).mean()
                histogram = macd_line - signal_line
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    vertical_spacing=0.1, row_heights=[0.6, 0.4])
                
                fig.add_trace(go.Candlestick(
                    x=data.index, open=data['open'], high=data['high'],
                    low=data['low'], close=data['close']), row=1, col=1)
                
                colors = ['green' if h >= 0 else 'red' for h in histogram]
                fig.add_trace(go.Bar(x=data.index, y=histogram, name='Histogram',
                    marker_color=colors), row=2, col=1)
                fig.add_trace(go.Scatter(x=data.index, y=macd_line, name='MACD'), row=2, col=1)
                fig.add_trace(go.Scatter(x=data.index, y=signal_line, name='Signal'), row=2, col=1)
                
                fig.update_layout(title=f"{tech_symbol} MACD分析", height=600,
                                 xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with tech_tabs[3]:
                # 布林带
                sma = data['close'].rolling(20).mean()
                std = data['close'].rolling(20).std()
                upper = sma + 2 * std
                lower = sma - 2 * std
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=data.index, open=data['open'], high=data['high'],
                    low=data['low'], close=data['close'], name='价格'))
                fig.add_trace(go.Scatter(x=data.index, y=upper, name='上轨',
                    line=dict(dash='dash', color='gray')))
                fig.add_trace(go.Scatter(x=data.index, y=sma, name='中轨'))
                fig.add_trace(go.Scatter(x=data.index, y=lower, name='下轨',
                    line=dict(dash='dash', color='gray'), fill='tonexty'))
                
                fig.update_layout(title=f"{tech_symbol} 布林带", height=500,
                                 xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

# ==================== 量化分析模块 ====================
elif main_module == "📐 量化分析 (Quantitative)":
    st.header("📐 量化分析")
    
    quant_tabs = st.tabs(["📊 统计分析", "📈 风险指标", "🔗 相关性"])
    
    with quant_tabs[0]:
        st.subheader("📊 收益率统计")
        
        quant_symbol = st.text_input("股票代码", value="QQQ", key="quant_symbol")
        
        if st.button("分析", key="quant_btn"):
            data, _ = get_price_data(quant_symbol)
            
            if not data.empty:
                returns = data['close'].pct_change().dropna()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 统计摘要")
                    stats = {
                        "年化收益率": f"{returns.mean() * 252 * 100:.2f}%",
                        "年化波动率": f"{returns.std() * np.sqrt(252) * 100:.2f}%",
                        "偏度": f"{returns.skew():.4f}",
                        "峰度": f"{returns.kurtosis():.4f}",
                        "最大日涨幅": f"{returns.max() * 100:.2f}%",
                        "最大日跌幅": f"{returns.min() * 100:.2f}%",
                    }
                    for k, v in stats.items():
                        st.metric(k, v)
                
                with col2:
                    fig = go.Figure()
                    fig.add_trace(go.Histogram(x=returns, nbinsx=50))
                    fig.update_layout(title="日收益率分布", height=400)
                    st.plotly_chart(fig, use_container_width=True)
    
    with quant_tabs[1]:
        st.subheader("📈 风险指标")
        
        risk_symbol = st.text_input("股票代码", value="QQQ", key="risk_symbol")
        risk_free = st.number_input("无风险利率 (%)", value=5.0) / 100
        
        if st.button("计算", key="risk_btn"):
            data, _ = get_price_data(risk_symbol)
            
            if not data.empty:
                returns = data['close'].pct_change().dropna()
                
                ann_return = returns.mean() * 252
                ann_vol = returns.std() * np.sqrt(252)
                sharpe = (ann_return - risk_free) / ann_vol
                
                # 最大回撤
                cum = (1 + returns).cumprod()
                rolling_max = cum.expanding().max()
                drawdown = (cum - rolling_max) / rolling_max
                max_dd = drawdown.min()
                
                # VaR
                var_95 = returns.quantile(0.05)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("夏普比率", f"{sharpe:.2f}")
                col2.metric("最大回撤", f"{max_dd*100:.2f}%")
                col3.metric("VaR (95%)", f"{var_95*100:.2f}%")
                
                # 回撤图
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=drawdown.index, y=drawdown*100, fill='tozeroy'))
                fig.update_layout(title="回撤曲线", yaxis_title="回撤 (%)", height=300)
                st.plotly_chart(fig, use_container_width=True)
    
    with quant_tabs[2]:
        st.subheader("🔗 相关性分析")
        
        corr_symbols = st.text_input("多个代码(逗号分隔)", value="QQQ,SPY,IWM,TLT,GLD")
        
        if st.button("计算相关性", key="corr_btn"):
            symbols = [s.strip() for s in corr_symbols.split(",")]
            
            returns_dict = {}
            for sym in symbols:
                data, _ = get_price_data(sym)
                if not data.empty:
                    returns_dict[sym] = data['close'].pct_change()
            
            if len(returns_dict) > 1:
                returns_df = pd.DataFrame(returns_dict).dropna()
                corr = returns_df.corr()
                
                fig = px.imshow(corr, labels=dict(color="相关系数"),
                    color_continuous_scale="RdBu_r", aspect="auto")
                fig.update_layout(title="相关性矩阵", height=500)
                st.plotly_chart(fig, use_container_width=True)

# ==================== 外汇模块 ====================
elif main_module == "💵 外汇 (Currency)":
    st.header("💵 外汇市场")
    
    fx_pair = st.text_input("货币对 (如USDJPY=X)", value="USDJPY=X")
    
    if st.button("查询", type="primary"):
        data, source = get_price_data(fx_pair)
        
        if not data.empty:
            st.caption(f"数据来源: {source}")
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=data.index, open=data['open'], high=data['high'],
                low=data['low'], close=data['close'], name=fx_pair
            ))
            fig.update_layout(title=f"{fx_pair} 走势", height=500,
                             xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            latest = data.iloc[-1]['close']
            prev = data.iloc[-2]['close'] if len(data) > 1 else latest
            change = (latest - prev) / prev * 100
            
            st.metric("最新价", f"{latest:.4f}", f"{change:.2f}%")

# ==================== 加密货币模块 ====================
elif main_module == "💎 加密货币 (Crypto)":
    st.header("💎 加密货币")
    
    crypto_symbol = st.text_input("代码 (如BTC-USD)", value="BTC-USD")
    
    if st.button("查询", type="primary"):
        data, source = get_price_data(crypto_symbol)
        
        if not data.empty:
            st.caption(f"数据来源: {source}")
            
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=data.index, open=data['open'], high=data['high'],
                low=data['low'], close=data['close'], name=crypto_symbol
            ))
            fig.update_layout(title=f"{crypto_symbol} 走势", height=500,
                             xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            latest = data.iloc[-1]
            col1.metric("最新价", f"${latest['close']:,.2f}")
            col2.metric("24h高", f"${latest['high']:,.2f}")
            col3.metric("24h低", f"${latest['low']:,.2f}")

# ==================== Footer ====================
st.sidebar.markdown("---")
st.sidebar.markdown("""
### 📚 说明
- 数据来源: yfinance (免费)
- 部分功能需要API密钥
- 数据仅供参考
""")
