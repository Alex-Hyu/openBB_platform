"""
OpenBB Streamlit Dashboard
完整可视化OpenBB所有功能模块
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

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
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        background-color: #f0f2f6;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# 初始化OpenBB
@st.cache_resource
def init_openbb():
    try:
        from openbb import obb
        return obb
    except ImportError:
        return None

obb = init_openbb()

# Sidebar - 模块导航
st.sidebar.markdown("## 🏦 OpenBB 数据平台")
st.sidebar.markdown("---")

# 主模块选择
main_module = st.sidebar.selectbox(
    "📁 选择功能模块",
    [
        "🏠 首页概览",
        "📈 股票 (Equity)",
        "🎯 衍生品 (Derivatives)", 
        "💰 ETF",
        "📊 指数 (Index)",
        "🌍 经济数据 (Economy)",
        "💵 外汇 (Currency)",
        "🔧 技术分析 (Technical)",
        "📐 量化分析 (Quantitative)",
        "💎 加密货币 (Crypto)",
        "📰 新闻 (News)",
        "🛢️ 大宗商品 (Commodity)",
        "🏛️ 固定收益 (Fixed Income)",
        "📋 监管数据 (Regulators)"
    ]
)

# ==================== 首页概览 ====================
if main_module == "🏠 首页概览":
    st.markdown('<h1 class="main-header">📊 OpenBB 金融数据可视化平台</h1>', unsafe_allow_html=True)
    
    if obb is None:
        st.error("⚠️ OpenBB未安装！请运行: `pip install openbb`")
        st.code("pip install openbb", language="bash")
        st.stop()
    
    st.success("✅ OpenBB 已连接")
    
    # 功能模块展示
    col1, col2, col3 = st.columns(3)
    
    modules = [
        ("📈 股票", "历史价格、基本面、筛选器", "equity"),
        ("🎯 衍生品", "期权链、Greeks、隐含波动率", "derivatives"),
        ("💰 ETF", "持仓、行业分布、业绩", "etf"),
        ("📊 指数", "成分股、历史数据", "index"),
        ("🌍 经济", "GDP、CPI、利率、就业", "economy"),
        ("💵 外汇", "汇率、历史数据", "currency"),
        ("🔧 技术分析", "MACD、RSI、布林带", "technical"),
        ("📐 量化", "夏普比率、VaR、相关性", "quantitative"),
        ("💎 加密货币", "价格、交易量", "crypto"),
        ("📰 新闻", "市场新闻、公司新闻", "news"),
        ("🛢️ 大宗商品", "原油、黄金、农产品", "commodity"),
        ("🏛️ 固定收益", "国债、收益率曲线", "fixedincome"),
    ]
    
    for i, (name, desc, _) in enumerate(modules):
        col = [col1, col2, col3][i % 3]
        with col:
            st.markdown(f"""
            <div class="module-card">
                <h4>{name}</h4>
                <p style="font-size:0.9rem">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 快速查询
    st.subheader("🚀 快速查询")
    quick_symbol = st.text_input("输入股票代码", value="AAPL", key="quick_symbol")
    
    if st.button("查询", key="quick_query"):
        with st.spinner("加载数据..."):
            try:
                data = obb.equity.price.historical(quick_symbol, provider="yfinance").to_df()
                if not data.empty:
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
                        height=500
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 显示关键指标
                    col1, col2, col3, col4 = st.columns(4)
                    latest = data.iloc[-1]
                    prev = data.iloc[-2] if len(data) > 1 else latest
                    change = (latest['close'] - prev['close']) / prev['close'] * 100
                    
                    col1.metric("收盘价", f"${latest['close']:.2f}", f"{change:.2f}%")
                    col2.metric("最高价", f"${latest['high']:.2f}")
                    col3.metric("最低价", f"${latest['low']:.2f}")
                    col4.metric("成交量", f"{latest['volume']:,.0f}")
            except Exception as e:
                st.error(f"查询失败: {str(e)}")

