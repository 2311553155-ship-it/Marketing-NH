import streamlit as st
import pandas as pd
import re
from io import BytesIO
from pathlib import Path

# ==========================================
# CẤU HÌNH
# ==========================================
st.set_page_config(
    page_title="Quản lý khách hàng",
    page_icon="👤",
    layout="wide"
)

# ==========================================
# LOGO
# ==========================================
logo_path = Path("Logo.jpg")
if logo_path.exists():
    st.sidebar.image("Logo.jpg", use_container_width=True)

# ==========================================
# KHỞI TẠO SESSION STATE
# ==========================================
if "customers" not in st.session_state:
    st.session_state.customers = []
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# ==========================================
# HÀM TIỆN ÍCH
# ==========================================
def validate_phone(phone: str) -> bool:
    pattern = r"^(0|\+84)(3[2-9]|5[6-9]|7[0|6-9]|8[0-9]|9[0-9])[0-9]{7}$"
    return bool(re.match(pattern, phone.strip()))

def export_excel() -> bytes:
    df = pd.DataFrame(st.session_state.customers)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Khách hàng")
    return output.getvalue()

def get_loai_label(loai: str) -> str:
    return {"VIP": "⭐ VIP", "Thường": "👤 Thường", "Tiềm năng": "🌱 Tiềm năng"}.get(loai, loai)

# ==========================================
# MENU
# ==========================================
st.sidebar.title("📋 MENU")
page = st.sidebar.radio(
    "Chọn trang",
    ["👤 Nhập khách hàng", "🔐 Admin"]
)

# ==========================================
# TRANG NHẬP KHÁCH HÀNG
# ==========================================
if page == "👤 Nhập khách hàng":
    st.title("👤 THÔNG TIN KHÁCH HÀNG")
    st.write("Vui lòng nhập thông tin khách hàng.")
    st.divider()

    phone   = st.text_input("📱 Số điện thoại *", placeholder="VD: 0901234567")
    name    = st.text_input("👤 Tên khách hàng *", placeholder="Nhập tên khách hàng")
    address = st.text_input("📍 Địa chỉ", placeholder="Nhập địa chỉ")
    loai    = st.selectbox("🏷️ Phân loại khách hàng", ["Thường", "Tiềm năng", "VIP"])
    note    = st.text_area("📝 Ghi chú", placeholder="Nhập ghi chú")
    st.divider()

    if st.button("💾 LƯU THÔNG TIN", type="primary", use_container_width=True):
        if phone.strip() == "":
            st.error("❌ Vui lòng nhập số điện thoại.")
        elif not validate_phone(phone):
            st.error("❌ Số điện thoại không đúng định dạng Việt Nam (VD: 0901234567).")
        elif name.strip() == "":
            st.error("❌ Vui lòng nhập tên khách hàng.")
        else:
            existing_phones = [c["Số điện thoại"] for c in st.session_state.customers]
            if phone.strip() in existing_phones:
                st.warning("⚠️ Số điện thoại này đã tồn tại trong danh sách.")
            else:
                st.session_state.customers.append({
                    "Số điện thoại": phone.strip(),
                    "Tên khách hàng": name.strip(),
                    "Địa chỉ": address.strip(),
                    "Phân loại": loai,
                    "Ghi chú": note.strip()
                })
                st.success("✅ Đã lưu thông tin khách hàng!")

