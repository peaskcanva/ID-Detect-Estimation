
import streamlit as st
import pdfplumber
import re

st.set_page_config(page_title="PEA AI Auditor", layout="wide")
st.title("⚡ PEA AI PDF Auditor (Smart ID Detection)")

# 1. ฐานข้อมูลมาตรฐาน แยกตามขนาดหม้อแปลง (อ้างอิงรหัสจากไฟล์ที่คุณส่งมา)
# เพิ่มรหัสหม้อแปลง (TR_CODE) เข้าไปในแต่ละชุดเพื่อใช้ระบุขนาด
# 1. ฐานข้อมูลมาตรฐานเฉพาะหน้าแรก (รวมรหัสพัสดุทุกรายการที่ปรากฏในตารางหน้า 1)
# 1. ฐานข้อมูลมาตรฐานเฉพาะหน้าแรก (อ้างอิงรหัสและจำนวนจากไฟล์ PDF ทั้ง 4 ขนาด)
TR_STANDARDS = {
    "50": {
        "TR_CODE": "1050010066",
        "items": {
            "1040020000": {"name": "L.T. H.R.C. FUSE 32-36 A.", "qty": -3.0},
            "1040020001": {"name": "L.T. H.R.C. FUSE 50 A.", "qty": -3.0},
            "1040020010": {"name": "H.R.C. FUSE, BLADE CONTACT, 32 A.", "qty": 3.0},
            "1040020011": {"name": "H.R.C. FUSE, BLADE CONTACT, 50 A.", "qty": 3.0},
            "1040020100": {"name": "L.T. FUSE SWITCHES 1X400 A. 500 V.", "qty": -6.0},
            "1040020102": {"name": "FSD, FULL INSULATED, 1X400A, 400V", "qty": 6.0},
            "1050010066": {"name": "TR. 50 kVA, 3P", "qty": 1.0},
            "14019": {"name": "LT. FUSE SET (20 kVA)", "qty": 1.0},
            "14020": {"name": "LT. FUSE SET (30 kVA)", "qty": 1.0},
            "14144": {"name": "X-ARM-C SET", "qty": 1.0},
            "40114": {"name": "LT WIRING 95 SQ.MM.", "qty": 2.0},
            "40205": {"name": "TR. INST. SET", "qty": 1.0}
        }
    },
    "100": {
        "TR_CODE": "1050010067",
        "items": {
            "1040020002": {"name": "L.T. H.R.C. FUSE 80 A.", "qty": -6.0}, # รื้อถอน
            "1040020012": {"name": "H.R.C. FUSE, BLADE CONTACT, 80 A.", "qty": 6.0}, # ก่อสร้าง
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
            "14021": {"name": "LT. FUSE SET (50 kVA)", "qty": 1.0},
            "14023": {"name": "LT. FUSE SET (100 kVA)", "qty": 1.0},
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
            "14023": {"name": "LT. FUSE SET (100 kVA)", "qty": 1.0},
            "14024": {"name": "LT. FUSE SET (140 kVA)", "qty": 1.0},
            "14144": {"name": "X-ARM-C SET", "qty": 1.0},
            "40115": {"name": "LT WIRING 120 SQ.MM.", "qty": 2.0},
            "40205": {"name": "TR. INST. SET", "qty": 1.0}
        }
    }
}

COMMON_ITEMS = {

}

uploaded_file = st.file_uploader("📂 อัปโหลดไฟล์ PDF (50/100/160/250 kVA)", type="pdf")

if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

        # ล้างช่องว่างเพื่อเช็ค ID
        clean_text_check = re.sub(r'\s+', '', full_text)

        # 2. ตรวจหาขนาดหม้อแปลงจาก "รหัสพัสดุหม้อแปลง" ในรายการ
        detected_size = None
        for size, data in TR_STANDARDS.items():
            if data["TR_CODE"] in clean_text_check:
                detected_size = size
                break

        if detected_size:
            st.success(f"📌 ตรวจพบรหัสหม้อแปลงขนาด **{detected_size} kVA** ในรายการพัสดุ")

            check_list = {**TR_STANDARDS[detected_size]["items"], **COMMON_ITEMS}

            st.subheader(f"🔍 ผลการตรวจสอบเทียบมาตรฐาน {detected_size} kVA")

            for code, std in check_list.items():
                if code in clean_text_check:
                    # หาบรรทัดที่มีรหัสพัสดุนี้
                    row_match = re.search(f"{code}.*?(\n|$)", full_text)
                    found_qty = "ไม่ระบุ"
                    if row_match:
                        line_text = row_match.group(0)
                        # ดึงตัวเลขตัวสุดท้าย (ซึ่งมักจะเป็นคอลัมน์ก่อสร้าง/รื้อถอน)
                        all_numbers = re.findall(r"-?\d+\.\d+", line_text)
                        if all_numbers:
                            found_qty = float(all_numbers[-1])

                    if found_qty == std['qty']:
                        st.success(f"✅ **{code}** | {std['name']} | จำนวน: {found_qty} (ถูกต้อง)")
                    else:
                        st.warning(f"⚠️ **{code}** | {std['name']} | จำนวนที่พบ: {found_qty} (มาตรฐานคือ {std['qty']})")
                else:
                    st.error(f"❌ **{code}** | ไม่พบรายการ: {std['name']}")
        else:
            st.error("❌ ไม่พบรหัสพัสดุหม้อแปลงที่กำหนดในไฟล์นี้ (โปรดเช็ครหัส 1050010066-69)")

    with st.expander("📝 ดูข้อความดิบจาก PDF"):
        st.text(full_text)
