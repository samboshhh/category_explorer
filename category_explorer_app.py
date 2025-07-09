
# --- 📊 Category Explorer Dashboard ---
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Category Explorer", layout="wide")

# --- 📥 Upload your data ---
st.title("💳 Category & Merchant Explorer")

uploaded_file = st.file_uploader("Upload your transaction CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.lower()
    df['amount_abs'] = df['amount'].abs()
    df = df[df['enrichment_categories'].notna()]

    # --- 🧼 Clean & Filter ---
    excluded = ['intra account transfer', 'inter account transfer', 'not enough information', 'peer to peer transfer']
    df = df[~df['enrichment_categories'].str.lower().isin(excluded)]

    # --- 🔁 Outgoings toggle ---
    show_incomings = st.checkbox("Include incoming transactions (positive amounts)?", value=False)
    if not show_incomings:
        df = df[df['amount'] < 0]

    # --- 📊 Top categories ---
    cat_summary = (
        df.groupby('enrichment_categories')
        .agg(
            txn_count=('id', 'count'),
            total_spend=('amount_abs', 'sum'),
            avg_txn=('amount_abs', 'mean')
        )
        .sort_values(by='total_spend', ascending=False)
        .head(50)
        .reset_index()
    )

    st.subheader("💡 Top Categories by Spend")
    fig = px.scatter(
        cat_summary,
        x='txn_count',
        y='total_spend',
        size='total_spend',
        color='enrichment_categories',
        hover_data=['avg_txn'],
        labels={'txn_count': 'Transactions', 'total_spend': 'Total Spend (£)', 'avg_txn': 'Avg Txn (£)'},
        title='Top 50 Spending Categories'
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- 🛍️ Category Drilldown ---
    st.subheader("📂 Category Drilldown")
    selected_category = st.selectbox("Choose a category", options=cat_summary['enrichment_categories'])
    filtered = df[df['enrichment_categories'] == selected_category]

    merchant_summary = (
        filtered.groupby('enrichment_merchant_name')
        .agg(total_spend=('amount_abs', 'sum'), txn_count=('id', 'count'))
        .sort_values(by='total_spend', ascending=False)
        .head(20)
        .reset_index()
    )

    merchant_summary['label'] = merchant_summary.apply(
        lambda row: f"£{row['total_spend']:,.0f} ({row['txn_count']} txns)", axis=1
    )

    fig_bar = px.bar(
        merchant_summary,
        x='total_spend',
        y='enrichment_merchant_name',
        orientation='h',
        text='label',
        labels={'total_spend': 'Total Spend (£)', 'enrichment_merchant_name': 'Merchant'},
        title=f"Top Merchants in {selected_category}"
    )
    fig_bar.update_traces(textposition='outside')
    fig_bar.update_layout(yaxis=dict(categoryorder='total ascending'), height=500)
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- 🔍 Merchant Search ---
    st.subheader("🔎 Merchant Search")
    query = st.text_input("Search merchant name:")
    if query:
        matches = df[df['enrichment_merchant_name'].str.lower().str.contains(query.lower(), na=False)]
        if not matches.empty:
            merchant_view = (
                matches.groupby('enrichment_categories')
                .agg(txn_count=('id', 'count'), total_spend=('amount_abs', 'sum'))
                .sort_values(by='total_spend', ascending=False)
                .reset_index()
            )

            fig_search = px.bar(
                merchant_view,
                x='total_spend',
                y='enrichment_categories',
                orientation='h',
                text='txn_count',
                labels={'total_spend': 'Total Spend (£)', 'txn_count': 'Transactions'},
                title=f"Spend Breakdown for '{query.title()}'"
            )
            fig_search.update_traces(texttemplate='%{text} txns', textposition='outside')
            fig_search.update_layout(height=400)
            st.plotly_chart(fig_search, use_container_width=True)

            st.dataframe(merchant_view.style.format({'total_spend': '£{:,.2f}'}))
        else:
            st.warning(f"No results found for '{query}'.")

else:
    st.info("⬆️ Please upload a CSV to get started.")
