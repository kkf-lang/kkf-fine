import base64
import io
import re
from github import Github
import openpyxl
import pandas as pd
import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="Employee Fine & Record Management System", layout="wide"
)
st.title("📋 Employee Fine & Record Management System")

# --- Fine Categories & Amounts ---
FINE_RATES = {
    "ကွမ်းစားခြင်း": 3000,
    "ဖုန်းတွေ့ရှိခြင်း": 5000,
    "Bluetooth နားကြပ်တွေ့ရှိခြင်း": 3000,
    "ဆေးလိပ်၊မီးခြစ်တွေ့ရှိခြင်း": 3000,
    "အလုပ်ချိန်အိပ်နေခြင်း": 3000,
    "ဝန်ထမ်းကတ်မဆွဲခြင်း": 3000,
}

FINE_COLUMNS = [
    "Employee ID",
    "Employee Name",
    "Fine Category",
    "Fine Amount",
    "Date",
]
EMP_COLUMNS = [
    "Employee ID",
    "Employee Name",
    "Department",
    "Join Date",
    "Status",
    "Photo Path",
]
RESIGN_COLUMNS = [
    "Employee ID",
    "Employee Name",
    "Department",
    "Resign Date",
    "Reason",
]

EMP_FILE_PATH = "employees.csv"
RESIGN_FILE_PATH = "resigned_employees.csv"
PHOTO_FOLDER = "employee_photos"

# --- Sidebar ---
st.sidebar.header("Select Mode")
mode = st.sidebar.selectbox(
    "Choose a module:",
    [
        "Employee Master Data (ဝန်ထမ်းစာရင်း)",
        "Edit/Delete Master Data (ဝန်ထမ်းဒေတာ)",
        "Resign Management (အလုပ်ထွက်စာရင်း)",
        "Excel Bulk Upload (Employee)",
        "Data Entry (Fine System)",
        "View All Records (ဒဏ်ငွေစာရင်းများ)",
        "Search, QR Scan & Edit",
        "Data Backup & GitHub Sync (ဂျစ်ဟပ် စင့်ခ်)",
    ],
    index=0,
)


# --- GitHub Connection Setup ---
@st.cache_resource
def get_github_connection():
    try:
        token = st.secrets["github"]["token"]
        return Github(token)
    except Exception as e:
        st.error(
            f"GitHub Token မတွေ့ရှိပါ။ Secrets ဖိုင်ကို စစ်ဆေးပါ။ Error: {e}"
        )
        return None


def get_repo():
    g = get_github_connection()
    if not g:
        return None
    repo_owner = st.secrets["github"]["repo_owner"]
    repo_name = st.secrets["github"]["repo_name"]
    return g.get_user(repo_owner).get_repo(repo_name)


def get_fine_file_path():
    try:
        return st.secrets["github"].get("file_path", "fine_data.csv")
    except Exception:
        return "fine_data.csv"


def load_csv_from_github(file_path, default_columns):
    repo = get_repo()
    if not repo:
        return pd.DataFrame(columns=default_columns)

    try:
        file_content = repo.get_contents(file_path)
        decoded_content = base64.b64decode(file_content.content).decode("utf-8")
        df = pd.read_csv(io.StringIO(decoded_content), dtype=str).fillna("")
        for col in default_columns:
            if col not in df.columns:
                df[col] = "Active" if col == "Status" else ""
        return df[default_columns]
    except Exception:
        return pd.DataFrame(columns=default_columns)


def save_csv_to_github(df, file_path, commit_message):
    repo = get_repo()
    if not repo:
        return False

    try:
        csv_content = df.to_csv(index=False)
        try:
            existing_file = repo.get_contents(file_path)
            repo.update_file(
                file_path, commit_message, csv_content, existing_file.sha
            )
        except Exception:
            repo.create_file(file_path, commit_message, csv_content)
        return True
    except Exception as e:
        st.error(f"GitHub သို့ ဒေတာသိမ်းဆည်းခြင်း မအောင်မြင်ပါ: {e}")
        return False


def sanitize_name_for_filename(emp_name):
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", emp_name.strip())
    cleaned = re.sub(r"\s+", "_", cleaned).strip("_")
    return cleaned or "employee"


def make_photo_path_by_name(emp_name, ext="png", suffix=""):
    clean_ext = ext.lower().lstrip(".")
    if clean_ext not in ["png", "jpg", "jpeg", "webp"]:
        clean_ext = "png"
    base_name = sanitize_name_for_filename(emp_name)
    if suffix:
        clean_suffix = re.sub(r"[^A-Za-z0-9_-]+", "_", str(suffix).strip()).strip("_")
        if clean_suffix:
            base_name = f"{base_name}_{clean_suffix}"
    return f"{PHOTO_FOLDER}/{base_name}.{clean_ext}"


def upload_photo_bytes_by_name(emp_name, raw_bytes, ext="png", suffix=""):
    if not raw_bytes:
        return ""
    repo = get_repo()
    if not repo:
        return ""

    photo_path = make_photo_path_by_name(emp_name, ext, suffix=suffix)
    try:
        try:
            existing = repo.get_contents(photo_path)
            repo.update_file(
                photo_path,
                f"Update photo for {emp_name.strip()}",
                raw_bytes,
                existing.sha,
            )
        except Exception:
            repo.create_file(
                photo_path, f"Upload photo for {emp_name.strip()}", raw_bytes
            )
        return photo_path
    except Exception as e:
        st.warning(f"ဓာတ်ပုံကို GitHub သို့ တင်ရာတွင် သတိပြုရန်: {e}")
        return ""


def upload_photo_by_name(emp_name, uploaded_file, suffix=""):
    if uploaded_file is None:
        return ""
    ext = (
        uploaded_file.name.split(".")[-1].lower()
        if "." in uploaded_file.name
        else "png"
    )
    return upload_photo_bytes_by_name(
        emp_name, uploaded_file.getvalue(), ext, suffix=suffix
    )