# ==================== 股票模块 ====================
elif main_module == "📈 股票 (Equity)":
    st.header("📈 股票数据分析")
    
    if obb is None:
        st.error("OpenBB未安装")
        st.stop()
    
    equity_tab = st.tabs([
        "📊 历史价格", 
        "🔍 股票筛选", 
        "📋 公司信息",
        "📈 基本面",
        "🏷️ 空头数据"
    ])
    
    # 历史价格
    with equity_tab[0]:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            symbol = st.text_input("股票代码", value="QQQ", key="eq_symbol")
            
            date_range = st.selectbox("时间范围", 
                ["1个月", "3个月", "6个月", "1年", "2年", "5年", "自定义"])
            
            if date_range == "自定义":
                start_date = st.date_input("开始日期", 
                    value=datetime.now() - timedelta(days=365))
                end_date = st.date_input("结束日期", value=datetime.now())
            else:
                days_map = {"1个月": 30, "3个月": 90, "6个月": 180, 
                           "1年": 365, "2年": 730, "5年": 1825}
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_map[date_range])
            
            chart_type = st.selectbox("图表类型", ["K线图", "折线图", "面积图"])
            
            show_volume = st.checkbox("显示成交量", value=True)
            
            fetch_btn = st.button("获取数据", key="eq_fetch")
        
        with col2:
            if fetch_btn:
                with st.spinner("加载数据..."):
                    try:
                        data = obb.equity.price.historical(
                            symbol, 
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=end_date.strftime("%Y-%m-%d"),
                            provider="yfinance"
                        ).to_df()
                        
                        if not data.empty:
                            # 创建图表
                            if show_volume:
                                from plotly.subplots import make_subplots
                                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                    vertical_spacing=0.03, row_heights=[0.7, 0.3])
                            else:
                                fig = go.Figure()
                            
                            if chart_type == "K线图":
                                trace = go.Candlestick(
                                    x=data.index, open=data['open'],
                                    high=data['high'], low=data['low'],
                                    close=data['close'], name=symbol
                                )
                            elif chart_type == "折线图":
                                trace = go.Scatter(
                                    x=data.index, y=data['close'],
                                    mode='lines', name=symbol
                                )
                            else:
                                trace = go.Scatter(
                                    x=data.index, y=data['close'],
                                    fill='tozeroy', name=symbol
                                )
                            
                            if show_volume:
                                fig.add_trace(trace, row=1, col=1)
                                colors = ['red' if data['close'].iloc[i] < data['open'].iloc[i] 
                                         else 'green' for i in range(len(data))]
                                fig.add_trace(go.Bar(x=data.index, y=data['volume'],
                                    marker_color=colors, name='成交量'), row=2, col=1)
                            else:
                                fig.add_trace(trace)
                            
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
                            
                            # 显示原始数据
                            with st.expander("📋 查看原始数据"):
                                st.dataframe(data.tail(50), use_container_width=True)
                                
                                csv = data.to_csv()
                                st.download_button(
                                    "下载CSV", csv, f"{symbol}_data.csv", "text/csv"
                                )
                                
                    except Exception as e:
                        st.error(f"获取数据失败: {str(e)}")
    
    # 股票筛选
    with equity_tab[1]:
        st.subheader("🔍 股票筛选器")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            market_cap_min = st.number_input("最小市值 (百万)", value=1000, step=100)
            pe_max = st.number_input("最大市盈率", value=50.0, step=1.0)
        
        with col2:
            market_cap_max = st.number_input("最大市值 (百万)", value=100000, step=1000)
            sector = st.selectbox("行业", ["全部", "Technology", "Healthcare", 
                "Financial Services", "Consumer Cyclical", "Energy"])
        
        with col3:
            volume_min = st.number_input("最小日均成交量", value=1000000, step=100000)
        
        if st.button("开始筛选", key="screener"):
            st.info("股票筛选功能需要配置数据源API密钥（如FMP、Polygon等）")
            st.code("""
# 筛选示例代码
from openbb import obb
results = obb.equity.screener(
    market_cap_min=1000000000,
    market_cap_max=100000000000,
    provider="fmp"  # 需要API密钥
)
            """)
    
    # 公司信息
    with equity_tab[2]:
        st.subheader("📋 公司基本信息")
        
        profile_symbol = st.text_input("输入股票代码", value="AAPL", key="profile_symbol")
        
        if st.button("查询公司信息", key="profile_fetch"):
            try:
                profile = obb.equity.profile(profile_symbol, provider="yfinance").to_df()
                if not profile.empty:
                    st.dataframe(profile.T, use_container_width=True)
            except Exception as e:
                st.warning(f"获取公司信息失败: {str(e)}")
    
    # 基本面数据
    with equity_tab[3]:
        st.subheader("📈 基本面数据")
        st.info("基本面数据需要配置FMP或其他数据源的API密钥")
        
        fund_symbol = st.text_input("股票代码", value="AAPL", key="fund_symbol")
        
        fund_type = st.selectbox("数据类型", [
            "收入表 (Income Statement)",
            "资产负债表 (Balance Sheet)",
            "现金流量表 (Cash Flow)"
        ])
        
        st.code(f"""
# 获取{fund_type}示例代码
from openbb import obb
# 需要API密钥
obb.equity.fundamental.income("{fund_symbol}", provider="fmp")
        """)
    
    # 空头数据
    with equity_tab[4]:
        st.subheader("🏷️ 空头数据")
        
        short_symbol = st.text_input("股票代码", value="GME", key="short_symbol")
        
        if st.button("查询空头数据", key="short_fetch"):
            try:
                short_vol = obb.equity.short_volume(short_symbol).to_df()
                if not short_vol.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=short_vol.index, 
                        y=short_vol['short_volume'] if 'short_volume' in short_vol.columns else short_vol.iloc[:, 0],
                        name='空头成交量'
                    ))
                    fig.update_layout(title=f"{short_symbol} 空头成交量", height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    st.dataframe(short_vol, use_container_width=True)
            except Exception as e:
                st.warning(f"获取空头数据失败: {str(e)}")

# ==================== 衍生品模块 ====================
elif main_module == "🎯 衍生品 (Derivatives)":
    st.header("🎯 衍生品分析")
    
    if obb is None:
        st.error("OpenBB未安装")
        st.stop()
    
    deriv_tabs = st.tabs(["📊 期权链", "📈 隐含波动率曲面", "🎲 异常期权活动"])
    
    # 期权链
    with deriv_tabs[0]:
        st.subheader("📊 期权链查询")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            opt_symbol = st.text_input("标的代码", value="QQQ", key="opt_symbol")
            
            if st.button("获取期权链", key="opt_chain"):
                st.session_state['fetch_options'] = True
        
        with col2:
            if st.session_state.get('fetch_options', False):
                with st.spinner("加载期权链..."):
                    try:
                        chains = obb.derivatives.options.chains(opt_symbol, provider="yfinance").to_df()
                        
                        if not chains.empty:
                            # 获取到期日列表
                            if 'expiration' in chains.columns:
                                expirations = chains['expiration'].unique()
                                selected_exp = st.selectbox("选择到期日", expirations)
                                
                                # 筛选特定到期日
                                exp_data = chains[chains['expiration'] == selected_exp]
                                
                                # 分离看涨和看跌
                                if 'option_type' in exp_data.columns:
                                    calls = exp_data[exp_data['option_type'] == 'call']
                                    puts = exp_data[exp_data['option_type'] == 'put']
                                else:
                                    calls = exp_data
                                    puts = pd.DataFrame()
                                
                                col_call, col_put = st.columns(2)
                                
                                with col_call:
                                    st.markdown("### 📈 看涨期权 (Calls)")
                                    display_cols = ['strike', 'last_price', 'bid', 'ask', 
                                                   'volume', 'open_interest', 'implied_volatility']
                                    available_cols = [c for c in display_cols if c in calls.columns]
                                    if available_cols:
                                        st.dataframe(calls[available_cols], use_container_width=True)
                                
                                with col_put:
                                    st.markdown("### 📉 看跌期权 (Puts)")
                                    if not puts.empty:
                                        available_cols = [c for c in display_cols if c in puts.columns]
                                        if available_cols:
                                            st.dataframe(puts[available_cols], use_container_width=True)
                                
                                # 可视化OI分布
                                if 'open_interest' in exp_data.columns and 'strike' in exp_data.columns:
                                    st.subheader("持仓量分布")
                                    
                                    fig = go.Figure()
                                    
                                    if not calls.empty:
                                        fig.add_trace(go.Bar(
                                            x=calls['strike'], 
                                            y=calls['open_interest'],
                                            name='Calls OI',
                                            marker_color='green'
                                        ))
                                    
                                    if not puts.empty:
                                        fig.add_trace(go.Bar(
                                            x=puts['strike'], 
                                            y=-puts['open_interest'],  # 负值显示在下方
                                            name='Puts OI',
                                            marker_color='red'
                                        ))
                                    
                                    fig.update_layout(
                                        title="期权持仓量分布 (OI)",
                                        barmode='relative',
                                        height=400
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.dataframe(chains, use_container_width=True)
                                
                    except Exception as e:
                        st.error(f"获取期权链失败: {str(e)}")
    
    # IV曲面
    with deriv_tabs[1]:
        st.subheader("📈 隐含波动率曲面")
        
        iv_symbol = st.text_input("标的代码", value="SPY", key="iv_symbol")
        
        if st.button("生成IV曲面", key="iv_surface"):
            st.info("IV曲面需要完整的期权数据。这里展示模拟数据结构：")
            
            # 模拟IV曲面数据
            import numpy as np
            
            strikes = np.linspace(0.8, 1.2, 20)  # Moneyness
            expirations = np.array([7, 14, 30, 60, 90, 180, 365])  # DTE
            
            # 模拟波动率微笑
            X, Y = np.meshgrid(strikes, expirations)
            Z = 0.2 + 0.1 * (X - 1)**2 + 0.001 * Y  # 简化IV模型
            
            fig = go.Figure(data=[go.Surface(x=X, y=Y, z=Z, colorscale='Viridis')])
            fig.update_layout(
                title=f'{iv_symbol} IV Surface (模拟数据)',
                scene=dict(
                    xaxis_title='Moneyness (K/S)',
                    yaxis_title='DTE',
                    zaxis_title='Implied Volatility'
                ),
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 异常期权活动
    with deriv_tabs[2]:
        st.subheader("🎲 异常期权活动")
        st.info("异常期权活动检测需要配置专业数据源（如CBOE、Unusual Whales等）")
        
        st.code("""
# 查询异常期权示例
from openbb import obb
unusual = obb.derivatives.options.unusual(provider="intrinio")  # 需要API密钥
        """)

# ==================== ETF模块 ====================
elif main_module == "💰 ETF":
    st.header("💰 ETF分析")
    
    if obb is None:
        st.error("OpenBB未安装")
        st.stop()
    
    etf_tabs = st.tabs(["📊 ETF信息", "🏢 持仓分析", "📈 业绩对比"])
    
    with etf_tabs[0]:
        st.subheader("📊 ETF基本信息")
        
        etf_symbol = st.text_input("ETF代码", value="SPY", key="etf_info_symbol")
        
        if st.button("查询ETF信息", key="etf_info"):
            try:
                info = obb.etf.info(etf_symbol, provider="yfinance").to_df()
                if not info.empty:
                    st.dataframe(info.T, use_container_width=True)
            except Exception as e:
                st.warning(f"获取ETF信息失败: {str(e)}")
    
    with etf_tabs[1]:
        st.subheader("🏢 ETF持仓分析")
        
        holding_symbol = st.text_input("ETF代码", value="QQQ", key="etf_holding_symbol")
        
        if st.button("查询持仓", key="etf_holdings"):
            try:
                holdings = obb.etf.holdings(holding_symbol, provider="yfinance").to_df()
                if not holdings.empty:
                    # 显示前20大持仓
                    st.dataframe(holdings.head(20), use_container_width=True)
                    
                    # 饼图
                    if 'weight' in holdings.columns or 'percent' in holdings.columns:
                        weight_col = 'weight' if 'weight' in holdings.columns else 'percent'
                        name_col = 'name' if 'name' in holdings.columns else holdings.columns[0]
                        
                        top10 = holdings.head(10)
                        fig = px.pie(top10, values=weight_col, names=name_col,
                                    title=f'{holding_symbol} 前10大持仓')
                        st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"获取持仓失败: {str(e)}")
    
    with etf_tabs[2]:
        st.subheader("📈 ETF业绩对比")
        
        compare_symbols = st.text_input("输入ETF代码(逗号分隔)", value="SPY,QQQ,IWM,DIA")
        
        if st.button("对比业绩", key="etf_compare"):
            symbols = [s.strip() for s in compare_symbols.split(",")]
            
            fig = go.Figure()
            
            for sym in symbols:
                try:
                    data = obb.equity.price.historical(
                        sym, 
                        start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                        provider="yfinance"
                    ).to_df()
                    
                    if not data.empty:
                        # 标准化到100
                        normalized = data['close'] / data['close'].iloc[0] * 100
                        fig.add_trace(go.Scatter(x=data.index, y=normalized, name=sym))
                except:
                    pass
            
            fig.update_layout(
                title="ETF业绩对比 (标准化到100)",
                yaxis_title="标准化价格",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

# ==================== 经济数据模块 ====================
elif main_module == "🌍 经济数据 (Economy)":
    st.header("🌍 宏观经济数据")
    
    if obb is None:
        st.error("OpenBB未安装")
        st.stop()
    
    econ_tabs = st.tabs(["📊 CPI通胀", "💼 就业数据", "📈 GDP", "🏦 利率", "📉 FRED数据"])
    
    with econ_tabs[0]:
        st.subheader("📊 消费者物价指数 (CPI)")
        
        countries = st.multiselect("选择国家", 
            ["united_states", "china", "japan", "germany", "united_kingdom"],
            default=["united_states"])
        
        if st.button("获取CPI数据", key="cpi_fetch"):
            try:
                for country in countries:
                    cpi_data = obb.economy.cpi(country=country).to_df()
                    if not cpi_data.empty:
                        st.write(f"**{country}**")
                        
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=cpi_data.index, 
                            y=cpi_data.iloc[:, 0],
                            name=country
                        ))
                        fig.update_layout(title=f"{country} CPI", height=300)
                        st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"获取CPI数据失败: {str(e)}")
    
    with econ_tabs[1]:
        st.subheader("💼 就业数据")
        st.info("就业数据需要配置FRED API密钥")
        
        st.code("""
# 获取非农就业数据
from openbb import obb
nfp = obb.economy.fred_series("PAYEMS", provider="fred")  # 需要API密钥
        """)
    
    with econ_tabs[2]:
        st.subheader("📈 GDP数据")
        
        try:
            gdp_data = obb.economy.gdp.nominal(country="united_states").to_df()
            if not gdp_data.empty:
                fig = px.line(gdp_data, title="美国名义GDP")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.info(f"GDP数据需要配置数据源: {str(e)}")
    
    with econ_tabs[3]:
        st.subheader("🏦 利率数据")
        
        try:
            # 尝试获取联邦基金利率
            rates = obb.fixedincome.rate.effr().to_df()
            if not rates.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=rates.index, y=rates.iloc[:, 0], name='EFFR'))
                fig.update_layout(title="有效联邦基金利率 (EFFR)", height=400)
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.info(f"利率数据需要配置数据源: {str(e)}")
    
    with econ_tabs[4]:
        st.subheader("📉 FRED数据查询")
        
        fred_series = st.text_input("FRED系列ID", value="GDP", 
            help="常用: GDP, UNRATE, CPIAUCSL, DFF, T10Y2Y")
        
        st.code(f"""
# 查询FRED数据
from openbb import obb
data = obb.economy.fred_series("{fred_series}", provider="fred")  # 需要FRED API密钥
        """)
        
        st.markdown("""
        **常用FRED系列ID:**
        - `GDP` - 国内生产总值
        - `UNRATE` - 失业率
        - `CPIAUCSL` - CPI
        - `DFF` - 联邦基金利率
        - `T10Y2Y` - 10Y-2Y利差
        - `VIXCLS` - VIX指数
        """)

