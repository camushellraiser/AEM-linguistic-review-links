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

# --- Define helper functions before usage ---
def convert_domain_and_protocol(url: str) -> str:
    return url.replace(
        "https://author-prod-use1.aemprod.thermofisher.net",
        "http://author1.prod.thermofisher.com"
    )


def replace_locale_path(url: str, new_path_segment: str) -> str:
    for existing_segment in LOCALE_TO_PATH.values():
        token = f"/{existing_segment}/"
        if token in url:
            existing_country = existing_segment.split("/")[0]
            new_country = new_path_segment.split("/")[0]
            if existing_country == new_country:
                return url
            return url.replace(token, f"/{new_path_segment}/")
    return url  # No known locale segment found

# --- Streamlit UI ---
st.set_page_config(page_title="AEM Linguistic Review Links", layout="centered")
st.title("🌐 AEM Linguistic Review Links Converter")

st.markdown("Paste one or more URLs below (one per line), then choose one or more locale targets:")

# Session state initialization
if "urls" not in st.session_state:
    st.session_state.urls = ""
if "locales" not in st.session_state:
    st.session_state.locales = []  # Stores display labels (flag + code)

# Build display labels combining flag + locale code
display_to_locale = {f"{FLAG_BY_LOCALE.get(loc, '')} {loc}": loc for loc in LOCALE_TO_PATH.keys()}
# Sort display labels alphabetically by locale code portion
sorted_display_labels = sorted(display_to_locale.keys(), key=lambda x: x.split(" ")[1])

# Input fields
urls_input = st.text_area("📥 Paste URLs here:", value=st.session_state.urls, height=200, key="urls")
selected_display = st.multiselect(
    "🌍 Select target locales:",
    options=sorted_display_labels,
    default=st.session_state.locales,
    key="locales"
)
# Convert selected display back to pure locale codes
selected_locales = [display_to_locale[d] for d in selected_display]

if st.button("🔁 Reset"):
    st.session_state.clear()
    st.rerun()

if st.button("🔄 Convert URLs"):
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

        # Build rows for Excel, skipping blank URLs
        all_rows = [
            {"Locale": locale, "AEM Linguistic Review Links": url}
            for locale, urls_list in grouped_urls.items()
            for url in urls_list
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