def extract_excel_images_by_row(excel_bytes):
    row_images = {}
    try:
        wb = openpyxl.load_workbook(io.BytesIO(excel_bytes), data_only=True)
        ws = wb.active
        for img in getattr(ws, "_images", []):
            anchor = getattr(img, "anchor", None)
            row_idx = None
            if hasattr(anchor, "_from") and hasattr(anchor._from, "row"):
                row_idx = int(anchor._from.row) + 1
            elif hasattr(anchor, "row"):
                row_idx = int(anchor.row) + 1
            if row_idx is not None:
                img_bytes = img._data()
                fmt = (
                    getattr(img, "format", None)
                    or ("jpeg" if img_bytes[:2] == b"\xff\xd8" else "png")
                ).lower()
                row_images[row_idx] = (img_bytes, fmt)
    except Exception:
        pass
    return row_images


@st.cache_data(ttl=120, show_spinner=False)
def load_photo_bytes_from_github(photo_path):
    if not photo_path or not str(photo_path).strip():
        return None
    try:
        repo = get_repo()
        if not repo:
            return None
        content_file = repo.get_contents(str(photo_path).strip())
        return base64.b64decode(content_file.content)
    except Exception:
        return None


def show_employee_card(emp_id, emp_name="", department="", photo_path="", width=130):
    c_img, c_info = st.columns([1, 4])
    with c_img:
        img_bytes = load_photo_bytes_from_github(photo_path)
        if img_bytes:
            caption_txt = emp_name if emp_name else emp_id
            st.image(img_bytes, width=width, caption=caption_txt)
        else:
            st.info("📷 ဓာတ်ပုံ မရှိပါ")
    with c_info:
        if emp_name:
            st.markdown(f"**Name:** {emp_name}")
        st.markdown(f"**Employee ID:** `{emp_id}`")
        if department:
            st.markdown(f"**Department:** {department}")


def get_employee_lookups(df_emp):
    by_id = {}
    by_name = {}
    if df_emp is None or df_emp.empty:
        return by_id, by_name
    for _, r in df_emp.iterrows():
        eid = str(r.get("Employee ID", "")).strip()
        ename = str(r.get("Employee Name", "")).strip()
        item = {
            "Employee ID": eid,
            "Employee Name": ename,
            "Department": str(r.get("Department", "")).strip(),
            "Join Date": str(r.get("Join Date", "")).strip(),
            "Status": str(r.get("Status", "Active")).strip() or "Active",
            "Photo Path": str(r.get("Photo Path", "")).strip(),
        }
        if eid:
            by_id[eid.lower()] = item
        if ename:
            by_name[ename.lower()] = item
    return by_id, by_name


def find_emp_info(emp_id, emp_name, by_id, by_name):
    if emp_id and emp_id.strip().lower() in by_id:
        return by_id[emp_id.strip().lower()]
    if emp_name and emp_name.strip().lower() in by_name:
        return by_name[emp_name.strip().lower()]
    return {}