# ==================== 外汇模块 ====================
elif main_module == "💵 外汇 (Currency)":
    st.header("💵 外汇市场")
    
    if obb is None:
        st.error("OpenBB未安装")
        st.stop()
    
    fx_tabs = st.tabs(["📊 汇率查询", "📈 历史走势", "🔄 货币对比"])
    
    with fx_tabs[0]:
        st.subheader("📊 实时汇率")
        
        base_currency = st.selectbox("基础货币", ["USD", "EUR", "GBP", "JPY", "CNY"])
        quote_currencies = st.multiselect("目标货币", 
            ["EUR", "GBP", "JPY", "CNY", "CHF", "AUD", "CAD"],
            default=["EUR", "JPY", "CNY"])
        
        if st.button("获取汇率", key="fx_rate"):
            for quote in quote_currencies:
                pair = f"{base_currency}{quote}"
                try:
                    data = obb.currency.price.historical(pair, provider="yfinance").to_df()
                    if not data.empty:
                        latest = data.iloc[-1]['close']
                        prev = data.iloc[-2]['close'] if len(data) > 1 else latest
                        change = (latest - prev) / prev * 100
                        st.metric(f"{pair}", f"{latest:.4f}", f"{change:.2f}%")
                except:
                    pass
    
    with fx_tabs[1]:
        st.subheader("📈 汇率历史走势")
        
        fx_pair = st.text_input("货币对", value="USDJPY", key="fx_pair",
            help="格式: USDJPY, EURUSD, GBPUSD等")
        
        if st.button("查询历史", key="fx_history"):
            try:
                data = obb.currency.price.historical(
                    fx_pair, 
                    start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                    provider="yfinance"
                ).to_df()
                
                if not data.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=data.index,
                        open=data['open'],
                        high=data['high'],
                        low=data['low'],
                        close=data['close'],
                        name=fx_pair
                    ))
                    fig.update_layout(title=f"{fx_pair} 走势", height=500)
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"获取数据失败: {str(e)}")
    
    with fx_tabs[2]:
        st.subheader("🔄 美元指数相关货币对")
        
        # 主要美元货币对
        usd_pairs = ["EURUSD", "USDJPY", "GBPUSD", "USDCHF", "AUDUSD", "USDCAD"]
        
        if st.button("加载货币对", key="fx_compare"):
            fig = go.Figure()
            
            for pair in usd_pairs:
                try:
                    data = obb.currency.price.historical(
                        pair,
                        start_date=(datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
                        provider="yfinance"
                    ).to_df()
                    
                    if not data.empty:
                        normalized = data['close'] / data['close'].iloc[0] * 100
                        fig.add_trace(go.Scatter(x=data.index, y=normalized, name=pair))
                except:
                    pass
            
            fig.update_layout(
                title="主要货币对走势对比 (标准化)",
                yaxis_title="相对变化 (%)",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

# ==================== 技术分析模块 ====================
elif main_module == "🔧 技术分析 (Technical)":
    st.header("🔧 技术分析")
    
    if obb is None:
        st.error("OpenBB未安装")
        st.stop()
    
    tech_tabs = st.tabs(["📈 趋势指标", "📊 动量指标", "📉 波动率指标", "🎯 综合分析"])
    
    tech_symbol = st.sidebar.text_input("分析标的", value="QQQ", key="tech_symbol")
    tech_period = st.sidebar.selectbox("时间范围", ["3个月", "6个月", "1年"], key="tech_period")
    
    # 获取数据
    @st.cache_data(ttl=300)
    def get_tech_data(symbol, days):
        try:
            data = obb.equity.price.historical(
                symbol,
                start_date=(datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
                provider="yfinance"
            ).to_df()
            return data
        except:
            return pd.DataFrame()
    
    days_map = {"3个月": 90, "6个月": 180, "1年": 365}
    data = get_tech_data(tech_symbol, days_map[tech_period])
    
    with tech_tabs[0]:
        st.subheader("📈 趋势指标")
        
        if not data.empty:
            col1, col2 = st.columns([1, 3])
            
            with col1:
                ma_type = st.selectbox("均线类型", ["SMA", "EMA", "WMA"])
                ma_periods = st.multiselect("均线周期", [5, 10, 20, 50, 100, 200], default=[20, 50])
            
            with col2:
                fig = go.Figure()
                
                # 价格
                fig.add_trace(go.Candlestick(
                    x=data.index, open=data['open'], high=data['high'],
                    low=data['low'], close=data['close'], name='Price'
                ))
                
                # 添加均线
                for period in ma_periods:
                    if ma_type == "SMA":
                        ma = data['close'].rolling(window=period).mean()
                    elif ma_type == "EMA":
                        ma = data['close'].ewm(span=period).mean()
                    else:
                        weights = list(range(1, period + 1))
                        ma = data['close'].rolling(window=period).apply(
                            lambda x: sum(weights * x) / sum(weights))
                    
                    fig.add_trace(go.Scatter(x=data.index, y=ma, name=f'{ma_type}{period}'))
                
                fig.update_layout(title=f"{tech_symbol} 趋势分析", height=500,
                                 xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
    
    with tech_tabs[1]:
        st.subheader("📊 动量指标")
        
        if not data.empty:
            indicator = st.selectbox("选择指标", ["RSI", "MACD", "Stochastic"])
            
            from plotly.subplots import make_subplots
            
            if indicator == "RSI":
                rsi_period = st.slider("RSI周期", 5, 30, 14)
                
                # 计算RSI
                delta = data['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                    vertical_spacing=0.1, row_heights=[0.6, 0.4])
                
                fig.add_trace(go.Candlestick(
                    x=data.index, open=data['open'], high=data['high'],
                    low=data['low'], close=data['close'], name='Price'), row=1, col=1)
                
                fig.add_trace(go.Scatter(x=data.index, y=rsi, name='RSI'), row=2, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                
                fig.update_layout(height=600, title=f"{tech_symbol} RSI分析")
                st.plotly_chart(fig, use_container_width=True)
            
            elif indicator == "MACD":
                fast = st.slider("快线周期", 5, 20, 12)
                slow = st.slider("慢线周期", 15, 40, 26)
                signal = st.slider("信号线周期", 5, 15, 9)
                
                # 计算MACD
                ema_fast = data['close'].ewm(span=fast).mean()
                ema_slow = data['close'].ewm(span=slow).mean()
                macd_line = ema_fast - ema_slow
                signal_line = macd_line.ewm(span=signal).mean()
                histogram = macd_line - signal_line
                
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    vertical_spacing=0.1, row_heights=[0.6, 0.4])
                
                fig.add_trace(go.Candlestick(
                    x=data.index, open=data['open'], high=data['high'],
                    low=data['low'], close=data['close'], name='Price'), row=1, col=1)
                
                colors = ['green' if h >= 0 else 'red' for h in histogram]
                fig.add_trace(go.Bar(x=data.index, y=histogram, name='Histogram',
                    marker_color=colors), row=2, col=1)
                fig.add_trace(go.Scatter(x=data.index, y=macd_line, name='MACD'), row=2, col=1)
                fig.add_trace(go.Scatter(x=data.index, y=signal_line, name='Signal'), row=2, col=1)
                
                fig.update_layout(height=600, title=f"{tech_symbol} MACD分析")
                st.plotly_chart(fig, use_container_width=True)
    
    with tech_tabs[2]:
        st.subheader("📉 波动率指标")
        
        if not data.empty:
            vol_indicator = st.selectbox("选择指标", ["布林带", "ATR", "历史波动率"])
            
            if vol_indicator == "布林带":
                bb_period = st.slider("周期", 10, 30, 20)
                bb_std = st.slider("标准差倍数", 1.0, 3.0, 2.0)
                
                sma = data['close'].rolling(window=bb_period).mean()
                std = data['close'].rolling(window=bb_period).std()
                upper = sma + bb_std * std
                lower = sma - bb_std * std
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=data.index, open=data['open'], high=data['high'],
                    low=data['low'], close=data['close'], name='Price'))
                fig.add_trace(go.Scatter(x=data.index, y=upper, name='Upper Band',
                    line=dict(dash='dash')))
                fig.add_trace(go.Scatter(x=data.index, y=sma, name='Middle'))
                fig.add_trace(go.Scatter(x=data.index, y=lower, name='Lower Band',
                    line=dict(dash='dash'), fill='tonexty'))
                
                fig.update_layout(height=500, title=f"{tech_symbol} 布林带")
                st.plotly_chart(fig, use_container_width=True)
            
            elif vol_indicator == "ATR":
                atr_period = st.slider("ATR周期", 5, 30, 14)
                
                high_low = data['high'] - data['low']
                high_close = abs(data['high'] - data['close'].shift())
                low_close = abs(data['low'] - data['close'].shift())
                tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
                atr = tr.rolling(window=atr_period).mean()
                
                from plotly.subplots import make_subplots
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                    vertical_spacing=0.1, row_heights=[0.6, 0.4])
                
                fig.add_trace(go.Candlestick(
                    x=data.index, open=data['open'], high=data['high'],
                    low=data['low'], close=data['close'], name='Price'), row=1, col=1)
                fig.add_trace(go.Scatter(x=data.index, y=atr, name='ATR',
                    fill='tozeroy'), row=2, col=1)
                
                fig.update_layout(height=600, title=f"{tech_symbol} ATR")
                st.plotly_chart(fig, use_container_width=True)
    
    with tech_tabs[3]:
        st.subheader("🎯 综合技术分析")
        
        if not data.empty:
            # 计算多个指标
            data_analysis = data.copy()
            
            # SMA
            data_analysis['SMA20'] = data['close'].rolling(20).mean()
            data_analysis['SMA50'] = data['close'].rolling(50).mean()
            
            # RSI
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            data_analysis['RSI'] = 100 - (100 / (1 + gain / loss))
            
            # MACD
            ema12 = data['close'].ewm(span=12).mean()
            ema26 = data['close'].ewm(span=26).mean()
            data_analysis['MACD'] = ema12 - ema26
            data_analysis['Signal'] = data_analysis['MACD'].ewm(span=9).mean()
            
            latest = data_analysis.iloc[-1]
            
            # 信号判断
            signals = []
            
            # SMA信号
            if latest['close'] > latest['SMA20']:
                signals.append(("价格 > SMA20", "看多", "green"))
            else:
                signals.append(("价格 < SMA20", "看空", "red"))
            
            if latest['SMA20'] > latest['SMA50']:
                signals.append(("SMA20 > SMA50", "看多", "green"))
            else:
                signals.append(("SMA20 < SMA50", "看空", "red"))
            
            # RSI信号
            if latest['RSI'] > 70:
                signals.append((f"RSI = {latest['RSI']:.1f}", "超买", "red"))
            elif latest['RSI'] < 30:
                signals.append((f"RSI = {latest['RSI']:.1f}", "超卖", "green"))
            else:
                signals.append((f"RSI = {latest['RSI']:.1f}", "中性", "gray"))
            
            # MACD信号
            if latest['MACD'] > latest['Signal']:
                signals.append(("MACD > Signal", "看多", "green"))
            else:
                signals.append(("MACD < Signal", "看空", "red"))
            
            # 显示信号
            st.markdown("### 技术信号汇总")
            
            cols = st.columns(len(signals))
            for i, (condition, signal, color) in enumerate(signals):
                with cols[i]:
                    st.markdown(f"""
                    <div style="background-color: {color}; padding: 10px; 
                        border-radius: 5px; text-align: center; color: white;">
                        <strong>{condition}</strong><br/>
                        {signal}
                    </div>
                    """, unsafe_allow_html=True)
            
            # 综合评分
            bullish_count = sum(1 for _, s, _ in signals if s == "看多")
            bearish_count = sum(1 for _, s, _ in signals if s == "看空")
            
            st.markdown("### 综合评估")
            total = bullish_count + bearish_count
            if total > 0:
                bullish_pct = bullish_count / total * 100
                st.progress(bullish_pct / 100)
                st.write(f"看多信号: {bullish_count} | 看空信号: {bearish_count}")

# ==================== 量化分析模块 ====================
elif main_module == "📐 量化分析 (Quantitative)":
    st.header("📐 量化分析")
    
    if obb is None:
        st.error("OpenBB未安装")
        st.stop()
    
    quant_tabs = st.tabs(["📊 统计分析", "📈 风险指标", "🔗 相关性分析"])
    
    with quant_tabs[0]:
        st.subheader("📊 收益率统计分析")
        
        quant_symbol = st.text_input("股票代码", value="QQQ", key="quant_symbol")
        
        if st.button("分析", key="quant_analyze"):
            try:
                data = obb.equity.price.historical(
                    quant_symbol,
                    start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                    provider="yfinance"
                ).to_df()
                
                if not data.empty:
                    returns = data['close'].pct_change().dropna()
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### 统计摘要")
                        stats = {
                            "年化收益率": f"{returns.mean() * 252 * 100:.2f}%",
                            "年化波动率": f"{returns.std() * (252**0.5) * 100:.2f}%",
                            "偏度": f"{returns.skew():.4f}",
                            "峰度": f"{returns.kurtosis():.4f}",
                            "最大日涨幅": f"{returns.max() * 100:.2f}%",
                            "最大日跌幅": f"{returns.min() * 100:.2f}%",
                        }
                        
                        for k, v in stats.items():
                            st.metric(k, v)
                    
                    with col2:
                        st.markdown("### 收益率分布")
                        fig = go.Figure()
                        fig.add_trace(go.Histogram(x=returns, nbinsx=50, name='Daily Returns'))
                        fig.update_layout(title="日收益率分布", height=400)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # 累计收益
                    st.markdown("### 累计收益")
                    cum_returns = (1 + returns).cumprod() - 1
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=cum_returns.index, y=cum_returns * 100,
                        fill='tozeroy', name='累计收益'))
                    fig.update_layout(yaxis_title="累计收益 (%)", height=400)
                    st.plotly_chart(fig, use_container_width=True)
                    
            except Exception as e:
                st.error(f"分析失败: {str(e)}")
    
    with quant_tabs[1]:
        st.subheader("📈 风险指标")
        
        risk_symbol = st.text_input("股票代码", value="QQQ", key="risk_symbol")
        risk_free = st.number_input("无风险利率 (%)", value=5.0, step=0.1) / 100
        
        if st.button("计算风险指标", key="risk_calc"):
            try:
                data = obb.equity.price.historical(
                    risk_symbol,
                    start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                    provider="yfinance"
                ).to_df()
                
                if not data.empty:
                    returns = data['close'].pct_change().dropna()
                    
                    # 计算风险指标
                    ann_return = returns.mean() * 252
                    ann_vol = returns.std() * (252**0.5)
                    sharpe = (ann_return - risk_free) / ann_vol
                    
                    # 最大回撤
                    cum_returns = (1 + returns).cumprod()
                    rolling_max = cum_returns.expanding().max()
                    drawdown = (cum_returns - rolling_max) / rolling_max
                    max_drawdown = drawdown.min()
                    
                    # Sortino (只考虑下行波动)
                    downside_returns = returns[returns < 0]
                    downside_vol = downside_returns.std() * (252**0.5)
                    sortino = (ann_return - risk_free) / downside_vol if downside_vol > 0 else 0
                    
                    # VaR (95%)
                    var_95 = returns.quantile(0.05)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("夏普比率", f"{sharpe:.2f}")
                        st.metric("Sortino比率", f"{sortino:.2f}")
                    
                    with col2:
                        st.metric("最大回撤", f"{max_drawdown*100:.2f}%")
                        st.metric("年化波动率", f"{ann_vol*100:.2f}%")
                    
                    with col3:
                        st.metric("VaR (95%)", f"{var_95*100:.2f}%")
                        st.metric("年化收益", f"{ann_return*100:.2f}%")
                    
                    # 回撤图
                    st.markdown("### 回撤曲线")
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=drawdown.index, y=drawdown * 100,
                        fill='tozeroy', name='回撤'))
                    fig.update_layout(yaxis_title="回撤 (%)", height=300)
                    st.plotly_chart(fig, use_container_width=True)
                    
            except Exception as e:
                st.error(f"计算失败: {str(e)}")
    
    with quant_tabs[2]:
        st.subheader("🔗 相关性分析")
        
        corr_symbols = st.text_input("输入多个代码(逗号分隔)", 
            value="QQQ,SPY,IWM,TLT,GLD", key="corr_symbols")
        
        if st.button("计算相关性", key="corr_calc"):
            symbols = [s.strip() for s in corr_symbols.split(",")]
            
            returns_dict = {}
            for sym in symbols:
                try:
                    data = obb.equity.price.historical(
                        sym,
                        start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                        provider="yfinance"
                    ).to_df()
                    if not data.empty:
                        returns_dict[sym] = data['close'].pct_change()
                except:
                    pass
            
            if len(returns_dict) > 1:
                returns_df = pd.DataFrame(returns_dict).dropna()
                corr_matrix = returns_df.corr()
                
                fig = px.imshow(corr_matrix, 
                    labels=dict(color="相关系数"),
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    color_continuous_scale="RdBu_r",
                    aspect="auto")
                fig.update_layout(title="相关性矩阵", height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(corr_matrix.round(3), use_container_width=True)

# ==================== 加密货币模块 ====================
elif main_module == "💎 加密货币 (Crypto)":
    st.header("💎 加密货币")
    
    if obb is None:
        st.error("OpenBB未安装")
        st.stop()
    
    crypto_tabs = st.tabs(["📊 价格查询", "🔍 搜索"])
    
    with crypto_tabs[0]:
        st.subheader("📊 加密货币价格")
        
        crypto_symbol = st.text_input("代码 (如BTC-USD)", value="BTC-USD", key="crypto_symbol")
        
        if st.button("查询", key="crypto_fetch"):
            try:
                data = obb.crypto.price.historical(crypto_symbol, provider="yfinance").to_df()
                
                if not data.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=data.index, open=data['open'], high=data['high'],
                        low=data['low'], close=data['close'], name=crypto_symbol
                    ))
                    fig.update_layout(title=f"{crypto_symbol} 价格", height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 统计
                    col1, col2, col3, col4 = st.columns(4)
                    latest = data.iloc[-1]
                    col1.metric("最新价", f"${latest['close']:,.2f}")
                    col2.metric("24h高", f"${latest['high']:,.2f}")
                    col3.metric("24h低", f"${latest['low']:,.2f}")
                    col4.metric("成交量", f"{latest['volume']:,.0f}")
                    
            except Exception as e:
                st.error(f"获取数据失败: {str(e)}")
    
    with crypto_tabs[1]:
        st.subheader("🔍 搜索加密货币")
        
        search_query = st.text_input("搜索", value="bitcoin", key="crypto_search")
        
        if st.button("搜索", key="crypto_search_btn"):
            try:
                results = obb.crypto.search(search_query).to_df()
                if not results.empty:
                    st.dataframe(results, use_container_width=True)
            except Exception as e:
                st.info(f"搜索功能需要配置数据源: {str(e)}")

# ==================== 新闻模块 ====================
elif main_module == "📰 新闻 (News)":
    st.header("📰 市场新闻")
    
    if obb is None:
        st.error("OpenBB未安装")
        st.stop()
    
    news_tabs = st.tabs(["🌍 全球新闻", "🏢 公司新闻"])
    
    with news_tabs[0]:
        st.subheader("🌍 全球市场新闻")
        st.info("新闻功能需要配置新闻API密钥 (如Benzinga, Polygon等)")
        
        st.code("""
# 获取市场新闻
from openbb import obb
news = obb.news.world(provider="benzinga")  # 需要API密钥
        """)
    
    with news_tabs[1]:
        st.subheader("🏢 公司新闻")
        
        news_symbol = st.text_input("股票代码", value="AAPL", key="news_symbol")
        
        st.code(f"""
# 获取{news_symbol}相关新闻
from openbb import obb
news = obb.news.company("{news_symbol}", provider="benzinga")  # 需要API密钥
        """)

# ==================== 大宗商品模块 ====================
elif main_module == "🛢️ 大宗商品 (Commodity)":
    st.header("🛢️ 大宗商品")
    
    if obb is None:
        st.error("OpenBB未安装")
        st.stop()
    
    st.subheader("主要商品价格")
    
    commodities = {
        "原油 (WTI)": "CL=F",
        "黄金": "GC=F",
        "白银": "SI=F",
        "天然气": "NG=F",
        "铜": "HG=F",
        "玉米": "ZC=F"
    }
    
    selected_commodity = st.selectbox("选择商品", list(commodities.keys()))
    symbol = commodities[selected_commodity]
    
    if st.button("查询价格", key="commodity_fetch"):
        try:
            data = obb.equity.price.historical(
                symbol,
                start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                provider="yfinance"
            ).to_df()
            
            if not data.empty:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=data.index, open=data['open'], high=data['high'],
                    low=data['low'], close=data['close'], name=selected_commodity
                ))
                fig.update_layout(title=f"{selected_commodity} 价格走势", height=500)
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"获取数据失败: {str(e)}")

