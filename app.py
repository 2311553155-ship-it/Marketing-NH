import streamlit as st
import pandas as pd
import re
import plotly.express as px
from io import BytesIO
from pathlib import Path
from supabase import create_client, Client

# ==========================================
# CẤU HÌNH
# ==========================================
st.set_page_config(
    page_title="Quản lý khách hàng",
    page_icon="👤",
    layout="wide"
)

# LOGO
if Path("Logo.jpg").exists():
    st.sidebar.image("Logo.jpg", use_container_width=True)

# ==========================================
# KẾT NỐI SUPABASE
# ==========================================
@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase = get_supabase()

# ==========================================
# HÀM THAO TÁC DATABASE
# ==========================================
def load_customers():
    res = supabase.table("customers").select("*").order("created_at").execute()
    return res.data or []

def add_customer(data: dict):
    supabase.table("customers").insert(data).execute()

def update_customer(id: int, data: dict):
    supabase.table("customers").update(data).eq("id", id).execute()

def delete_customer(id: int):
    supabase.table("customers").delete().eq("id", id).execute()

# ==========================================
# HÀM TIỆN ÍCH
# ==========================================
def small_error(msg: str):
    st.markdown(f'<p style="color:#cc0000;font-size:13px;margin:-10px 0 5px 0;">⚠️ {msg}</p>', unsafe_allow_html=True)

def validate_phone(phone: str) -> bool:
    pattern = r"^(0|\+84)(3[2-9]|5[6-9]|7[0|6-9]|8[0-9]|9[0-9])[0-9]{7}$"
    return bool(re.match(pattern, phone.strip()))

def export_excel(data) -> bytes:
    df = pd.DataFrame(data)
    if "id" in df.columns: df.drop(columns=["id","created_at"], inplace=True, errors="ignore")
    df.columns = ["Số điện thoại","Tên khách hàng","Địa chỉ","Phân loại","Ghi chú"] if len(df.columns)==5 else df.columns
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Khách hàng")
    return output.getvalue()

def get_loai_label(loai: str) -> str:
    return {"VIP": "⭐ VIP", "Thường": "👤 Thường", "Tiềm năng": "🌱 Tiềm năng"}.get(loai, loai)

# ==========================================
# SESSION STATE
# ==========================================
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

# ==========================================
# MENU
# ==========================================
st.sidebar.title("📋 MENU")
page = st.sidebar.radio("Chọn trang", ["👤 Nhập khách hàng", "🔐 Admin"])

