import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import graficos as g

if __name__ == "__main__":

    st.set_page_config(
        page_title="App revenue Dashboard",
        page_icon="📊",
        layout="wide"
    )

    # para no volver a cargar el dataset cada vez que se cambie algun control, lo cual tarda demasiado
    if 'apk_data' not in st.session_state:
       st.session_state['apk_data'] = g.load_preprocess_data()

    apk_data = st.session_state['apk_data']

    apk_paid_data = g.calculate_estimated_revenue(apk_data)

    if 'categories' not in st.session_state:
       st.session_state['categories'] = g.get_categories(apk_paid_data)

    if 'developers' not in st.session_state:
       st.session_state['developers'] = g.get_developers(apk_paid_data)


    if 'applications_privacy_policy' not in st.session_state:
       st.session_state['applications_privacy_policy'] = g.get_apps_wordcloud(apk_data, "Privacy policy")

    if 'applications_service_terms' not in st.session_state:
       st.session_state['applications_service_terms'] = g.get_apps_wordcloud(apk_data, "Service terms")

    st.sidebar.header("Dashboard Filters")
    selected_category = st.sidebar.selectbox(
        "Select Category",
        options=['All'] + list(st.session_state['categories'])
    )

    if selected_category == 'All':
        selected_category = None

    selected_developer = st.sidebar.selectbox(
        "Select Developer",
        options=['All'] + list(st.session_state['developers'])
    )

    if selected_developer == 'All':
        selected_developer = None

    selected_revenue_by_minimum_android_operation = st.sidebar.selectbox(
        "Select revenue by minimum android version aggregation",
        options=['Sum', 'Mean']
    )

    selected_revenue_by_category_operation = st.sidebar.selectbox(
        "Select revenue by category aggregation",
        options=['Sum', 'Mean']
    )

    selected_revenue_by_content_rating_operation = st.sidebar.selectbox(
        "Select revenue by content rating aggregation",
        options=['Sum', 'Mean']
    )


    selected_type_wordcloud = st.sidebar.selectbox(
        "Select type for wordcloud",
        options=["Privacy policy", "Service terms"]
    )

    selected_application_wordcloud = st.sidebar.selectbox(
        "Select application for wordcloud",
        options=['All'] + list(st.session_state['applications_privacy_policy' if selected_type_wordcloud == "Privacy policy" else "applications_service_terms"])
    )

    if selected_application_wordcloud == 'All':
        selected_application_wordcloud = None

    st.title("📊 App revenue Dashboard")
    st.markdown("Revenue analytics for mobile applications.")

    # renderizar los datos en dos columnas
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.altair_chart(g.free_paid_apps_chart(apk_data), width="stretch")
        st.altair_chart(g.revenue_rating_relation_chart(apk_paid_data), width="stretch")
        st.altair_chart(g.revenue_minimum_android_relation_chart(apk_paid_data, selected_revenue_by_minimum_android_operation), width="stretch")
        st.altair_chart(g.revenue_by_content_rating(apk_paid_data, selected_revenue_by_content_rating_operation), width="stretch")
        st.pyplot(g.generate_wordcloud(apk_data, app_name = selected_application_wordcloud, text_type = selected_type_wordcloud), width="stretch")

    with chart_col2:
        st.altair_chart(g.most_revenue_chart(apk_paid_data, selected_category, selected_developer), width="stretch")
        st.altair_chart(g.category_revenues_chart(apk_paid_data, selected_revenue_by_category_operation), width="stretch")
        st.altair_chart(g.revenue_by_category_and_rating(apk_paid_data), width="stretch")
        st.altair_chart(g.permission_count(apk_data), width="stretch")