# ==================== 固定收益模块 ====================
elif main_module == "🏛️ 固定收益 (Fixed Income)":
    st.header("🏛️ 固定收益")
    
    if obb is None:
        st.error("OpenBB未安装")
        st.stop()
    
    fi_tabs = st.tabs(["📈 国债收益率", "📊 收益率曲线"])
    
    with fi_tabs[0]:
        st.subheader("📈 美国国债收益率")
        
        # 国债ETF代理
        treasury_etfs = {
            "短期 (1-3年)": "SHY",
            "中期 (7-10年)": "IEF",
            "长期 (20+年)": "TLT"
        }
        
        if st.button("加载国债数据", key="treasury_fetch"):
            fig = go.Figure()
            
            for name, etf in treasury_etfs.items():
                try:
                    data = obb.equity.price.historical(
                        etf,
                        start_date=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                        provider="yfinance"
                    ).to_df()
                    
                    if not data.empty:
                        normalized = data['close'] / data['close'].iloc[0] * 100
                        fig.add_trace(go.Scatter(x=data.index, y=normalized, name=f"{name} ({etf})"))
                except:
                    pass
            
            fig.update_layout(title="国债ETF走势对比", yaxis_title="标准化价格", height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    with fi_tabs[1]:
        st.subheader("📊 美国国债收益率曲线")
        st.info("完整收益率曲线数据需要配置FRED API密钥")
        
        st.code("""
# 获取收益率曲线
from openbb import obb
curve = obb.fixedincome.rate.treasury(provider="fred")  # 需要API密钥
        """)

# ==================== 监管数据模块 ====================
elif main_module == "📋 监管数据 (Regulators)":
    st.header("📋 监管数据 (SEC)")
    
    if obb is None:
        st.error("OpenBB未安装")
        st.stop()
    
    st.subheader("SEC数据查询")
    
    sec_symbol = st.text_input("公司代码", value="AAPL", key="sec_symbol")
    
    filing_type = st.selectbox("文件类型", ["10-K", "10-Q", "8-K", "13F"])
    
    st.code(f"""
# 查询SEC文件
from openbb import obb
filings = obb.regulators.sec.filings("{sec_symbol}", form_type="{filing_type}")
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
### 📚 资源链接
- [OpenBB文档](https://docs.openbb.co)
- [OpenBB GitHub](https://github.com/OpenBB-finance/OpenBB)
- [API密钥配置](https://docs.openbb.co/python/settings)
""")

st.sidebar.markdown("---")
st.sidebar.info("部分功能需要配置数据源API密钥才能使用完整功能")