# ==========================================
# TRANG NHẬP KHÁCH HÀNG
# ==========================================
if page == "👤 Nhập khách hàng":
    st.title("👤 THÔNG TIN KHÁCH HÀNG")
    st.write("Vui lòng nhập thông tin khách hàng.")
    st.divider()

    phone   = st.text_input("📱 Số điện thoại *", placeholder="VD: 0901234567", key=f"phone_{st.session_state.form_key}")
    if st.session_state.submitted:
        if phone.strip() == "":
            small_error("Vui lòng nhập số điện thoại.")
        elif not validate_phone(phone):
            small_error("Số điện thoại không đúng định dạng (VD: 0901234567).")

    name    = st.text_input("👤 Tên khách hàng *", placeholder="Nhập tên khách hàng", key=f"name_{st.session_state.form_key}")
    if st.session_state.submitted and name.strip() == "":
        small_error("Vui lòng nhập tên khách hàng.")

    address = st.text_input("📍 Địa chỉ", placeholder="Nhập địa chỉ", key=f"addr_{st.session_state.form_key}")
    loai    = st.selectbox("🏷️ Phân loại khách hàng", ["Thường", "Tiềm năng", "VIP"], key=f"loai_{st.session_state.form_key}")
    note    = st.text_area("📝 Ghi chú", placeholder="Nhập ghi chú", key=f"note_{st.session_state.form_key}")
    st.divider()

    if st.button("💾 LƯU THÔNG TIN", type="primary", use_container_width=True):
        st.session_state.submitted = True
        phone_ok = phone.strip() != "" and validate_phone(phone)
        name_ok  = name.strip() != ""
        if phone_ok and name_ok:
            try:
                add_customer({
                    "so_dien_thoai": phone.strip(),
                    "ten_khach_hang": name.strip(),
                    "dia_chi": address.strip(),
                    "phan_loai": loai,
                    "ghi_chu": note.strip()
                })
                st.session_state.submitted = False
                st.session_state.save_success = True
                st.session_state.form_key += 1
            except Exception as e:
                if "unique" in str(e).lower():
                    st.error("❌ Số điện thoại này đã tồn tại.")
                else:
                    st.error(f"❌ Lỗi: {e}")
        st.rerun()

    if st.session_state.get("save_success"):
        st.success("✅ Đã lưu thông tin khách hàng thành công!")
        st.session_state.save_success = False

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

        customers = load_customers()

        if len(customers) == 0:
            st.info("📭 Chưa có khách hàng nào.")
        else:
            df = pd.DataFrame(customers)

            # THỐNG KÊ
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("👥 Tổng khách hàng", len(df))
            c2.metric("⭐ VIP", len(df[df["phan_loai"] == "VIP"]))
            c3.metric("🌱 Tiềm năng", len(df[df["phan_loai"] == "Tiềm năng"]))
            c4.metric("👤 Thường", len(df[df["phan_loai"] == "Thường"]))
            st.divider()

            # BIỂU ĐỒ
            with st.expander("📈 Biểu đồ thống kê", expanded=True):
                chart_df = df["phan_loai"].value_counts().reset_index()
                chart_df.columns = ["Phân loại", "Số lượng"]
                color_map = {"VIP": "#FFD700", "Tiềm năng": "#4CAF50", "Thường": "#2196F3"}
                fig = px.bar(chart_df, x="Phân loại", y="Số lượng",
                             color="Phân loại", color_discrete_map=color_map,
                             text="Số lượng", title="Phân bố khách hàng theo loại")
                fig.update_traces(textposition="outside", textfont_size=16)
                fig.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)",
                                  yaxis=dict(showgrid=True, gridcolor="#eee", title="Số khách hàng"),
                                  xaxis=dict(title=""), height=350)
                st.plotly_chart(fig, use_container_width=True)
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
                    filtered["ten_khach_hang"].str.contains(search, case=False, na=False) |
                    filtered["so_dien_thoai"].str.contains(search, case=False, na=False)
                )
                filtered = filtered[mask]
            if filter_loai != "Tất cả":
                filtered = filtered[filtered["phan_loai"] == filter_loai]

            st.caption(f"Hiển thị {len(filtered)} / {len(df)} khách hàng")
            st.divider()

            # DANH SÁCH
            st.subheader("📋 Danh sách khách hàng")
            if len(filtered) == 0:
                st.info("Không tìm thấy khách hàng phù hợp.")
            else:
                for _, row in filtered.iterrows():
                    with st.expander(
                        f"{get_loai_label(row['phan_loai'])}  |  {row['ten_khach_hang']}  —  {row['so_dien_thoai']}"
                    ):
                        if st.session_state.edit_id == row["id"]:
                            new_phone = st.text_input("📱 Số điện thoại", value=row["so_dien_thoai"], key=f"p{row['id']}")
                            new_name  = st.text_input("👤 Tên", value=row["ten_khach_hang"], key=f"n{row['id']}")
                            new_addr  = st.text_input("📍 Địa chỉ", value=row["dia_chi"] or "", key=f"a{row['id']}")
                            new_loai  = st.selectbox("🏷️ Loại", ["Thường","Tiềm năng","VIP"],
                                                     index=["Thường","Tiềm năng","VIP"].index(row["phan_loai"]),
                                                     key=f"l{row['id']}")
                            new_note  = st.text_area("📝 Ghi chú", value=row["ghi_chu"] or "", key=f"note{row['id']}")
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button("✅ Lưu", key=f"save{row['id']}", type="primary"):
                                    if not validate_phone(new_phone):
                                        st.error("❌ Số điện thoại không đúng định dạng.")
                                    elif new_name.strip() == "":
                                        st.error("❌ Vui lòng nhập tên.")
                                    else:
                                        update_customer(row["id"], {
                                            "so_dien_thoai": new_phone.strip(),
                                            "ten_khach_hang": new_name.strip(),
                                            "dia_chi": new_addr.strip(),
                                            "phan_loai": new_loai,
                                            "ghi_chu": new_note.strip()
                                        })
                                        st.session_state.edit_id = None
                                        st.rerun()
                            with b2:
                                if st.button("❌ Hủy", key=f"cancel{row['id']}"):
                                    st.session_state.edit_id = None
                                    st.rerun()
                        else:
                            st.write(f"📍 **Địa chỉ:** {row['dia_chi'] or '—'}")
                            st.write(f"📝 **Ghi chú:** {row['ghi_chu'] or '—'}")
                            b1, b2 = st.columns(2)
                            with b1:
                                if st.button("✏️ Chỉnh sửa", key=f"edit{row['id']}"):
                                    st.session_state.edit_id = row["id"]
                                    st.rerun()
                            with b2:
                                if st.button("🗑️ Xóa", key=f"del{row['id']}"):
                                    delete_customer(row["id"])
                                    st.rerun()

            st.divider()
            excel_file = export_excel(customers)
            st.download_button(
                label="📥 XUẤT FILE EXCEL",
                data=excel_file,
                file_name="danh_sach_khach_hang.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
