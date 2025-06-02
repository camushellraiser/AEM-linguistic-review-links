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

# --- Helper Functions ---

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

# Page type selection
type_option = st.radio(
    "Select Page Type:",
    [
        "Same Page(s) - Use for one or several locales using the same page",
        "Different Page(s) - Use for several locales using different pages or for Launch Pages"
    ]
)
# Strip description
type_option = type_option.split(" - ")[0]

# Locale selection dropdown with flags
display_to_locale = {f"{FLAG_BY_LOCALE.get(loc, '')} {loc}": loc for loc in LOCALE_TO_PATH.keys()}
sorted_display_labels = sorted(display_to_locale.keys(), key=lambda x: x.split(" ")[1])
selected_display = st.multiselect(
    "🌍 Select target locales:",
    options=sorted_display_labels,
    default=[],
    key="locales"
)
selected_locales = [display_to_locale[d] for d in selected_display]

# Render text inputs based on page type
table_inputs = {}
if type_option == "Different Page(s)":
    for locale in selected_locales:
        flag = FLAG_BY_LOCALE.get(locale, "")
        key_name = f"urls_{locale}"
        table_inputs[locale] = st.text_area(
            f"📥 Paste URLs/paths for {locale} {flag}:", height=150, key=key_name
        )
elif type_option == "Same Page(s)":
    table_inputs["regular"] = st.text_area(
        "📥 Paste URLs/paths/rows here:", height=200, key="urls"
    )

# Buttons and placeholder for download
grid1, grid2, grid3 = st.columns([1,1,1])
with grid1:
    convert_clicked = st.button("🔄 Convert URLs")
with grid2:
    reset_clicked = st.button("🔁 Reset")
with grid3:
    download_placeholder = st.empty()

# Reset logic: full reload
if reset_clicked:
    st.markdown('<meta http-equiv="refresh" content="0">', unsafe_allow_html=True)
    st.stop()

# Conversion logic
grouped_urls = {}
if convert_clicked:
    if not selected_locales:
        st.warning("Please select at least one locale.")
    else:
        if type_option == "Different Page(s)":
            for locale in selected_locales:
                raw_text = table_inputs.get(locale, "")
                raw_items = [u for u in raw_text.strip().splitlines() if u.strip()]
                prepared = [
                    ensure_full_url(item.split("\t")[1]) if "\t" in item else ensure_full_url(item)
                    for item in raw_items
                ]
                new_path = LOCALE_TO_PATH[locale]
                converted = [replace_locale_path(url, new_path) for url in prepared]
                grouped_urls[locale] = converted
        else:  # Same Page(s)
            raw_text = table_inputs.get("regular", "")
            raw_items = [u for u in raw_text.strip().splitlines() if u.strip()]
            prepared = [
                ensure_full_url(item.split("\t")[1]) if "\t" in item else ensure_full_url(item)
                for item in raw_items
            ]
            for locale in selected_locales:
                new_path = LOCALE_TO_PATH[locale]
                converted = [replace_locale_path(url, new_path) for url in prepared]
                grouped_urls[locale] = converted

    st.session_state.grouped_urls = grouped_urls
    # Build Excel bytes
    all_rows = [{"Locale": loc, "AEM Linguistic Review Links": u}
                for loc, urls_list in grouped_urls.items() for u in urls_list if u.strip()]
    df_result = pd.DataFrame(all_rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df_result.to_excel(writer, index=False, sheet_name="AEM Linguistic Review Links")
        ws = writer.sheets["AEM Linguistic Review Links"]
        ws.set_column("A:A", 20)
        ws.set_column("B:B", 60)
    st.session_state.excel_bytes = buf.getvalue()

# Show download button if Excel data exists
if "excel_bytes" in st.session_state and st.session_state.excel_bytes:
    download_placeholder.download_button(
        label="📥 Download as Excel (.xlsx)",
        data=st.session_state.excel_bytes,
        file_name="AEM Linguistic Review Links.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Display converted URLs below if available
if "grouped_urls" in st.session_state and st.session_state.grouped_urls:
    st.subheader("✅ Converted URLs by Locale")
    for locale, url_list in st.session_state.grouped_urls.items():
        flag = FLAG_BY_LOCALE.get(locale, "")
        st.markdown(f"### {locale} {flag}")
        for u in url_list:
            st.write(u)
            st.write(" ")
