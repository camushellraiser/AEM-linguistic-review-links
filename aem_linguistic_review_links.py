
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="AEM Linguistic Review Links", layout="centered")

st.title("🌐 AEM Linguistic Review Links Converter")

st.markdown("""
Paste one or more URLs below (one per line).  
This app will convert them to the proper review format for Thermo Fisher.
""")

# --- User Input ---
urls_input = st.text_area("📥 Paste URLs here:", height=200)

# --- Conversion Logic ---
def convert_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if "aemprod.thermofisher.net" in url:
        url = url.replace("https://", "http://", 1)
        url = url.replace("author-prod-use1.aemprod.thermofisher.net", "author1.prod.thermofisher.com", 1)
    return url

# --- Conversion Trigger ---
if st.button("🔄 Convert URLs"):
    if urls_input.strip():
        input_lines = urls_input.strip().splitlines()
        converted_urls = [convert_url(u) for u in input_lines]

        df_result = pd.DataFrame({"AEM Linguistic Review Links": converted_urls})

        st.subheader("✅ Converted URLs")
        st.dataframe(df_result, use_container_width=True)

        # Download as Excel using openpyxl
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_result.to_excel(writer, index=False, sheet_name="Links")
        st.download_button(
            label="📥 Download as Excel",
            data=output.getvalue(),
            file_name="AEM_Linguistic_Review_Links.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Please paste at least one URL before clicking 'Convert'.")
