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
    for existing_segment in LOCALE_TO_PATH.values():
        if f"/{existing_segment}/" in url:
            existing_country = existing_segment.split("/")[0]
            new_country = new_path_segment.split("/")[0]
            if existing_country == new_country:
                return url  # Same country, skip path replacement
            return url.replace(f"/{existing_segment}/", f"/{new_path_segment}/")

    # If not found, try to find any locale pattern in the form of /xx/xx/ and replace it
    import re
    match = re.search(r"/(?:[a-z\-]+)/(?:[a-z\-]+)/", url)
    if match:
        existing_country = match.group(0).strip("/").split("/")[0]
        new_country = new_path_segment.split("/")[0]
        if existing_country == new_country:
            return url
        return url.replace(match.group(0), f"/{new_path_segment}/")

    return url.replace(f"/{existing_segment}/", f"/{new_path_segment}/")

    # If not found, try to find any locale pattern in the form of /xx/xx/ and replace it
    import re
    match = re.search(r"/(?:[a-z\-]+)/(?:[a-z\-]+)/", url)
    if match:
        return url.replace(match.group(0), f"/{new_path_segment}/")

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
        df_result.rename(columns={"Converted URL": "AEM Linguistic Review Links"}, inplace=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_result.to_excel(writer, index=False, sheet_name="AEM Linguistic Review Links")
            worksheet = writer.sheets["AEM Linguistic Review Links"]
            worksheet.set_column("A:A", 20)
            worksheet.set_column("B:B", 60)
        st.download_button(
            label="📥 Download as Excel (.xlsx)",
            data=output.getvalue(),
            file_name="AEM Linguistic Review Links.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