# ==========================================
# TRANG ADMIN
# ==========================================
elif page == "🔐 Admin":
    st.title("🔐 ADMIN")
    st.divider()

    if not st.session_state.admin_logged_in:
        password = st.text_input("🔑 Mật khẩu", type="password")
        if st.button("ĐĂNG NHẬP", type="primary"):
            if password == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("❌ Sai mật khẩu.")
    else:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.subheader("📊 DANH SÁCH KHÁCH HÀNG")
        with col2:
            if st.button("🚪 Đăng xuất"):
                st.session_state.admin_logged_in = False
                st.rerun()
        st.divider()

        if len(st.session_state.customers) == 0:
            st.info("📭 Chưa có khách hàng nào.")
        else:
            df = pd.DataFrame(st.session_state.customers)

            # THỐNG KÊ
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("👥 Tổng khách hàng", len(df))
            c2.metric("⭐ VIP", len(df[df["Phân loại"] == "VIP"]))
            c3.metric("🌱 Tiềm năng", len(df[df["Phân loại"] == "Tiềm năng"]))
            c4.metric("👤 Thường", len(df[df["Phân loại"] == "Thường"]))
            st.divider()

            # BIỂU ĐỒ
            with st.expander("📈 Biểu đồ thống kê", expanded=True):
                chart_df = df["Phân loại"].value_counts().reset_index()
                chart_df.columns = ["Phân loại", "Số lượng"]
                st.bar_chart(chart_df.set_index("Phân loại"))
            st.divider()

            # TÌM KIẾM & LỌC
            st.subheader("🔍 Tìm kiếm & Lọc")
            s1, s2 = st.columns([3, 1])
            with s1:
                search = st.text_input("Tìm theo tên hoặc số điện thoại", placeholder="Nhập từ khóa...")
            with s2:
                filter_loai = st.selectbox("Lọc theo loại", ["Tất cả", "VIP", "Tiềm năng", "Thường"])

            filtered = df.copy()
            if search.strip():
                mask = (
                    filtered["Tên khách hàng"].str.contains(search, case=False, na=False) |
                    filtered["Số điện thoại"].str.contains(search, case=False, na=False)
                )
                filtered = filtered[mask]
            if filter_loai != "Tất cả":
                filtered = filtered[filtered["Phân loại"] == filter_loai]

            st.caption(f"Hiển thị {len(filtered)} / {len(df)} khách hàng")
            st.divider()

            # DANH SÁCH + CHỈNH SỬA / XÓA
            st.subheader("📋 Danh sách khách hàng")
            if len(filtered) == 0:
                st.info("Không tìm thấy khách hàng phù hợp.")
            else:
                for i, row in filtered.iterrows():
                    with st.expander(
                        f"{get_loai_label(row['Phân loại'])}  |  {row['Tên khách hàng']}  —  {row['Số điện thoại']}"
                    ):
                        if st.session_state.edit_index == i:
                            new_phone = st.text_input("📱 Số điện thoại", value=row["Số điện thoại"], key=f"p{i}")
                            new_name  = st.text_input("👤 Tên", value=row["Tên khách hàng"], key=f"n{i}")
                            new_addr  = st.text_input("📍 Địa chỉ", value=row["Địa chỉ"], key=f"a{i}")
                            new_loai  = st.selectbox("🏷️ Loại", ["Thường","Tiềm năng","VIP"],
                                                     index=["Thường","Tiềm năng","VIP"].index(row["Phân loại"]),
                                                     key=f"l{i}")
                            new_note  = st.text_area("📝 Ghi chú", value=row["Ghi chú"], key=f"note{i}")
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button("✅ Lưu", key=f"save{i}", type="primary"):
                                    if not validate_phone(new_phone):
                                        st.error("❌ Số điện thoại không đúng định dạng.")
                                    elif new_name.strip() == "":
                                        st.error("❌ Vui lòng nhập tên.")
                                    else:
                                        st.session_state.customers[i] = {
                                            "Số điện thoại": new_phone.strip(),
                                            "Tên khách hàng": new_name.strip(),
                                            "Địa chỉ": new_addr.strip(),
                                            "Phân loại": new_loai,
                                            "Ghi chú": new_note.strip()
                                        }
                                        st.session_state.edit_index = None
                                        st.rerun()
                            with b2:
                                if st.button("❌ Hủy", key=f"cancel{i}"):
                                    st.session_state.edit_index = None
                                    st.rerun()
                        else:
                            st.write(f"📍 **Địa chỉ:** {row['Địa chỉ'] or '—'}")
                            st.write(f"📝 **Ghi chú:** {row['Ghi chú'] or '—'}")
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button("✏️ Chỉnh sửa", key=f"edit{i}"):
                                    st.session_state.edit_index = i
                                    st.rerun()
                            with b2:
                                if st.button("🗑️ Xóa", key=f"del{i}"):
                                    st.session_state.customers.pop(i)
                                    st.rerun()

            st.divider()

            # XUẤT EXCEL
            excel_file = export_excel()
            st.download_button(
                label="📥 XUẤT FILE EXCEL",
                data=excel_file,
                file_name="danh_sach_khach_hang.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
