# 🏦 OpenBB Streamlit 可视化平台

将 OpenBB 金融数据平台的所有功能可视化到 Streamlit 界面，点击即可使用。

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![OpenBB](https://img.shields.io/badge/OpenBB-4.0+-green.svg)

## 📋 功能模块

| 模块 | 功能 | 数据源 |
|------|------|--------|
| 📈 股票 (Equity) | 历史价格、筛选器、公司信息、基本面、空头数据 | yfinance (免费), FMP, Polygon |
| 🎯 衍生品 (Derivatives) | 期权链、Greeks、IV曲面、异常活动 | yfinance (免费), CBOE |
| 💰 ETF | 持仓分析、行业分布、业绩对比 | yfinance (免费), FMP |
| 📊 指数 (Index) | 成分股、历史数据 | yfinance (免费) |
| 🌍 经济数据 (Economy) | CPI、GDP、就业、利率 | FRED, OECD |
| 💵 外汇 (Currency) | 实时汇率、历史走势 | yfinance (免费) |
| 🔧 技术分析 (Technical) | MA、RSI、MACD、布林带、ATR | 内置计算 |
| 📐 量化分析 (Quantitative) | 夏普比率、VaR、回撤、相关性 | 内置计算 |
| 💎 加密货币 (Crypto) | 价格、搜索 | yfinance (免费) |
| 📰 新闻 (News) | 全球新闻、公司新闻 | Benzinga, Polygon |
| 🛢️ 大宗商品 (Commodity) | 原油、黄金、农产品 | yfinance (免费) |
| 🏛️ 固定收益 (Fixed Income) | 国债、收益率曲线 | FRED |
| 📋 监管数据 (Regulators) | SEC文件 | SEC |

## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境 (推荐)
python -m venv openbb_env
source openbb_env/bin/activate  # Linux/Mac
# openbb_env\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 或者安装完整版OpenBB (包含所有数据源)
pip install "openbb[all]"
```

### 2. 配置API密钥 (可选但推荐)

某些数据源需要API密钥。在Python中配置：

```python
from openbb import obb

# 设置API密钥
obb.user.credentials.fmp_api_key = "YOUR_FMP_KEY"
obb.user.credentials.polygon_api_key = "YOUR_POLYGON_KEY"
obb.user.credentials.fred_api_key = "YOUR_FRED_KEY"

# 或者通过环境变量
# export OPENBB_FMP_API_KEY=your_key
```

**免费API密钥获取:**
- [FMP](https://financialmodelingprep.com/) - 免费tier可用
- [Polygon](https://polygon.io/) - 免费tier可用
- [FRED](https://fred.stlouisfed.org/docs/api/api_key.html) - 免费
- [Alpha Vantage](https://www.alphavantage.co/) - 免费

### 3. 运行应用

```bash
streamlit run app.py
```

应用将在 `http://localhost:8501` 启动

## 📊 使用说明

### 免费功能 (无需API密钥)
使用 `yfinance` 数据源，以下功能开箱即用：
- 股票历史价格和K线图
- 期权链查询
- ETF信息和持仓
- 外汇汇率
- 加密货币价格
- 大宗商品价格
- 技术分析指标
- 量化风险分析

### 需要API密钥的功能
- 详细公司基本面数据 (FMP)
- 实时新闻 (Benzinga)
- 完整经济数据 (FRED)
- 高级期权数据 (CBOE)

## 🎯 特别针对QQQ期权交易的功能

本平台特别优化了期权交易分析功能：

### 期权链分析
- 实时查看 QQQ/SPY 期权链
- Call/Put 持仓量可视化
- 按到期日筛选

### Gamma分析集成建议
如果需要更专业的GEX分析，可以：
1. 集成SpotGamma数据API
2. 使用本平台导出的期权数据进行自定义计算

## 🛠️ 自定义扩展

### 添加新的数据模块

```python
# 在app.py中添加新模块
elif main_module == "🆕 新模块":
    st.header("新功能模块")
    
    # 使用OpenBB获取数据
    data = obb.your_module.your_function()
    
    # 可视化
    st.plotly_chart(fig)
```

### 添加新的数据源

```python
# 安装新的provider
pip install openbb-newprovider

# 在代码中使用
data = obb.equity.price.historical("AAPL", provider="newprovider")
```

## 📁 项目结构

```
openbb_streamlit/
├── app.py              # 主应用文件
├── requirements.txt    # 依赖列表
├── README.md           # 说明文档
└── pages/              # (可选) 多页面应用
    ├── 1_equity.py
    ├── 2_options.py
    └── ...
```

## 🔧 性能优化

### 数据缓存
应用使用 `@st.cache_data` 缓存数据请求，避免重复API调用：

```python
@st.cache_data(ttl=300)  # 缓存5分钟
def get_data(symbol):
    return obb.equity.price.historical(symbol).to_df()
```

### 部署建议
- 使用 Streamlit Cloud 免费部署
- 或使用 Docker 容器化部署
- 配置环境变量存储API密钥

## 📚 相关资源

- [OpenBB 官方文档](https://docs.openbb.co)
- [OpenBB GitHub](https://github.com/OpenBB-finance/OpenBB)
- [Streamlit 文档](https://docs.streamlit.io)
- [Plotly 文档](https://plotly.com/python/)

## ⚠️ 免责声明

本工具仅供学习和研究使用。金融市场有风险，投资需谨慎。本工具提供的数据和分析不构成投资建议。

## 📄 License

MIT License
