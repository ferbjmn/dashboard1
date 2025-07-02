import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
import time
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="📊 Dashboard Financiero Avanzado",
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# Parámetros iniciales WACC
Rf = 0.0435  # Tasa libre de riesgo
Rm = 0.085   # Retorno esperado del mercado
Tc = 0.21    # Tasa impositiva corporativa

# Funciones de cálculo
def calcular_wacc(info, balance_sheet):
    try:
        beta = info.get("beta", 1.0)
        price = info.get("currentPrice")
        shares = info.get("sharesOutstanding")
        market_cap = price * shares if price and shares else None
        
        # Manejo de deuda
        lt_debt = balance_sheet.loc["Long Term Debt"].iloc[0] if "Long Term Debt" in balance_sheet.index else 0
        st_debt = balance_sheet.loc["Short Term Debt"].iloc[0] if "Short Term Debt" in balance_sheet.index else 0
        total_debt = lt_debt + st_debt
        
        Re = Rf + beta * (Rm - Rf)  # Costo de capital
        Rd = 0.055  # Se optimizó en función de la deuda

        E = market_cap  # Valor de mercado del equity
        D = total_debt  # Valor de mercado de la deuda

        if None in [Re, E, D] or E + D == 0:
            return None, total_debt

        # Ajuste de Rd en función del tamaño de la deuda
        if D > 0:
            Rd = 0.05 if D < 1_000_000_000 else 0.06
        
        wacc = (E / (E + D)) * Re + (D / (E + D)) * Rd * (1 - Tc)
        return wacc, total_debt
    except Exception as e:
        st.error(f"Error calculando WACC: {str(e)}")
        return None, None

def calcular_crecimiento_historico(financials, metric):
    try:
        if metric not in financials.index:
            return None
            
        datos = financials.loc[metric].dropna().iloc[:4]  # Últimos 4 periodos
        if len(datos) < 2:
            return None
            
        primer_valor = datos.iloc[-1]
        ultimo_valor = datos.iloc[0]
        años = len(datos) - 1
        
        if primer_valor == 0:
            return None
            
        cagr = (ultimo_valor / primer_valor) ** (1 / años) - 1
        return cagr
    except:
        return None

