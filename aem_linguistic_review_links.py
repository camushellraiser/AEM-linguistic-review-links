
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

# Input text area
urls_input = st.text_area("📥 Paste URLs here:", height=200)

# Dropdown for locales
selected_locales = st.multiselect("🌍 Select target locales:", options=list(LOCALE_TO_PATH.keys()))

def convert_domain_and_protocol(url):
    return url.replace("https://author-prod-use1.aemprod.thermofisher.net", "http://author1.prod.thermofisher.com")

def replace_locale_path(url, new_path_segment):
    parts = url.strip().split("/")
    # Try to find the locale pair segment (e.g., 'japan/en-jp')
    for i in range(len(parts) - 1):
        candidate = f"{parts[i]}/{parts[i + 1]}"
        if candidate in LOCALE_TO_PATH.values():
            parts[i] = new_path_segment.split("/")[0]
            parts[i + 1] = new_path_segment.split("/")[1]
            return "/".join(parts)
    # If no match, insert the new path in the expected location
    try:
        index = parts.index("content") + 2
        parts[index] = new_path_segment.split("/")[0]
        parts[index + 1] = new_path_segment.split("/")[1]
    except Exception:
        return url  # fallback: return original
    return "/".join(parts)

# Convert URLs
if st.button("🔄 Convert URLs"):
    if not urls_input.strip():
        st.warning("Please paste at least one URL.")
    elif not selected_locales:
        st.warning("Please select at least one locale.")
    else:
        urls = urls_input.strip().splitlines()
        result_data = []

        for url in urls:
            for locale in selected_locales:
                new_path = LOCALE_TO_PATH[locale]
                updated_url = replace_locale_path(url, new_path)
                final_url = convert_domain_and_protocol(updated_url)
                result_data.append({
                    "Original URL": url,
                    "Locale": locale,
                    "Converted URL": final_url
                })

        df_result = pd.DataFrame(result_data)
        st.subheader("✅ Converted URLs")
        st.dataframe(df_result, use_container_width=True)

        # Export to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_result.to_excel(writer, index=False, sheet_name="Converted Links")
        st.download_button(
            label="📥 Download as Excel (.xlsx)",
            data=output.getvalue(),
            file_name="Converted_Links.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