# ==========================================
# 1. Employee Master Data (ဝန်ထမ်းစာရင်း)
# ==========================================
if mode == "Employee Master Data (ဝန်ထမ်းစာရင်း)":
    st.header("👤 Employee Master Data (ဝန်ထမ်းစာရင်း ထည့်သွင်းရန်)")
    df_emp = load_csv_from_github(EMP_FILE_PATH, EMP_COLUMNS)

    with st.form("emp_master_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            e_id = st.text_input("Employee ID", placeholder="EMP-0001")
            dept = st.text_input("Department", placeholder="Production")
            photo_file = st.file_uploader(
                "ဝန်ထမ်း ဓာတ်ပုံ (ဝန်ထမ်းအမည်ဖြင့် သိမ်းဆည်းပါမည်)",
                type=["png", "jpg", "jpeg", "webp"],
            )
        with c2:
            e_name = st.text_input("Employee Name", placeholder="Daw Aye Aye Myat")
            j_date = st.date_input("Join Date")
            if photo_file is not None:
                preview_name = e_name.strip() or "Preview"
                st.image(
                    photo_file.getvalue(),
                    width=140,
                    caption=preview_name,
                )

        submitted_emp = st.form_submit_button("Save Employee (ဝန်ထမ်းသိမ်းရန်)")

    if submitted_emp:
        clean_id = e_id.strip()
        clean_name = e_name.strip()
        clean_dept = dept.strip()

        existing_ids = {
            str(x).strip().lower()
            for x in df_emp["Employee ID"].tolist()
            if str(x).strip()
        }

        if not clean_id or not clean_name:
            st.error("❌ Employee ID နှင့် Employee Name မဖြစ်မနေ ထည့်သွင်းရပါမည်။")
        elif clean_id.lower() in existing_ids:
            st.error(
                f"❌ Employee ID '{clean_id}' သည် ရှိပြီးသား ဝန်ထမ်းစာရင်းတွင် ပါဝင်နေပါသည်။ ထပ်မံထည့်သွင်း၍ မရပါ။"
            )
        else:
            existing_names_count = sum(
                1
                for n in df_emp["Employee Name"].tolist()
                if str(n).strip().lower() == clean_name.lower()
            )
            suffix = clean_id if existing_names_count > 0 else ""

            with st.spinner("ဓာတ်ပုံနှင့် ဝန်ထမ်းဒေတာကို GitHub သို့ သိမ်းဆည်းနေပါသည်..."):
                photo_path = upload_photo_by_name(
                    clean_name, photo_file, suffix=suffix
                )
                load_photo_bytes_from_github.clear()
                row = {
                    "Employee ID": clean_id,
                    "Employee Name": clean_name,
                    "Department": clean_dept,
                    "Join Date": j_date.strftime("%Y-%m-%d"),
                    "Status": "Active",
                    "Photo Path": photo_path,
                }
                updated_emp = pd.concat(
                    [df_emp, pd.DataFrame([row])], ignore_index=True
                )
                saved = save_csv_to_github(
                    updated_emp,
                    EMP_FILE_PATH,
                    f"Add employee {clean_name} ({clean_id})",
                )
            if saved:
                st.success(
                    f"✅ ဝန်ထမ်း '{clean_name}' ({clean_id}) ကို GitHub ထဲသို့ တစ်ခါတည်း သိမ်းဆည်းပြီးပါပြီ။"
                )
                st.rerun()

    st.subheader("Saved Employees (သိမ်းဆည်းထားသော ဝန်ထမ်းစာရင်း)")
    if not df_emp.empty:
        emp_opts = [
            f"{r['Employee Name']} ({r['Employee ID']})"
            for _, r in df_emp.iterrows()
        ]
        sel_preview = st.selectbox("ဓာတ်ပုံ ကြည့်ရန် ဝန်ထမ်း ရွေးပါ:", emp_opts)
        p_row = df_emp.iloc[emp_opts.index(sel_preview)]
        show_employee_card(
            p_row["Employee ID"],
            p_row["Employee Name"],
            p_row["Department"],
            p_row.get("Photo Path", ""),
        )
    st.dataframe(df_emp, use_container_width=True)


# ==========================================
# 2. Edit/Delete Master Data (ဝန်ထမ်းဒေတာ)
# ==========================================
elif mode == "Edit/Delete Master Data (ဝန်ထမ်းဒေတာ)":
    st.header("✏️ Edit / Delete Employee Master Data (ဝန်ထမ်းဒေတာ ပြင်ဆင်/ဖျက်ရန်)")
    df_emp = load_csv_from_github(EMP_FILE_PATH, EMP_COLUMNS)

    if df_emp.empty:
        st.info("ဝန်ထမ်းဒေတာ မရှိသေးပါ။")
    else:
        options = [
            f"{r['Employee Name']} ({r['Employee ID']})"
            for _, r in df_emp.iterrows()
        ]
        selected_opt = st.selectbox(
            "တစ်ဦးချင်း ပြင်ဆင်/ဖျက်လိုသော ဝန်ထမ်းကို ရွေးပါ:", options
        )
        idx = options.index(selected_opt)
        current_row = df_emp.iloc[idx]

        show_employee_card(
            current_row["Employee ID"],
            current_row["Employee Name"],
            current_row["Department"],
            current_row.get("Photo Path", ""),
        )

        with st.form("edit_emp_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_id = st.text_input(
                    "Employee ID", value=str(current_row["Employee ID"])
                )
                new_dept = st.text_input(
                    "Department", value=str(current_row["Department"])
                )
                new_status = st.selectbox(
                    "Status",
                    ["Active", "Resigned"],
                    index=(
                        0
                        if str(current_row.get("Status", "Active")) != "Resigned"
                        else 1
                    ),
                )
            with c2:
                new_name = st.text_input(
                    "Employee Name", value=str(current_row["Employee Name"])
                )
                new_join = st.text_input(
                    "Join Date (YYYY-MM-DD)",
                    value=str(current_row["Join Date"]),
                )
                new_photo = st.file_uploader(
                    "ဓာတ်ပုံ အသစ်ပြောင်းရန် (ဝန်ထမ်းအမည်ဖြင့် သိမ်းဆည်းပါမည်)",
                    type=["png", "jpg", "jpeg", "webp"],
                )

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                update_btn = st.form_submit_button(
                    "Update Employee (အချက်အလက် ပြင်ဆင်သိမ်းရန်)"
                )
            with col_btn2:
                delete_btn = st.form_submit_button(
                    "Delete Selected One (ဤဝန်ထမ်းကို ဖျက်ရန်)"
                )

        if update_btn:
            clean_new_id = new_id.strip()
            clean_new_name = new_name.strip()
            other_ids = {
                str(df_emp.at[i, "Employee ID"]).strip().lower()
                for i in df_emp.index
                if i != idx and str(df_emp.at[i, "Employee ID"]).strip()
            }
            if not clean_new_id or not clean_new_name:
                st.error("❌ Employee ID နှင့် Employee Name မဖြစ်မနေ ထည့်ရပါမည်။")
            elif clean_new_id.lower() in other_ids:
                st.error(
                    f"❌ Employee ID '{clean_new_id}' ကို အခြားဝန်ထမ်းတစ်ဦးတွင် အသုံးပြုပြီးသား ဖြစ်နေပါသည်။"
                )
            else:
                photo_path = str(current_row.get("Photo Path", "")).strip()
                if new_photo is not None:
                    dup_name = any(
                        str(df_emp.at[i, "Employee Name"]).strip().lower()
                        == clean_new_name.lower()
                        for i in df_emp.index
                        if i != idx
                    )
                    photo_path = upload_photo_by_name(
                        clean_new_name,
                        new_photo,
                        suffix=clean_new_id if dup_name else "",
                    )
                    load_photo_bytes_from_github.clear()

                df_emp.at[idx, "Employee ID"] = clean_new_id
                df_emp.at[idx, "Employee Name"] = clean_new_name
                df_emp.at[idx, "Department"] = new_dept.strip()
                df_emp.at[idx, "Join Date"] = new_join.strip()
                df_emp.at[idx, "Status"] = new_status
                df_emp.at[idx, "Photo Path"] = photo_path
                if save_csv_to_github(
                    df_emp, EMP_FILE_PATH, f"Update employee {clean_new_name}"
                ):
                    st.success(
                        "✅ ဝန်ထမ်းဒေတာကို ပြင်ဆင်ပြီး GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။"
                    )
                    st.rerun()

        if delete_btn:
            deleted_name = df_emp.at[idx, "Employee Name"]
            df_emp = df_emp.drop(index=idx).reset_index(drop=True)
            if save_csv_to_github(
                df_emp, EMP_FILE_PATH, f"Delete employee {deleted_name}"
            ):
                st.success(
                    "✅ ဝန်ထမ်းဒေတာကို ဖျက်ပြီး GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။"
                )
                st.rerun()

        st.markdown("---")
        st.subheader("🗑️ ဖြတ်ချင်သော ဝန်ထမ်းများကို ရွေးဖျက်ရန် / အားလုံးဖျက်ရန်")

        multi_choices = st.multiselect(
            "ဖျက်လိုသော ဝန်ထမ်းစာရင်းများကို ရွေးချယ်ပါ (တစ်ခုထက်ပို၍ ရွေးနိုင်သည်):",
            options,
        )
        if st.button("Delete Selected Employees (ရွေးချယ်ထားသော ဝန်ထမ်းများကို ဖျက်ပါ)"):
            if not multi_choices:
                st.warning("ဖျက်လိုသော ဝန်ထမ်းကို အနည်းဆုံးတစ်ခု ရွေးချယ်ပါ။")
            else:
                drop_indices = [options.index(item) for item in multi_choices]
                remaining_emp = df_emp.drop(index=drop_indices).reset_index(drop=True)
                with st.spinner("ရွေးချယ်ထားသော ဝန်ထမ်းများကို GitHub မှ ဖျက်နေပါသည်..."):
                    if save_csv_to_github(
                        remaining_emp,
                        EMP_FILE_PATH,
                        f"Delete {len(drop_indices)} selected employees",
                    ):
                        st.success(
                            f"✅ ရွေးချယ်ထားသော ဝန်ထမ်း {len(drop_indices)} ဦးကို ဖျက်ပြီး GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။"
                        )
                        st.rerun()

        with st.expander("⚠️ Delete All Employee Data (ဝန်ထမ်းဒေတာ အားလုံး ဖျက်ရန်)"):
            confirm_all_emp = st.checkbox(
                "ဝန်ထမ်းဒေတာ အားလုံးကို အမှန်တကယ် ဖျက်လိုကြောင်း အတည်ပြုပါသည်",
                key="confirm_del_all_emp",
            )
            if st.button(
                "Delete All Employees Now (ဝန်ထမ်းဒေတာ အားလုံးကို ဖျက်ပါ)",
                type="primary",
            ):
                if not confirm_all_emp:
                    st.error("အရင်ဆုံး အတည်ပြု checkbox ကို အမှန်ခြစ်ပေးပါ။")
                else:
                    empty_emp = pd.DataFrame(columns=EMP_COLUMNS)
                    with st.spinner("ဝန်ထမ်းဒေတာ အားလုံးကို GitHub မှ ဖျက်နေပါသည်..."):
                        if save_csv_to_github(
                            empty_emp,
                            EMP_FILE_PATH,
                            "Delete all employee master data",
                        ):
                            st.success(
                                "✅ ဝန်ထမ်းဒေတာ အားလုံးကို ဖျက်ပြီး GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။"
                            )
                            st.rerun()

        st.markdown("---")
        st.dataframe(df_emp, use_container_width=True)


# ==========================================
# 3. Resign Management (အလုပ်ထွက်စာရင်း)
# ==========================================
elif mode == "Resign Management (အလုပ်ထွက်စာရင်း)":
    st.header("🚪 Resign Management (အလုပ်ထွက် ဝန်ထမ်းစာရင်း စီမံခန့်ခွဲမှု)")
    df_emp = load_csv_from_github(EMP_FILE_PATH, EMP_COLUMNS)
    df_resign = load_csv_from_github(RESIGN_FILE_PATH, RESIGN_COLUMNS)
    by_id, by_name = get_employee_lookups(df_emp)

    master_choices = ["-- Master Data မှ ရွေးရန် --"] + [
        f"{v['Employee Name']} ({v['Employee ID']})" for v in by_id.values()
    ]
    picked_emp = st.selectbox("ဝန်ထမ်းစာရင်းမှ ခေါ်ယူရန်:", master_choices)

    default_r_id = ""
    default_r_name = ""
    default_r_dept = ""
    default_r_photo = ""
    if picked_emp != "-- Master Data မှ ရွေးရန် --":
        match = re.search(r"\(([^()]+)\)\s*$", picked_emp)
        picked_id = match.group(1).strip().lower() if match else ""
        info = by_id.get(picked_id, {})
        default_r_id = info.get("Employee ID", "")
        default_r_name = info.get("Employee Name", "")
        default_r_dept = info.get("Department", "")
        default_r_photo = info.get("Photo Path", "")

    if default_r_id or default_r_name:
        show_employee_card(
            default_r_id, default_r_name, default_r_dept, default_r_photo
        )

    with st.form("resign_form"):
        c1, c2 = st.columns(2)
        with c1:
            r_emp_id = st.text_input("Employee ID", value=default_r_id)
            r_dept = st.text_input("Department", value=default_r_dept)
            r_date = st.date_input("Resign Date (အလုပ်ထွက်သည့် ရက်စွဲ)")
        with c2:
            r_emp_name = st.text_input("Employee Name", value=default_r_name)
            r_reason = st.text_input("Reason (အလုပ်ထွက်ရသည့် အကြောင်းရင်း)")

        resign_sub = st.form_submit_button(
            "Record Resignation (အလုပ်ထွက်စာရင်း သိမ်းရန်)"
        )

    if resign_sub:
        if not r_emp_id.strip() or not r_emp_name.strip():
            st.error("Employee ID နှင့် Employee Name ထည့်သွင်းပါ။")
        else:
            new_resign = {
                "Employee ID": r_emp_id.strip(),
                "Employee Name": r_emp_name.strip(),
                "Department": r_dept.strip(),
                "Resign Date": r_date.strftime("%Y-%m-%d"),
                "Reason": r_reason.strip(),
            }
            df_resign = pd.concat(
                [df_resign, pd.DataFrame([new_resign])], ignore_index=True
            )
            saved_r = save_csv_to_github(
                df_resign,
                RESIGN_FILE_PATH,
                f"Add resign record for {r_emp_name.strip()}",
            )

            if not df_emp.empty:
                mask = (
                    df_emp["Employee ID"].astype(str).str.strip().str.lower()
                    == r_emp_id.strip().lower()
                )
                if mask.any():
                    df_emp.loc[mask, "Status"] = "Resigned"
                    save_csv_to_github(
                        df_emp,
                        EMP_FILE_PATH,
                        f"Mark employee {r_emp_id.strip()} as Resigned",
                    )

            if saved_r:
                st.success("✅ အလုပ်ထွက်စာရင်းကို GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။")
                st.rerun()

    st.subheader("Resigned Employees List (အလုပ်ထွက်ပြီး ဝန်ထမ်းများ)")
    if not df_resign.empty:
        r_opts = [
            f"{r['Employee Name']} ({r['Employee ID']}) - {r['Resign Date']}"
            for _, r in df_resign.iterrows()
        ]
        sel_r = st.selectbox("ဓာတ်ပုံကြည့်ရန် အလုပ်ထွက်ဝန်ထမ်း ရွေးပါ:", r_opts)
        r_row = df_resign.iloc[r_opts.index(sel_r)]
        m_info = find_emp_info(
            str(r_row["Employee ID"]),
            str(r_row["Employee Name"]),
            by_id,
            by_name,
        )
        show_employee_card(
            r_row["Employee ID"],
            r_row["Employee Name"],
            r_row["Department"],
            m_info.get("Photo Path", ""),
        )
    st.dataframe(df_resign, use_container_width=True)


# ==========================================
# 4. Excel Bulk Upload (Employee + Photos by Name)
# ==========================================
elif mode == "Excel Bulk Upload (Employee)":
    st.header("📤 Excel Bulk Upload (Employee Master Data & Photos)")
    st.info(
        "Excel (.xlsx) သို့မဟုတ် CSV (.csv) ဖိုင်တွင် `Employee ID`, `Employee Name`, `Department`, `Join Date` ကော်လံများ ပါဝင်ရပါမည်။ "
        "ဓာတ်ပုံဖိုင်များကို ဝန်ထမ်းအမည်ဖြင့် (ဥပမာ- `Daw Aye Aye Myat.jpg`) တစ်ပြိုင်နက် ရွေးတင်နိုင်သလို Excel ထဲတွင် embedded ဓာတ်ပုံများ ပါရှိပါကလည်း ဝန်ထမ်းအမည်ဖြင့် သိမ်းဆည်းပေးပါမည်။"
    )

    uploaded_file = st.file_uploader(
        "1. Excel သို့မဟုတ် CSV ဖိုင် ရွေးပါ", type=["xlsx", "xls", "csv"]
    )
    uploaded_photos = st.file_uploader(
        "2. ဝန်ထမ်း ဓာတ်ပုံများ တစ်ပြိုင်နက် ရွေးတင်ရန် (ဖိုင်နာမည် = ဝန်ထမ်းအမည်, ဥပမာ Daw Aye Aye Myat.jpg)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
    )

    photo_map_by_name = {}
    if uploaded_photos:
        for p_file in uploaded_photos:
            stem = (
                p_file.name.rsplit(".", 1)[0].strip().lower()
                if "." in p_file.name
                else p_file.name.strip().lower()
            )
            ext = (
                p_file.name.rsplit(".", 1)[1].lower()
                if "." in p_file.name
                else "png"
            )
            photo_map_by_name[stem] = (p_file.getvalue(), ext)

    if uploaded_file is not None:
        try:
            raw_excel_bytes = uploaded_file.getvalue()
            excel_row_images = {}

            if uploaded_file.name.lower().endswith(".csv"):
                df_up = pd.read_csv(io.BytesIO(raw_excel_bytes), dtype=str).fillna(
                    ""
                )
            else:
                df_up = pd.read_excel(
                    io.BytesIO(raw_excel_bytes), dtype=str
                ).fillna("")
                if uploaded_file.name.lower().endswith(".xlsx"):
                    excel_row_images = extract_excel_images_by_row(
                        raw_excel_bytes
                    )

            for col in [
                "Employee ID",
                "Employee Name",
                "Department",
                "Join Date",
                "Photo Path",
            ]:
                if col not in df_up.columns:
                    df_up[col] = ""
            if "Status" not in df_up.columns:
                df_up["Status"] = "Active"

            if "Photo" in df_up.columns:
                for idx_r in df_up.index:
                    if not str(df_up.at[idx_r, "Photo Path"]).strip():
                        p_val = str(df_up.at[idx_r, "Photo"]).strip()
                        if p_val:
                            df_up.at[idx_r, "Photo Path"] = (
                                p_val
                                if "/" in p_val
                                else f"{PHOTO_FOLDER}/{p_val}"
                            )

            df_up = df_up[EMP_COLUMNS].dropna(how="all")

            preview_rows = []
            for df_idx, r in df_up.iterrows():
                eid = str(r["Employee ID"]).strip()
                ename = str(r["Employee Name"]).strip()
                if not eid and not ename:
                    continue
                excel_row_num = df_idx + 2
                has_excel_img = excel_row_num in excel_row_images
                has_uploaded_img = ename.lower() in photo_map_by_name
                has_path = bool(str(r.get("Photo Path", "")).strip())
                photo_status = (
                    "Excel Embedded Photo"
                    if has_excel_img
                    else (
                        "Uploaded Photo (By Name)"
                        if has_uploaded_img
                        else ("Path Specified" if has_path else "No Photo")
                    )
                )
                preview_rows.append(
                    {
                        "Row": excel_row_num,
                        "Employee ID": eid,
                        "Employee Name": ename,
                        "Department": str(r["Department"]).strip(),
                        "Join Date": str(r["Join Date"]).strip(),
                        "Photo Source": photo_status,
                    }
                )

            st.write("Preview Uploaded Data & Photo Mapping:")
            st.dataframe(pd.DataFrame(preview_rows), use_container_width=True)

            if st.button(
                "Import & Save Data & Photos to GitHub (ဒေတာနှင့် ပုံများကို GitHub သို့ ထည့်သွင်းပါ)"
            ):
                df_emp = load_csv_from_github(EMP_FILE_PATH, EMP_COLUMNS)
                existing_ids = {
                    str(x).strip().lower()
                    for x in df_emp["Employee ID"].tolist()
                    if str(x).strip()
                }
                existing_names_lower = [
                    str(n).strip().lower()
                    for n in df_emp["Employee Name"].tolist()
                    if str(n).strip()
                ]
                new_rows = []
                skipped_ids = []
                uploaded_photo_count = 0

                with st.spinner(
                    "ဓာတ်ပုံများနှင့် ဝန်ထမ်းဒေတာများကို GitHub သို့ သိမ်းဆည်းနေပါသည်..."
                ):
                    for df_idx, r in df_up.iterrows():
                        eid = str(r["Employee ID"]).strip()
                        ename = str(r["Employee Name"]).strip()
                        if not eid or not ename:
                            continue
                        if eid.lower() in existing_ids:
                            skipped_ids.append(eid)
                            continue

                        excel_row_num = df_idx + 2
                        saved_photo_path = str(r.get("Photo Path", "")).strip()
                        dup_count = sum(
                            1
                            for n in existing_names_lower
                            if n == ename.lower()
                        )
                        suffix = eid if dup_count > 0 else ""

                        if excel_row_num in excel_row_images:
                            img_bytes, img_ext = excel_row_images[excel_row_num]
                            up_path = upload_photo_bytes_by_name(
                                ename, img_bytes, img_ext, suffix=suffix
                            )
                            if up_path:
                                saved_photo_path = up_path
                                uploaded_photo_count += 1
                        elif ename.lower() in photo_map_by_name:
                            img_bytes, img_ext = photo_map_by_name[
                                ename.lower()
                            ]
                            up_path = upload_photo_bytes_by_name(
                                ename, img_bytes, img_ext, suffix=suffix
                            )
                            if up_path:
                                saved_photo_path = up_path
                                uploaded_photo_count += 1

                        new_rows.append(
                            {
                                "Employee ID": eid,
                                "Employee Name": ename,
                                "Department": str(r["Department"]).strip(),
                                "Join Date": str(r["Join Date"]).strip(),
                                "Status": str(r["Status"]).strip() or "Active",
                                "Photo Path": saved_photo_path,
                            }
                        )
                        existing_ids.add(eid.lower())
                        existing_names_lower.append(ename.lower())

                    if not new_rows:
                        st.warning(
                            "ထည့်သွင်းရန် ID အသစ်မရှိပါ (ရှိပြီးသား ID များသာ ပါဝင်နေပါသည်)။"
                        )
                    else:
                        combined = pd.concat(
                            [df_emp, pd.DataFrame(new_rows)], ignore_index=True
                        )
                        if save_csv_to_github(
                            combined,
                            EMP_FILE_PATH,
                            f"Bulk upload {len(new_rows)} new employees and {uploaded_photo_count} photos",
                        ):
                            load_photo_bytes_from_github.clear()
                            msg = (
                                f"✅ ဝန်ထမ်းဒေတာအသစ် {len(new_rows)} ခုနှင့် "
                                f"ဓာတ်ပုံ {uploaded_photo_count} ပုံကို GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။"
                            )
                            if skipped_ids:
                                msg += f" (ရှိပြီးသား ID {len(skipped_ids)} ခုကို ကျော်သွားပါသည်)"
                            st.success(msg)
                            st.rerun()
        except Exception as e:
            st.error(f"ဖိုင်ဖတ်ရာတွင် အမှားအယွင်းရှိပါသည်: {e}")


# ==========================================
# 5. Data Entry (Fine System)
# ==========================================
elif mode == "Data Entry (Fine System)":
    st.header("Fine Data Management Module (ဒဏ်ငွေဒေတာ စီမံခန့်ခွဲမှု မော်ဂျူး)")
    fine_file = get_fine_file_path()
    df_records = load_csv_from_github(fine_file, FINE_COLUMNS)
    df_emp = load_csv_from_github(EMP_FILE_PATH, EMP_COLUMNS)
    by_id, by_name = get_employee_lookups(df_emp)

    st.subheader("Enter Fine Data (ဒဏ်ငွေဒေတာ ထည့်သွင်းရန်)")

    master_emp_list = ["-- Manual / အသစ်ရိုက်ထည့်ရန် --"] + [
        f"{v['Employee Name']} ({v['Employee ID']})" for v in by_id.values()
    ]
    selected_master = st.selectbox(
        "ဝန်ထမ်းစာရင်းမှ ခေါ်ယူရန် (Employee Master):", master_emp_list
    )

    auto_id = ""
    auto_name = ""
    auto_dept = ""
    auto_photo = ""
    if selected_master != "-- Manual / အသစ်ရိုက်ထည့်ရန် --":
        match = re.search(r"\(([^()]+)\)\s*$", selected_master)
        key_id = match.group(1).strip().lower() if match else ""
        m_data = by_id.get(key_id, {})
        auto_id = m_data.get("Employee ID", "")
        auto_name = m_data.get("Employee Name", "")
        auto_dept = m_data.get("Department", "")
        auto_photo = m_data.get("Photo Path", "")

    category_list = list(FINE_RATES.keys())
    if "fine_amount_val" not in st.session_state:
        st.session_state["fine_amount_val"] = FINE_RATES[category_list[0]]

    def on_category_change():
        selected_cat = st.session_state["fine_category_sel"]
        st.session_state["fine_amount_val"] = FINE_RATES.get(selected_cat, 0)

    col1, col2 = st.columns(2)
    with col1:
        emp_id = st.text_input(
            "Employee ID", value=auto_id, placeholder="EMP-0056"
        )
        fine_category = st.selectbox(
            "Fine Category (ဒဏ်ငွေအမျိုးအစား)",
            category_list,
            key="fine_category_sel",
            on_change=on_category_change,
        )
    with col2:
        emp_name = st.text_input(
            "Employee Name", value=auto_name, placeholder="Daw Aye Aye Myat"
        )
        fine_amount = st.number_input(
            "Fine Amount (ဒဏ်ငွေပမာဏ - ကျပ်)",
            min_value=0,
            step=1000,
            key="fine_amount_val",
        )

    active_lookup_info = find_emp_info(emp_id, emp_name, by_id, by_name)
    preview_photo = active_lookup_info.get("Photo Path", auto_photo)
    preview_dept = active_lookup_info.get("Department", auto_dept)
    if emp_id.strip() or emp_name.strip():
        show_employee_card(
            emp_id.strip(), emp_name.strip(), preview_dept, preview_photo
        )

    fine_date = st.date_input("Date (ရက်စွဲ)")

    if st.button("Add Fine Data (ဒဏ်ငွေထည့်ပါ)"):
        if not emp_id.strip() or not emp_name.strip():
            st.error("Employee ID နှင့် Name မဖြစ်မနေ ထည့်ရပါမည်။")
        else:
            new_entry = {
                "Employee ID": emp_id.strip(),
                "Employee Name": emp_name.strip(),
                "Fine Category": fine_category,
                "Fine Amount": int(fine_amount),
                "Date": fine_date.strftime("%Y-%m-%d"),
            }
            updated_df = pd.concat(
                [df_records, pd.DataFrame([new_entry])], ignore_index=True
            )
            commit_msg = f"Add fine data for {emp_name.strip()} ({emp_id.strip()})"
            if save_csv_to_github(updated_df, fine_file, commit_msg):
                st.success(
                    "✅ ဒဏ်ငွေဒေတာကို GitHub သို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။"
                )
                st.rerun()

    st.markdown("---")
    st.subheader("🔄 Real-time Live Sync Status")
    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        st.markdown(
            "**Auto GitHub Sync:** <span style='color: green;'>**ACTIVE**</span>",
            unsafe_allow_html=True,
        )
    with col_s2:
        st.write(f"**Target File:** `{fine_file}`")
        st.write(
            "Status: All changes are committed & pushed directly to GitHub."
        )

    st.markdown("---")
    st.subheader("Active Fine Data Records (လက်ရှိ ဒဏ်ငွေဒေတာစာရင်းများ)")
    st.dataframe(df_records, use_container_width=True)


# ==========================================
# 6. View All Records (ဒဏ်ငွေစာရင်းများ)
# ==========================================
elif mode == "View All Records (ဒဏ်ငွေစာရင်းများ)":
    st.header("📊 View All Fine Records (ဒဏ်ငွေစာရင်းများ)")
    fine_file = get_fine_file_path()
    df_all = load_csv_from_github(fine_file, FINE_COLUMNS)
    df_emp = load_csv_from_github(EMP_FILE_PATH, EMP_COLUMNS)
    by_id, by_name = get_employee_lookups(df_emp)

    if df_all.empty:
        st.info("ဒဏ်ငွေစာရင်း မရှိသေးပါ။")
    else:
        search_q = st.text_input(
            "ရှာဖွေရန် (Employee ID / Name / Category)", ""
        )
        filtered = df_all.copy()
        if search_q.strip():
            q = search_q.strip().lower()
            mask = filtered.apply(
                lambda r: q in str(r["Employee ID"]).lower()
                or q in str(r["Employee Name"]).lower()
                or q in str(r["Fine Category"]).lower(),
                axis=1,
            )
            filtered = filtered[mask]

        total_amt = (
            pd.to_numeric(filtered["Fine Amount"], errors="coerce")
            .fillna(0)
            .sum()
        )
        st.metric("Total Fine Amount (စုစုပေါင်း ဒဏ်ငွေ)", f"{int(total_amt):,} ကျပ်")

        if not filtered.empty:
            rec_opts = [
                f"#{i+1} | {r['Employee Name']} ({r['Employee ID']}) - {r['Fine Category']} ({r['Date']})"
                for i, r in filtered.iterrows()
            ]
            chosen_rec = st.selectbox("ဓာတ်ပုံ ကြည့်ရန် မှတ်တမ်း ရွေးပါ:", rec_opts)
            chosen_row = filtered.iloc[rec_opts.index(chosen_rec)]
            m_info = find_emp_info(
                str(chosen_row["Employee ID"]),
                str(chosen_row["Employee Name"]),
                by_id,
                by_name,
            )
            show_employee_card(
                chosen_row["Employee ID"],
                chosen_row["Employee Name"],
                m_info.get("Department", ""),
                m_info.get("Photo Path", ""),
            )

        st.dataframe(filtered, use_container_width=True)


# ==========================================
# 7. Search, QR Scan & Edit
# ==========================================
elif mode == "Search, QR Scan & Edit":
    st.header("🔍 Search, QR Code / ID Scan & Edit Fine Records")
    fine_file = get_fine_file_path()
    df_fine = load_csv_from_github(fine_file, FINE_COLUMNS)
    df_emp = load_csv_from_github(EMP_FILE_PATH, EMP_COLUMNS)
    by_id, by_name = get_employee_lookups(df_emp)

    scan_input = st.text_input(
        "QR / Barcode Scan သို့မဟုတ် Employee ID / Name ရိုက်ထည့်ပါ:",
        placeholder="EMP-0056",
    )

    if scan_input.strip():
        q_emp = find_emp_info(scan_input, scan_input, by_id, by_name)
        if q_emp:
            st.success("ဝန်ထမ်း Master Data မှ တွေ့ရှိသော အချက်အလက်:")
            show_employee_card(
                q_emp["Employee ID"],
                q_emp["Employee Name"],
                q_emp["Department"],
                q_emp["Photo Path"],
            )

    if df_fine.empty:
        st.info("ပြင်ဆင်/ဖျက်ရန် ဒဏ်ငွေဒေတာ မရှိသေးပါ။")
    else:
        working_df = df_fine.copy()
        if scan_input.strip():
            q = scan_input.strip().lower()
            matched_indices = [
                i
                for i, r in working_df.iterrows()
                if q in str(r["Employee ID"]).lower()
                or q in str(r["Employee Name"]).lower()
            ]
        else:
            matched_indices = list(working_df.index)

        if not matched_indices:
            st.warning(f"'{scan_input}' နှင့် ကိုက်ညီသော ဒဏ်ငွေမှတ်တမ်း မတွေ့ပါ။")
        else:
            record_labels = [
                f"#{i+1} | {working_df.at[i, 'Employee Name']} ({working_df.at[i, 'Employee ID']}) - {working_df.at[i, 'Fine Category']} ({working_df.at[i, 'Fine Amount']})"
                for i in matched_indices
            ]
            chosen_label = st.selectbox("မှတ်တမ်း ရွေးချယ်ပါ:", record_labels)
            target_idx = matched_indices[record_labels.index(chosen_label)]

            cur_eid = str(df_fine.at[target_idx, "Employee ID"]).strip()
            cur_ename = str(df_fine.at[target_idx, "Employee Name"]).strip()
            m_info = find_emp_info(cur_eid, cur_ename, by_id, by_name)
            show_employee_card(
                cur_eid,
                cur_ename,
                m_info.get("Department", ""),
                m_info.get("Photo Path", ""),
            )

            with st.form("edit_fine_record_form"):
                c1, c2 = st.columns(2)
                with c1:
                    ed_id = st.text_input("Employee ID", value=cur_eid)
                    ed_cat = st.text_input(
                        "Fine Category",
                        value=str(df_fine.at[target_idx, "Fine Category"]),
                    )
                    ed_date = st.text_input(
                        "Date", value=str(df_fine.at[target_idx, "Date"])
                    )
                with c2:
                    ed_name = st.text_input("Employee Name", value=cur_ename)
                    ed_amt = st.number_input(
                        "Fine Amount (ကျပ်)",
                        min_value=0,
                        step=1000,
                        value=int(
                            pd.to_numeric(
                                df_fine.at[target_idx, "Fine Amount"],
                                errors="coerce",
                            )
                            or 0
                        ),
                    )

                b1, b2 = st.columns(2)
                with b1:
                    save_ed = st.form_submit_button("Update Record (ပြင်ဆင်သိမ်းရန်)")
                with b2:
                    del_ed = st.form_submit_button("Delete Record (မှတ်တမ်း ဖျက်ရန်)")

            if save_ed:
                df_fine.at[target_idx, "Employee ID"] = ed_id.strip()
                df_fine.at[target_idx, "Employee Name"] = ed_name.strip()
                df_fine.at[target_idx, "Fine Category"] = ed_cat.strip()
                df_fine.at[target_idx, "Fine Amount"] = int(ed_amt)
                df_fine.at[target_idx, "Date"] = ed_date.strip()
                if save_csv_to_github(
                    df_fine, fine_file, f"Update fine record for {ed_name.strip()}"
                ):
                    st.success(
                        "✅ ဒဏ်ငွေမှတ်တမ်းကို ပြင်ဆင်ပြီး GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။"
                    )
                    st.rerun()

            if del_ed:
                del_name = df_fine.at[target_idx, "Employee Name"]
                df_fine = df_fine.drop(index=target_idx).reset_index(drop=True)
                if save_csv_to_github(
                    df_fine, fine_file, f"Delete fine record for {del_name}"
                ):
                    st.success(
                        "✅ ဒဏ်ငွေမှတ်တမ်းကို ဖျက်ပြီး GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။"
                    )
                    st.rerun()

        st.markdown("---")
        st.subheader("🗑️ ဖြတ်ချင်သော ဒဏ်ငွေမှတ်တမ်းများကို ရွေးဖျက်ရန် / အားလုံးဖျက်ရန်")
        all_fine_labels = [
            f"#{i+1} | {r['Employee Name']} ({r['Employee ID']}) - {r['Fine Category']} ({r['Fine Amount']} - {r['Date']})"
            for i, r in df_fine.iterrows()
        ]
        selected_fine_dels = st.multiselect(
            "ဖျက်လိုသော ဒဏ်ငွေမှတ်တမ်းများကို ရွေးချယ်ပါ:",
            all_fine_labels,
        )
        if st.button("Delete Selected Fine Records (ရွေးချယ်ထားသော မှတ်တမ်းများကို ဖျက်ပါ)"):
            if not selected_fine_dels:
                st.warning("ဖျက်လိုသော မှတ်တမ်းကို အနည်းဆုံးတစ်ခု ရွေးချယ်ပါ။")
            else:
                drop_f_idx = [
                    all_fine_labels.index(lbl) for lbl in selected_fine_dels
                ]
                rem_fine = df_fine.drop(index=drop_f_idx).reset_index(drop=True)
                with st.spinner("ရွေးချယ်ထားသော ဒဏ်ငွေမှတ်တမ်းများကို ဖျက်နေပါသည်..."):
                    if save_csv_to_github(
                        rem_fine,
                        fine_file,
                        f"Delete {len(drop_f_idx)} selected fine records",
                    ):
                        st.success(
                            f"✅ ရွေးချယ်ထားသော ဒဏ်ငွေမှတ်တမ်း {len(drop_f_idx)} ခုကို ဖျက်ပြီး GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။"
                        )
                        st.rerun()

        with st.expander("⚠️ Delete All Fine Records (ဒဏ်ငွေမှတ်တမ်း အားလုံး ဖျက်ရန်)"):
            confirm_all_fine = st.checkbox(
                "ဒဏ်ငွေမှတ်တမ်း အားလုံးကို အမှန်တကယ် ဖျက်လိုကြောင်း အတည်ပြုပါသည်",
                key="confirm_del_all_fine",
            )
            if st.button(
                "Delete All Fine Records Now (ဒဏ်ငွေမှတ်တမ်း အားလုံးကို ဖျက်ပါ)",
                type="primary",
            ):
                if not confirm_all_fine:
                    st.error("အရင်ဆုံး အတည်ပြု checkbox ကို အမှန်ခြစ်ပေးပါ။")
                else:
                    empty_fine = pd.DataFrame(columns=FINE_COLUMNS)
                    with st.spinner("ဒဏ်ငွေမှတ်တမ်း အားလုံးကို GitHub မှ ဖျက်နေပါသည်..."):
                        if save_csv_to_github(
                            empty_fine,
                            fine_file,
                            "Delete all fine records",
                        ):
                            st.success(
                                "✅ ဒဏ်ငွေမှတ်တမ်း အားလုံးကို ဖျက်ပြီး GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။"
                            )
                            st.rerun()


# ==========================================
# 8. Data Backup & GitHub Sync (ဂျစ်ဟပ် စင့်ခ်)
# ==========================================
elif mode == "Data Backup & GitHub Sync (ဂျစ်ဟပ် စင့်ခ်)":
    st.header("☁️ Data Backup & GitHub Sync Module")
    fine_file = get_fine_file_path()
    df_fine_b = load_csv_from_github(fine_file, FINE_COLUMNS)
    df_emp_b = load_csv_from_github(EMP_FILE_PATH, EMP_COLUMNS)
    df_res_b = load_csv_from_github(RESIGN_FILE_PATH, RESIGN_COLUMNS)

    st.write(f"**Fine Data (`{fine_file}`):** {len(df_fine_b)} records")
    st.dataframe(df_fine_b, height=180, use_container_width=True)

    st.write(f"**Employee Master (`{EMP_FILE_PATH}`):** {len(df_emp_b)} records")
    st.dataframe(df_emp_b, height=180, use_container_width=True)

    if st.button(
        "Sync All Data Files to GitHub Now (ဖိုင်အားလုံးကို GitHub သို့ စင့်ခ်လုပ်ပါ)"
    ):
        ok1 = save_csv_to_github(
            df_fine_b, fine_file, "Sync fine data from app"
        )
        ok2 = save_csv_to_github(
            df_emp_b, EMP_FILE_PATH, "Sync employee master data from app"
        )
        ok3 = save_csv_to_github(
            df_res_b, RESIGN_FILE_PATH, "Sync resign data from app"
        )
        if ok1 and ok2 and ok3:
            st.success(
                "✅ ဒေတာဖိုင်အားလုံးကို GitHub သို့ အောင်မြင်စွာ စင့်ခ်လုပ်ပြီးပါပြီ။"
            )

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.text("Powered by kkf-lang Dev Team")
st.sidebar.text("App Version: 2.5.0 (Photo Named by Employee)")