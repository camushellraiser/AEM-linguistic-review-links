import streamlit as st
import pandas as pd
import io
import re

# Mapping from locale to region path
LOCALE_TO_PATH = {
    "zh-TW": "ipac/en-tw",
    "en-US": "latin-america/en",
    "pt-BR": "latin-america/en-br",
    "es-AR": "latin-america/en-ar",
    "es-CL": "latin-america/en-cl",
    "es-MX": "latin-america/en-mx",
    "fr-FR": "europe/en-fr",
    "de-DE": "europe/en-de",
    "ru-RU": "europe/en-ru",
    "es-ES": "europe/en-es",
    "zh-CN": "greater-china/en-cn",
    "zh-HK": "greater-china/en-hk",
    "ko-KR": "ipac/en-kr",
    "ja-JP": "japan/en-jp"
}

# Mapping from locale to flag emoji
FLAG_BY_LOCALE = {
    "zh-TW": "🇹🇼",
    "en-US": "🇺🇸",
    "pt-BR": "🇧🇷",
    "es-AR": "🇦🇷",
    "es-CL": "🇨🇱",
    "es-MX": "🇲🇽",
    "fr-FR": "🇫🇷",
    "de-DE": "🇩🇪",
    "ru-RU": "🇷🇺",
    "es-ES": "🇪🇸",
    "zh-CN": "🇨🇳",
    "zh-HK": "🇭🇰",
    "ko-KR": "🇰🇷",
    "ja-JP": "🇯🇵"
}

st.set_page_config(page_title="AEM Linguistic Review Links", layout="centered")
stitle = "🌐 AEM Linguistic Review Links Converter"
st.title(stitle)

st.markdown("Paste one or more URLs below (one per line), then choose one or more locale targets:")

# Session state initialization
if "urls" not in st.session_state:
    st.session_state.urls = ""
if "locales" not in st.session_state:
    st.session_state.locales = []

# Input fields
urls_input = st.text_area("📥 Paste URLs here:", value=st.session_state.urls, height=200, key="urls")
selected_locales = st.multiselect(
    "🌍 Select target locales:",
    options=sorted(LOCALE_TO_PATH.keys()),  # Sort locales alphabetically
    default=st.session_state.locales,
    key="locales"
)

def convert_domain_and_protocol(url: str) -> str:
    """
    Change the domain/protocol from 'https://author-prod-use1.aemprod.thermofisher.net'
    to 'http://author1.prod.thermofisher.com', leaving the rest of the path intact.
    """
    return url.replace(
        "https://author-prod-use1.aemprod.thermofisher.net",
        "http://author1.prod.thermofisher.com"
    )


def replace_locale_path(url: str, new_path_segment: str) -> str:
    """
    Look for any existing LOCALE_TO_PATH value in the URL (e.g. '/japan/ja-jp/').
    If found, compare the 'country' (first part) of that segment to the new one:
      - If same country, do nothing to the path.
      - If different country, replace '/<existing_segment>/' with '/<new_path_segment>/'.
    If no known segment is found, leave the path unchanged.
    """
    for existing_segment in LOCALE_TO_PATH.values():
        token = f"/{existing_segment}/"
        if token in url:
            existing_country = existing_segment.split("/")[0]
            new_country = new_path_segment.split("/")[0]
            if existing_country == new_country:
                return url  # Same country, no path change
            return url.replace(token, f"/{new_path_segment}/")

    return url  # No known locale segment found

# Buttons
col1, col2 = st.columns([1, 1])
with col1:
    convert = st.button("🔄 Convert URLs")
with col2:
    reset = st.button("🔁 Reset")

if reset:
    st.session_state.clear()
    st.rerun()

if convert:
    if not urls_input.strip():
        st.warning("Please paste at least one URL.")
    elif not selected_locales:
        st.warning("Please select at least one locale.")
    else:
        urls = [u.strip() for u in urls_input.strip().splitlines() if u.strip()]
        grouped_urls = {}

        for locale in selected_locales:
            new_path = LOCALE_TO_PATH[locale]
            converted = []
            for url in urls:
                updated_url = replace_locale_path(url, new_path)
                final_url = convert_domain_and_protocol(updated_url)
                converted.append(final_url)
            grouped_urls[locale] = converted

        # Build a list of dicts, skipping blank URLs
        all_rows = [
            {"Locale": locale, "AEM Linguistic Review Links": url}
            for locale, urls in grouped_urls.items()
            for url in urls
            if url.strip()
        ]
        df_result = pd.DataFrame(all_rows)

        # Write to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_result.to_excel(
                writer,
                index=False,
                sheet_name="AEM Linguistic Review Links"
            )
            worksheet = writer.sheets["AEM Linguistic Review Links"]
            worksheet.set_column("A:A", 20)
            worksheet.set_column("B:B", 60)

        st.subheader("✅ Converted URLs by Locale")
        for locale, url_list in grouped_urls.items():
            flag = FLAG_BY_LOCALE.get(locale, "")
            st.markdown(f"### {locale} {flag}")
            st.text("\n\n".join(url_list))  # Blank line between each URL

        st.download_button(
            label="📥 Download as Excel (.xlsx)",
            data=output.getvalue(),
            file_name="AEM Linguistic Review Links.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