def obtener_datos_financieros(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        bs = stock.balance_sheet
        fin = stock.financials
        cf = stock.cashflow

        # Datos básicos
        price = info.get("currentPrice", None)
        name = info.get("longName", ticker)
        sector = info.get("sector", "N/D")
        country = info.get("country", "N/D")
        industry = info.get("industry", "N/D")

        # Ratios de valoración
        pe = info.get("trailingPE", None)
        pb = info.get("priceToBook", None)
        dividend = info.get("dividendRate", None)
        dividend_yield = info.get("dividendYield", None)
        payout = info.get("payoutRatio", None)
        
        # Ratios de rentabilidad
        roa = info.get("returnOnAssets", None)
        roe = info.get("returnOnEquity", None)
        
        # Ratios de liquidez
        current_ratio = info.get("currentRatio", None)
        quick_ratio = info.get("quickRatio", None)
        
        # Ratios de deuda
        ltde = info.get("longTermDebtToEquity", None)
        de = info.get("debtToEquity", None)
        
        # Margenes
        op_margin = info.get("operatingMargins", None)
        profit_margin = info.get("profitMargins", None)
        
        # Flujo de caja
        fcf = cf.loc["Free Cash Flow"].iloc[0] if "Free Cash Flow" in cf.index else None
        shares = info.get("sharesOutstanding", None)
        pfcf = price / (fcf / shares) if fcf and shares else None
        
        # Cálculos avanzados
        ebit = fin.loc["EBIT"].iloc[0] if "EBIT" in fin.index else None
        equity = bs.loc["Total Stockholder Equity"].iloc[0] if "Total Stockholder Equity" in bs.index else None
        wacc, total_debt = calcular_wacc(info, bs)
        capital_invertido = total_debt + equity if total_debt and equity else None
        roic = ebit * (1 - Tc) / capital_invertido if ebit and capital_invertido else None
        eva = (roic - wacc) * capital_invertido if roic and wacc and capital_invertido else None
        
        # Crecimientos
        revenue_growth = calcular_crecimiento_historico(fin, "Total Revenue")
        eps_growth = calcular_crecimiento_historico(fin, "Net Income")
        fcf_growth = calcular_crecimiento_historico(cf, "Free Cash Flow") or calcular_crecimiento_historico(cf, "Operating Cash Flow")
        
        # Liquidez avanzada
        cash_ratio = info.get("cashRatio", None)
        operating_cash_flow = cf.loc["Operating Cash Flow"].iloc[0] if "Operating Cash Flow" in cf.index else None
        current_liabilities = bs.loc["Total Current Liabilities"].iloc[0] if "Total Current Liabilities" in bs.index else None
        cash_flow_ratio = operating_cash_flow / current_liabilities if operating_cash_flow and current_liabilities else None
        
        return {
            "Ticker": ticker,
            "Nombre": name,
            "Sector": sector,
            "País": country,
            "Industria": industry,
            "Precio": price,
            "P/E": pe,
            "P/B": pb,
            "P/FCF": pfcf,
            "Dividend Year": dividend,
            "Dividend Yield %": dividend_yield,
            "Payout Ratio": payout,
            "ROA": roa,
            "ROE": roe,
            "Current Ratio": current_ratio,
            "Quick Ratio": quick_ratio,
            "LtDebt/Eq": ltde,
            "Debt/Eq": de,
            "Oper Margin": op_margin,
            "Profit Margin": profit_margin,
            "WACC": wacc,
            "ROIC": roic,
            "EVA": eva,
            "Deuda Total": total_debt,
            "Patrimonio Neto": equity,
            "Revenue Growth": revenue_growth,
            "EPS Growth": eps_growth,
            "FCF Growth": fcf_growth,
            "Cash Ratio": cash_ratio,
            "Cash Flow Ratio": cash_flow_ratio,
            "Operating Cash Flow": operating_cash_flow,
            "Current Liabilities": current_liabilities,
        }
    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

# Función para formatear columnas
def formatear_columnas(df):
    # Formatear valores numéricos
    df["Precio"] = df["Precio"].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/D")
    
    # Formatear columnas porcentuales
    porcentajes = ["Dividend Yield %", "ROA", "ROE", "Oper Margin", "Profit Margin", "WACC", "ROIC", "EVA"]
    for col in porcentajes:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/D")
    
    return df

# Interfaz de usuario
def main():
    st.title("📊 Dashboard de Análisis Financiero Avanzado")
    
    # Sidebar con configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        tickers_input = st.text_area(
            "🔎 Ingresa tickers (separados por coma)", 
            "AAPL, MSFT, GOOGL, AMZN, TSLA",
            help="Ejemplo: AAPL, MSFT, GOOG"
        )
        max_tickers = st.slider("Número máximo de tickers", 1, 100, 10)
        
        st.markdown("---")
        st.markdown("**Parámetros WACC**")
        global Rf, Rm, Tc
        Rf = st.number_input("Tasa libre de riesgo (%)", min_value=0.0, max_value=20.0, value=4.35) / 100
        Rm = st.number_input("Retorno esperado del mercado (%)", min_value=0.0, max_value=30.0, value=8.5) / 100
        Tc = st.number_input("Tasa impositiva corporativa (%)", min_value=0.0, max_value=50.0, value=21.0) / 100
    
    # Procesamiento de tickers
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()][:max_tickers]
    
    if st.button("🔍 Analizar Acciones", type="primary"):
        if not tickers:
            st.warning("Por favor ingresa al menos un ticker")
            return
            
        resultados = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, t in enumerate(tickers):
            status_text.text(f"⏳ Procesando {t} ({i+1}/{len(tickers)})...")
            resultados[t] = obtener_datos_financieros(t)
            progress_bar.progress((i + 1) / len(tickers))
            time.sleep(1)  # Para evitar bloqueos de la API
            
        status_text.text("✅ Análisis completado!")
        time.sleep(0.5)
        status_text.empty()
        progress_bar.empty()
        
        # Mostrar resultados
        if resultados:
            datos = list(resultados.values())
            
            # Filtramos empresas con errores
            datos_validos = [d for d in datos if "Error" not in d]
            if not datos_validos:
                st.error("No se pudo obtener datos válidos para ningún ticker")
                return
                
            df = pd.DataFrame(datos_validos)
            df = formatear_columnas(df)
            
            # Sección 1: Resumen General
            st.header("📋 Resumen General")
            st.dataframe(
                df.dropna(how='all', axis=1),
                use_container_width=True,
                height=400
            )
            
            # Continuar con las secciones de gráficos y análisis...
            
if __name__ == "__main__":
    main()
