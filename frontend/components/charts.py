import streamlit as st
import plotly.graph_objects as go


def render_chart(fig_json: dict | None):
    if not fig_json:
        return
    fig = go.Figure(fig_json)
    st.plotly_chart(fig, use_container_width=True)
