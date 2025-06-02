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
    "ja-JP": "japan/ja-jp"
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

BASE_PREFIX = "http://author1.prod.thermofisher.com/editor.html"

# --- Helper functions ---
def ensure_full_url(item: str) -> str:
    item = item.strip()
    if not item:
        return ""
    if item.startswith("/"):
        full = f"{BASE_PREFIX}{item}"
        if not full.endswith(".html"):
            full += ".html"
        return full
    if item.startswith("http"):
        full = item
        if not full.endswith(".html"):
            full += ".html"
        full = full.replace(
            "https://author-prod-use1.aemprod.thermofisher.net",
            "http://author1.prod.thermofisher.com"
        )
        return full
    full = f"{BASE_PREFIX}/{item}"
    if not full.endswith(".html"):
        full += ".html"
    return full


def replace_locale_path(url: str, new_path_segment: str) -> str:
    for existing_segment in LOCALE_TO_PATH.values():
        token = f"/{existing_segment}/"
        if token in url:
            existing_country = existing_segment.split("/")[0]
            new_country = new_path_segment.split("/")[0]
            if existing_country == new_country:
                return url
            return url.replace(token, f"/{new_path_segment}/")
    return url

# --- Streamlit UI ---
st.set_page_config(page_title="AEM Linguistic Review Links", layout="centered")
st.title("🌐 AEM Linguistic Review Links Converter")

st.markdown("Paste URLs/paths/rows below, then choose locale targets and click Convert or Reset:")

# Session state initialization
if "urls" not in st.session_state:
    st.session_state.urls = ""
if "locales" not in st.session_state:
    st.session_state.locales = []
if "grouped_urls" not in st.session_state:
    st.session_state.grouped_urls = {}
if "excel_bytes" not in st.session_state:
    st.session_state.excel_bytes = None

# Build display labels combining flag + locale code
display_to_locale = {f"{FLAG_BY_LOCALE.get(loc, '')} {loc}": loc for loc in LOCALE_TO_PATH.keys()}
sorted_display_labels = sorted(display_to_locale.keys(), key=lambda x: x.split(" ")[1])

# Input fields
urls_input = st.text_area("📥 Paste URLs/paths/rows here:", value=st.session_state.urls, height=200, key="urls")
selected_display = st.multiselect(
    "🌍 Select target locales:",
    options=sorted_display_labels,
    default=st.session_state.locales,
    key="locales"
)
selected_locales = [display_to_locale[d] for d in selected_display]

# Buttons
col1, col2 = st.columns(2)
with col1:
    convert_clicked = st.button("🔄 Convert URLs")
with col2:
    reset_clicked = st.button("🔁 Reset")

if reset_clicked:
    # Clear all session state and rerun
    st.session_state.clear()
    st.experimental_rerun()

if convert_clicked:
    raw_items = [u for u in urls_input.strip().splitlines() if u.strip()]
    prepared_urls = []
    for item in raw_items:
        if "\t" in item:
            parts = item.split("\t")
            path = parts[1]
            full = ensure_full_url(path)
        else:
            full = ensure_full_url(item)
        prepared_urls.append(full)

    grouped = {}
    for locale in selected_locales:
        new_path = LOCALE_TO_PATH[locale]
        converted = [replace_locale_path(url, new_path) for url in prepared_urls]
        grouped[locale] = converted
    st.session_state.grouped_urls = grouped

    # Prepare Excel bytes
    all_rows = [
        {"Locale": loc, "AEM Linguistic Review Links": u}
        for loc, urls_list in grouped.items()
        for u in urls_list
        if u.strip()
    ]
    df_result = pd.DataFrame(all_rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df_result.to_excel(writer, index=False, sheet_name="AEM Linguistic Review Links")
        ws = writer.sheets["AEM Linguistic Review Links"]
        ws.set_column("A:A", 20)
        ws.set_column("B:B", 60)
    st.session_state.excel_bytes = buf.getvalue()

# Display results if available
if st.session_state.grouped_urls:
    st.subheader("✅ Converted URLs by Locale")
    for locale, url_list in st.session_state.grouped_urls.items():
        flag = FLAG_BY_LOCALE.get(locale, "")
        st.markdown(f"### {locale} {flag}")
        for u in url_list:
            st.write(u)
            st.write(" ")

    if st.session_state.excel_bytes:
        st.download_button(
            label="📥 Download as Excel (.xlsx)",
            data=st.session_state.excel_bytes,
            file_name="AEM Linguistic Review Links.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
