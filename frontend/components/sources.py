import streamlit as st


def render_sources(citations: list[dict]):
    if not citations:
        st.info("Aucune source pour l'instant.")
        return

    st.subheader("Sources")
    for c in citations:
        institution = c.get("institution", "?")
        report = c.get("report_name", "?")
        year = c.get("year", "?")
        page = c.get("page", "?")
        url = c.get("url")

        label = f"**{institution}** — {report} ({year}), p.{page}"
        if url:
            st.markdown(f"- [{label}]({url})")
        else:
            st.markdown(f"- {label}")
