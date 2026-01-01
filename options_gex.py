"""
OpenBB Options & GEX Analysis Module
专门针对期权交易和Gamma分析的高级功能
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

# 页面配置
st.set_page_config(
    page_title="期权 & GEX 分析",
    page_icon="🎯",
    layout="wide"
)

# 初始化OpenBB
@st.cache_resource
def init_openbb():
    try:
        from openbb import obb
        return obb
    except ImportError:
        return None

obb = init_openbb()

# ==================== Black-Scholes Greeks 计算 ====================
def black_scholes_greeks(S, K, T, r, sigma, option_type='call'):
    """计算期权Greeks"""
    if T <= 0:
        T = 0.001
    
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    
    if option_type == 'call':
        delta = norm.cdf(d1)
        theta = (-S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) - r*K*np.exp(-r*T)*norm.cdf(d2)) / 365
    else:
        delta = norm.cdf(d1) - 1
        theta = (-S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) + r*K*np.exp(-r*T)*norm.cdf(-d2)) / 365
    
    gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
    vega = S * norm.pdf(d1) * np.sqrt(T) / 100
    
    return {'delta': delta, 'gamma': gamma, 'theta': theta, 'vega': vega}

def calculate_gex(row, spot_price, contract_size=100):
    """计算单个行权价的GEX"""
    try:
        K = row['strike']
        oi = row.get('open_interest', 0) or 0
        iv = row.get('implied_volatility', 0.3) or 0.3
        
        if 'expiration' in row:
            exp_date = pd.to_datetime(row['expiration'])
            T = max((exp_date - datetime.now()).days / 365, 0.001)
        else:
            T = 30 / 365
        
        greeks = black_scholes_greeks(spot_price, K, T, 0.05, iv, row.get('option_type', 'call'))
        gex = greeks['gamma'] * oi * spot_price**2 * contract_size * 0.01
        
        if row.get('option_type', 'call') == 'put':
            gex = -gex
            
        return gex
    except:
        return 0

# ==================== 主界面 ====================
st.title("🎯 期权 & Gamma分析平台")

if obb is None:
    st.error("⚠️ OpenBB未安装！请运行: `pip install openbb`")
    st.stop()

# Sidebar配置
st.sidebar.header("⚙️ 分析配置")

symbols = st.sidebar.multiselect(
    "选择标的",
    ["QQQ", "SPY", "IWM", "DIA"],
    default=["QQQ"]
)

analysis_type = st.sidebar.selectbox(
    "分析类型",
    ["📊 期权链分析", "🎯 GEX分析", "📈 综合战场图", "🔧 Greeks计算器"]
)

# ==================== 期权链分析 ====================
if analysis_type == "📊 期权链分析":
    st.header("📊 期权链深度分析")
    
    for symbol in symbols:
        st.subheader(f"🏷️ {symbol}")
        
        try:
            with st.spinner(f"加载 {symbol} 期权链..."):
                chains = obb.derivatives.options.chains(symbol, provider="yfinance").to_df()
            
            if chains.empty:
                st.warning(f"{symbol} 无期权数据")
                continue
            
            price_data = obb.equity.price.historical(symbol, provider="yfinance").to_df()
            spot_price = price_data['close'].iloc[-1] if not price_data.empty else 500
            
            st.metric(f"{symbol} 现价", f"${spot_price:.2f}")
            
            if 'expiration' in chains.columns:
                expirations = sorted(chains['expiration'].unique())
                selected_exp = st.selectbox(f"到期日 ({symbol})", expirations[:10], key=f"exp_{symbol}")
                
                exp_data = chains[chains['expiration'] == selected_exp].copy()
                dte = (pd.to_datetime(selected_exp) - datetime.now()).days
                
                if 'option_type' in exp_data.columns:
                    calls = exp_data[exp_data['option_type'] == 'call'].copy()
                    puts = exp_data[exp_data['option_type'] == 'put'].copy()
                else:
                    calls, puts = exp_data, pd.DataFrame()
                
                # OI分布图
                fig = go.Figure()
                
                if not calls.empty and 'open_interest' in calls.columns:
                    fig.add_trace(go.Bar(x=calls['strike'], y=calls['open_interest'],
                        name='Calls OI', marker_color='rgba(0, 255, 0, 0.6)'))
                
                if not puts.empty and 'open_interest' in puts.columns:
                    fig.add_trace(go.Bar(x=puts['strike'], y=-puts['open_interest'],
                        name='Puts OI', marker_color='rgba(255, 0, 0, 0.6)'))
                
                fig.add_vline(x=spot_price, line_dash="dash", line_color="yellow",
                             annotation_text=f"现价: ${spot_price:.2f}")
                
                fig.update_layout(title=f"{symbol} OI分布 (DTE: {dte}天)", height=500, barmode='relative')
                st.plotly_chart(fig, use_container_width=True)
                
                # 关键位置
                col1, col2, col3 = st.columns(3)
                if not calls.empty and 'open_interest' in calls.columns and calls['open_interest'].max() > 0:
                    call_wall = calls.loc[calls['open_interest'].idxmax(), 'strike']
                    col1.metric("📈 Call Wall", f"${call_wall:.2f}")
                if not puts.empty and 'open_interest' in puts.columns and puts['open_interest'].max() > 0:
                    put_wall = puts.loc[puts['open_interest'].idxmax(), 'strike']
                    col2.metric("📉 Put Wall", f"${put_wall:.2f}")
                
        except Exception as e:
            st.error(f"获取 {symbol} 数据失败: {str(e)}")

# ==================== GEX分析 ====================
elif analysis_type == "🎯 GEX分析":
    st.header("🎯 Gamma Exposure (GEX) 分析")
    
    st.info("""
    **GEX分析:**
    - 正Gamma: 做市商对冲抑制波动，均值回归
    - 负Gamma: 做市商对冲放大波动，趋势性强
    - Zero Gamma: Gamma转换点
    """)
    
    for symbol in symbols:
        st.subheader(f"🎯 {symbol} GEX")
        
        try:
            chains = obb.derivatives.options.chains(symbol, provider="yfinance").to_df()
            price_data = obb.equity.price.historical(symbol, provider="yfinance").to_df()
            
            if chains.empty:
                continue
            
            spot_price = price_data['close'].iloc[-1] if not price_data.empty else 500
            
            if 'expiration' in chains.columns:
                expirations = sorted(chains['expiration'].unique())[:5]
                selected_exps = st.multiselect(f"到期日 ({symbol})", expirations,
                    default=[expirations[0]] if expirations else [], key=f"gex_{symbol}")
                
                if not selected_exps:
                    continue
                
                exp_data = chains[chains['expiration'].isin(selected_exps)].copy()
                exp_data['gex'] = exp_data.apply(lambda row: calculate_gex(row, spot_price), axis=1)
                
                gex_by_strike = exp_data.groupby('strike')['gex'].sum().reset_index()
                total_gex = gex_by_strike['gex'].sum()
                
                # Zero Gamma估算
                gex_by_strike['cumsum'] = gex_by_strike['gex'].cumsum()
                zero_gamma_idx = (gex_by_strike['cumsum'].abs()).idxmin()
                zero_gamma = gex_by_strike.loc[zero_gamma_idx, 'strike']
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("现价", f"${spot_price:.2f}")
                col2.metric("Net GEX", f"{total_gex/1e9:.2f}B")
                col3.metric("Zero Gamma", f"${zero_gamma:.2f}")
                col4.metric("环境", "正Gamma" if spot_price > zero_gamma else "负Gamma")
                
                # GEX图
                fig = go.Figure()
                colors = ['green' if g > 0 else 'red' for g in gex_by_strike['gex']]
                fig.add_trace(go.Bar(x=gex_by_strike['strike'], y=gex_by_strike['gex']/1e6, marker_color=colors))
                fig.add_vline(x=spot_price, line_dash="dash", line_color="yellow")
                fig.add_vline(x=zero_gamma, line_dash="dot", line_color="white")
                fig.update_layout(title=f"{symbol} GEX (百万$)", height=500)
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"GEX计算失败: {str(e)}")

# ==================== 综合战场图 ====================
elif analysis_type == "📈 综合战场图":
    st.header("📈 多品种Gamma战场图")
    
    summary_data = []
    
    for symbol in symbols:
        try:
            chains = obb.derivatives.options.chains(symbol, provider="yfinance").to_df()
            price_data = obb.equity.price.historical(symbol, provider="yfinance").to_df()
            
            if chains.empty or price_data.empty:
                continue
            
            spot = price_data['close'].iloc[-1]
            
            if 'expiration' in chains.columns:
                nearest_exp = sorted(chains['expiration'].unique())[0]
                exp_data = chains[chains['expiration'] == nearest_exp]
                
                if 'option_type' in exp_data.columns and 'open_interest' in exp_data.columns:
                    calls = exp_data[exp_data['option_type'] == 'call']
                    puts = exp_data[exp_data['option_type'] == 'put']
                    
                    call_wall = calls.loc[calls['open_interest'].idxmax(), 'strike'] if not calls.empty and calls['open_interest'].max() > 0 else None
                    put_wall = puts.loc[puts['open_interest'].idxmax(), 'strike'] if not puts.empty and puts['open_interest'].max() > 0 else None
                    zero_gamma = (call_wall + put_wall) / 2 if call_wall and put_wall else spot
                    
                    summary_data.append({
                        '品种': symbol,
                        '现价': f"${spot:.2f}",
                        'Zero Gamma': f"${zero_gamma:.2f}",
                        'Call Wall': f"${call_wall:.2f}" if call_wall else "N/A",
                        'Put Wall': f"${put_wall:.2f}" if put_wall else "N/A",
                        'Gamma环境': "正" if spot > zero_gamma else "负"
                    })
        except:
            pass
    
    if summary_data:
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

# ==================== Greeks计算器 ====================
elif analysis_type == "🔧 Greeks计算器":
    st.header("🔧 期权Greeks计算器")
    
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
            greeks = black_scholes_greeks(S, K, T_days/365, r, sigma, opt_type)
            
            c1, c2 = st.columns(2)
            c1.metric("Delta", f"{greeks['delta']:.4f}")
            c1.metric("Gamma", f"{greeks['gamma']:.6f}")
            c2.metric("Theta", f"{greeks['theta']:.4f}")
            c2.metric("Vega", f"{greeks['vega']:.4f}")
            
            # Delta曲线
            prices = np.linspace(S * 0.8, S * 1.2, 50)
            deltas = [black_scholes_greeks(p, K, T_days/365, r, sigma, opt_type)['delta'] for p in prices]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=prices, y=deltas, name='Delta'))
            fig.add_vline(x=S, line_dash="dash")
            fig.update_layout(title="Delta vs 价格", height=400)
            st.plotly_chart(fig, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info("注意: 完整GEX数据需要SpotGamma等专业数据源")
