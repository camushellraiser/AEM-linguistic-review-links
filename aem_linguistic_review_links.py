import streamlit as st
import pandas as pd
import io

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

st.set_page_config(page_title="AEM Linguistic Review Links", layout="centered")
st.title("🌐 AEM Linguistic Review Links Converter")

st.markdown("Paste one or more URLs below (one per line), then choose one or more locale targets:")

# Session state initialization
if "urls" not in st.session_state:
    st.session_state.urls = ""
if "locales" not in st.session_state:
    st.session_state.locales = []

# Input fields
urls_input = st.text_area("📥 Paste URLs here:", value=st.session_state.urls, height=200, key="urls")
selected_locales = st.multiselect("🌍 Select target locales:", options=list(LOCALE_TO_PATH.keys()), default=st.session_state.locales, key="locales")

def convert_domain_and_protocol(url):
    return url.replace("https://author-prod-use1.aemprod.thermofisher.net", "http://author1.prod.thermofisher.com")

def replace_locale_path(url, new_path_segment):
    parts = url.strip().split("/")
    for i in range(len(parts) - 1):
        candidate = f"{parts[i]}/{parts[i + 1]}"
        if candidate in LOCALE_TO_PATH.values():
            parts[i] = new_path_segment.split("/")[0]
            parts[i + 1] = new_path_segment.split("/")[1]
            return "/".join(parts)
    try:
        index = parts.index("content") + 2
        parts[index] = new_path_segment.split("/")[0]
        parts[index + 1] = new_path_segment.split("/")[1]
    except Exception:
        return url
    return "/".join(parts)

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
        urls = urls_input.strip().splitlines()
        grouped_urls = {}

        for locale in selected_locales:
            new_path = LOCALE_TO_PATH[locale]
            converted = []
            for url in urls:
                updated_url = replace_locale_path(url, new_path)
                final_url = convert_domain_and_protocol(updated_url)
                converted.append(final_url)
            grouped_urls[locale] = converted

        # Display results in grouped blocks
        st.subheader("✅ Converted URLs by Locale")
        for locale, url_list in grouped_urls.items():
            st.markdown(f"### {locale}")
            st.text("\n".join(url_list))

        # Export to Excel
        all_rows = [
            {"Locale": locale, "Converted URL": url}
            for locale, urls in grouped_urls.items()
            for url in urls
        ]
        df_result = pd.DataFrame(all_rows)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_result.to_excel(writer, index=False, sheet_name="Converted Links")
            worksheet = writer.sheets["Converted Links"]
            worksheet.set_column("A:B", 40)
        st.download_button(
            label="📥 Download as Excel (.xlsx)",
            data=output.getvalue(),
            file_name="Converted_Links.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
