import streamlit as st
import pdfplumber
import re
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="PEA AI Auditor PRO", layout="wide")

# ปรับแต่ง CSS สำหรับสถานะและส่วนต่าง
st.markdown("""
    <style>
    .stDataFrame { border-radius: 10px; }
    .stButton>button { background-color: #007bff; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ PEA AI PDF Auditor (Difference Analysis Mode)")

# --- ฐานข้อมูลมาตรฐาน (ฉบับสมบูรณ์) ---
TR_STANDARDS = {
    "50": {
        "TR_CODE": "1050010066",
        "items": {
            "1040020000": {"name": "L.T. H.R.C. FUSE 32-36 A.", "qty": -3.0},
            "1040020001": {"name": "L.T. H.R.C. FUSE 50 A.", "qty": -3.0},
            "1040020010": {"name": "H.R.C. FUSE, BLADE CONTACT, 32 A.", "qty": 3.0},
            "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -6.0},
            "1040020102": {"name": "FSD, FULL INSULATED, 1X400A, 400V", "qty": 6.0},
            "1050010066": {"name": "TR. 50 kVA, 3P", "qty": 1.0},
            "14144": {"name": "X-ARM-C SET", "qty": 1.0},
            "40114": {"name": "LT WIRING 95 SQ.MM.", "qty": 2.0},
            "40205": {"name": "TR. INST. SET", "qty": 1.0}
        }
    },
    "100": {
        "TR_CODE": "1050010067",
        "items": {
            "1040020002": {"name": "L.T. H.R.C. FUSE 80 A.", "qty": -6.0},
            "1040020012": {"name": "H.R.C. FUSE, BLADE CONTACT, 80 A.", "qty": 6.0},
            "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -6.0},
            "1040020102": {"name": "FSD, FULL INSULATED, 1X400A", "qty": 6.0},
            "1050010067": {"name": "TR. 100 kVA, 3P", "qty": 1.0},
            "14021": {"name": "LT. FUSE SET (50 kVA)", "qty": 2.0},
            "14144": {"name": "X-ARM-C SET", "qty": 1.0},
            "40114": {"name": "LT WIRING 95 SQ.MM.", "qty": 2.0},
            "40205": {"name": "TR. INST. SET", "qty": 1.0}
        }
    },
    "160": {
        "TR_CODE": "1050010068",
        "items": {
            "1040020002": {"name": "L.T. H.R.C. FUSE 80 A.", "qty": -3.0},
            "1040020012": {"name": "H.R.C. FUSE, BLADE CONTACT, 80 A.", "qty": 3.0},
            "1040020004": {"name": "L.T. H.R.C. FUSE 150-160 A.", "qty": -3.0},
            "1040020014": {"name": "H.R.C. FUSE, BLADE CONTACT, 160 A.", "qty": 3.0},
            "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -6.0},
            "1040020102": {"name": "FSD, FULL INSULATED, 1X400A", "qty": 6.0},
            "1050010068": {"name": "TR. 160 kVA, 3P", "qty": 1.0},
            "14144": {"name": "X-ARM-C SET", "qty": 1.0},
            "40114": {"name": "LT WIRING 95 SQ.MM.", "qty": 2.0},
            "40205": {"name": "TR. INST. SET", "qty": 1.0}
        }
    },
    "250": {
        "TR_CODE": "1050010069",
        "items": {
            "1040020004": {"name": "L.T. H.R.C. FUSE 150-160 A.", "qty": -3.0},
            "1040020014": {"name": "H.R.C. FUSE, BLADE CONTACT, 160 A.", "qty": 3.0},
            "1040020005": {"name": "L.T. H.R.C. FUSE 200 A.", "qty": -3.0},
            "1040020015": {"name": "H.R.C. FUSE, BLADE CONTACT, 200 A.", "qty": 3.0},
            "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -6.0},
            "1040020102": {"name": "FSD, FULL INSULATED, 1X400A", "qty": 6.0},
            "1050010069": {"name": "TR. 250 kVA, 3P", "qty": 1.0},
            "14144": {"name": "X-ARM-C SET", "qty": 1.0},
            "40115": {"name": "LT WIRING 120 SQ.MM.", "qty": 2.0},
            "40205": {"name": "TR. INST. SET", "qty": 1.0}
        }
    }
}

def color_status(val):
    if "ครบ" in str(val): return 'background-color: #d4edda'
    if "ขาด" in str(val): return 'background-color: #f8d7da'
    if "เกิน" in str(val): return 'background-color: #fff3cd'
    return ''

uploaded_file = st.file_uploader("📂 อัปโหลดไฟล์ PDF ตรวจสอบพัสดุ", type="pdf")

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
        clean_text_check = re.sub(r'\s+', '', full_text)
        detected_size = next((sz for sz, d in TR_STANDARDS.items() if d["TR_CODE"] in clean_text_check), None)

        if detected_size:
            st.success(f"✅ ตรวจพบหม้อแปลงขนาด **{detected_size} kVA**")
            check_list = TR_STANDARDS[detected_size]["items"]
            audit_results = []

            for code, std in check_list.items():
                found_qty = 0.0
                if code in clean_text_check:
                    row = re.search(f"{code}.*?(\n|$)", full_text)
                    if row:
                        nums = re.findall(r"-?\d+\.\d+", row.group(0))
                        if nums:
                            found_qty = float(nums[-1])
                
                # คำนวณส่วนต่าง
                diff = found_qty - std['qty']
                
                # วิเคราะห์หมายเหตุ
                if diff == 0:
                    note = "✅ ครบถ้วน"
                elif diff < 0:
                    note = f"❌ ขาดไป {abs(diff):.1f}"
                else:
                    note = f"➕ เกินมา {diff:.1f}"

                audit_results.append({
                    "รหัสพัสดุ": code,
                    "ชื่ออุปกรณ์": std['name'],
                    "มาตรฐาน": std['qty'],
                    "ในไฟล์ PDF": found_qty,
                    "ส่วนต่าง": diff,
                    "หมายเหตุ": note
                })

            df = pd.DataFrame(audit_results)
            st.subheader(f"📊 รายงานวิเคราะห์ส่วนต่าง (หม้อแปลง {detected_size} kVA)")
            
            # แสดงตารางพร้อมไฮไลท์สีในคอลัมน์หมายเหตุ
            st.dataframe(df.style.applymap(color_status, subset=['หมายเหตุ']), use_container_width=True)

            # ปุ่มดาวน์โหลด Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Difference_Analysis')
            
            st.download_button(
                label="📥 Download รายงานส่วนต่าง (Excel)",
                data=output.getvalue(),
                file_name=f"Difference_Report_{detected_size}kVA.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("❌ ไม่พบรหัสหม้อแปลงที่กำหนดในไฟล์นี้ กรุณาตรวจสอบว่าไฟล์ PDF ถูกต้อง")
