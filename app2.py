import base64
import io
from github import Github
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
EMP_COLUMNS = ["Employee ID", "Employee Name", "Department", "Join Date", "Status"]
RESIGN_COLUMNS = [
    "Employee ID",
    "Employee Name",
    "Department",
    "Resign Date",
    "Reason",
]

EMP_FILE_PATH = "employees.csv"
RESIGN_FILE_PATH = "resigned_employees.csv"

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
    index=4,
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


def get_fine_file_path():
    try:
        return st.secrets["github"].get("file_path", "fine_data.csv")
    except Exception:
        return "fine_data.csv"


def load_csv_from_github(file_path, default_columns):
    g = get_github_connection()
    if not g:
        return pd.DataFrame(columns=default_columns)

    repo_owner = st.secrets["github"]["repo_owner"]
    repo_name = st.secrets["github"]["repo_name"]

    try:
        repo = g.get_user(repo_owner).get_repo(repo_name)
        file_content = repo.get_contents(file_path)
        decoded_content = base64.b64decode(file_content.content).decode("utf-8")
        df = pd.read_csv(io.StringIO(decoded_content))
        for col in default_columns:
            if col not in df.columns:
                df[col] = "Active" if col == "Status" else ""
        return df[default_columns]
    except Exception:
        return pd.DataFrame(columns=default_columns)


def save_csv_to_github(df, file_path, commit_message):
    g = get_github_connection()
    if not g:
        return False

    repo_owner = st.secrets["github"]["repo_owner"]
    repo_name = st.secrets["github"]["repo_name"]

    try:
        repo = g.get_user(repo_owner).get_repo(repo_name)
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


# ==========================================
# 1. Employee Master Data (ဝန်ထမ်းစာရင်း)
# ==========================================
if mode == "Employee Master Data (ဝန်ထမ်းစာရင်း)":
    st.header("👤 Employee Master Data (ဝန်ထမ်းစာရင်း ထည့်သွင်းရန်)")
    df_emp = load_csv_from_github(EMP_FILE_PATH, EMP_COLUMNS)

    with st.form("emp_master_form"):
        c1, c2 = st.columns(2)
        with c1:
            e_id = st.text_input("Employee ID", placeholder="EMP-0001")
            dept = st.text_input("Department", placeholder="Production")
        with c2:
            e_name = st.text_input("Employee Name", placeholder="U Kyaw Kyaw")
            j_date = st.date_input("Join Date")
        submitted_emp = st.form_submit_button("Save Employee (ဝန်ထမ်းသိမ်းရန်)")

    if submitted_emp:
        if not e_id.strip() or not e_name.strip():
            st.error("Employee ID နှင့် Employee Name ထည့်သွင်းပါ။")
        elif e_id.strip() in df_emp["Employee ID"].astype(str).values:
            st.warning(
                f"Employee ID '{e_id.strip()}' ရှိပြီးသား ဖြစ်နေပါသည်။ Edit/Delete module မှ ပြင်ဆင်နိုင်ပါသည်။"
            )
        else:
            row = {
                "Employee ID": e_id.strip(),
                "Employee Name": e_name.strip(),
                "Department": dept.strip(),
                "Join Date": j_date.strftime("%Y-%m-%d"),
                "Status": "Active",
            }
            df_emp = pd.concat([df_emp, pd.DataFrame([row])], ignore_index=True)
            if save_csv_to_github(
                df_emp, EMP_FILE_PATH, f"Add employee {e_id.strip()}"
            ):
                st.success("✅ ဝန်ထမ်းဒေတာကို GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။")
                st.rerun()

    st.subheader("Saved Employees (သိမ်းဆည်းထားသော ဝန်ထမ်းစာရင်း)")
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
            f"{r['Employee ID']} - {r['Employee Name']}"
            for _, r in df_emp.iterrows()
        ]
        selected_opt = st.selectbox(
            "ပြင်ဆင်/ဖျက်လိုသော ဝန်ထမ်းကို ရွေးပါ:", options
        )
        idx = options.index(selected_opt)
        current_row = df_emp.iloc[idx]

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

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                update_btn = st.form_submit_button(
                    "Update Employee (အချက်အလက် ပြင်ဆင်သိမ်းရန်)"
                )
            with col_btn2:
                delete_btn = st.form_submit_button(
                    "Delete Employee (ဝန်ထမ်း ဖျက်ရန်)"
                )

        if update_btn:
            df_emp.at[idx, "Employee ID"] = new_id.strip()
            df_emp.at[idx, "Employee Name"] = new_name.strip()
            df_emp.at[idx, "Department"] = new_dept.strip()
            df_emp.at[idx, "Join Date"] = new_join.strip()
            df_emp.at[idx, "Status"] = new_status
            if save_csv_to_github(
                df_emp, EMP_FILE_PATH, f"Update employee {new_id.strip()}"
            ):
                st.success("✅ ဝန်ထမ်းဒေတာကို ပြင်ဆင်ပြီး GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။")
                st.rerun()

        if delete_btn:
            deleted_id = df_emp.at[idx, "Employee ID"]
            df_emp = df_emp.drop(index=idx).reset_index(drop=True)
            if save_csv_to_github(
                df_emp, EMP_FILE_PATH, f"Delete employee {deleted_id}"
            ):
                st.success("✅ ဝန်ထမ်းဒေတာကို ဖျက်ပြီး GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။")
                st.rerun()

        st.dataframe(df_emp, use_container_width=True)


# ==========================================
# 3. Resign Management (အလုပ်ထွက်စာရင်း)
# ==========================================
elif mode == "Resign Management (အလုပ်ထွက်စာရင်း)":
    st.header("🚪 Resign Management (အလုပ်ထွက် ဝန်ထမ်းစာရင်း စီမံခန့်ခွဲမှု)")
    df_emp = load_csv_from_github(EMP_FILE_PATH, EMP_COLUMNS)
    df_resign = load_csv_from_github(RESIGN_FILE_PATH, RESIGN_COLUMNS)

    with st.form("resign_form"):
        c1, c2 = st.columns(2)
        with c1:
            r_emp_id = st.text_input("Employee ID", placeholder="EMP-0001")
            r_dept = st.text_input("Department", placeholder="Production")
            r_date = st.date_input("Resign Date (အလုပ်ထွက်သည့် ရက်စွဲ)")
        with c2:
            r_emp_name = st.text_input("Employee Name", placeholder="U Kyaw Kyaw")
            r_reason = st.text_input("Reason (အလုပ်ထွက်ရသည့် အကြောင်းရင်း)")

        resign_sub = st.form_submit_button("Record Resignation (အလုပ်ထွက်စာရင်း သိမ်းရန်)")

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
                f"Add resign record for {r_emp_id.strip()}",
            )

            # Master Data ထဲမှာ ရှိနေရင် Status ကို Resigned ပြောင်းပေးမည်
            if not df_emp.empty and r_emp_id.strip() in df_emp["Employee ID"].astype(str).values:
                df_emp.loc[
                    df_emp["Employee ID"].astype(str) == r_emp_id.strip(),
                    "Status",
                ] = "Resigned"
                save_csv_to_github(
                    df_emp,
                    EMP_FILE_PATH,
                    f"Mark employee {r_emp_id.strip()} as Resigned",
                )

            if saved_r:
                st.success("✅ အလုပ်ထွက်စာရင်းကို GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။")
                st.rerun()

    st.subheader("Resigned Employees List (အလုပ်ထွက်ပြီး ဝန်ထမ်းများ)")
    st.dataframe(df_resign, use_container_width=True)


# ==========================================
# 4. Excel Bulk Upload (Employee)
# ==========================================
elif mode == "Excel Bulk Upload (Employee)":
    st.header("📤 Excel Bulk Upload (Employee Master Data)")
    st.info(
        "Excel (.xlsx) သို့မဟုတ် CSV (.csv) ဖိုင်တွင် `Employee ID`, `Employee Name`, `Department`, `Join Date` ကော်လံများ ပါဝင်ရပါမည်။"
    )

    uploaded_file = st.file_uploader(
        "Choose Excel or CSV file", type=["xlsx", "xls", "csv"]
    )
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df_up = pd.read_csv(uploaded_file)
            else:
                df_up = pd.read_excel(uploaded_file)

            for col in ["Employee ID", "Employee Name", "Department", "Join Date"]:
                if col not in df_up.columns:
                    df_up[col] = ""
            if "Status" not in df_up.columns:
                df_up["Status"] = "Active"

            df_up = df_up[EMP_COLUMNS].dropna(how="all")
            st.write("Preview Uploaded Data:")
            st.dataframe(df_up, use_container_width=True)

            if st.button("Import & Save to GitHub (ဒေတာများကို GitHub သို့ ထည့်သွင်းပါ)"):
                df_emp = load_csv_from_github(EMP_FILE_PATH, EMP_COLUMNS)
                combined = pd.concat([df_emp, df_up], ignore_index=True)
                combined = combined.drop_duplicates(
                    subset=["Employee ID"], keep="last"
                ).reset_index(drop=True)

                if save_csv_to_github(
                    combined,
                    EMP_FILE_PATH,
                    f"Bulk upload {len(df_up)} employees",
                ):
                    st.success(
                        f"✅ ဝန်ထမ်းဒေတာ {len(df_up)} ခုကို GitHub သို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။"
                    )
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

    st.subheader("Enter Fine Data (ဒဏ်ငွေဒေတာ ထည့်သွင်းရန်)")

    category_list = list(FINE_RATES.keys())
    if "fine_amount_val" not in st.session_state:
        st.session_state["fine_amount_val"] = FINE_RATES[category_list[0]]

    def on_category_change():
        selected_cat = st.session_state["fine_category_sel"]
        st.session_state["fine_amount_val"] = FINE_RATES.get(selected_cat, 0)

    col1, col2 = st.columns(2)
    with col1:
        emp_id = st.text_input("Employee ID", placeholder="EMP-0056")
        fine_category = st.selectbox(
            "Fine Category (ဒဏ်ငွေအမျိုးအစား)",
            category_list,
            key="fine_category_sel",
            on_change=on_category_change,
        )
    with col2:
        emp_name = st.text_input("Employee Name", placeholder="Daw Aye Aye Myat")
        fine_amount = st.number_input(
            "Fine Amount (ဒဏ်ငွေပမာဏ - ကျပ်)",
            min_value=0,
            step=1000,
            key="fine_amount_val",
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

        total_amt = pd.to_numeric(
            filtered["Fine Amount"], errors="coerce"
        ).fillna(0).sum()
        st.metric("Total Fine Amount (စုစုပေါင်း ဒဏ်ငွေ)", f"{int(total_amt):,} ကျပ်")
        st.dataframe(filtered, use_container_width=True)


# ==========================================
# 7. Search, QR Scan & Edit
# ==========================================
elif mode == "Search, QR Scan & Edit":
    st.header("🔍 Search, QR Code / ID Scan & Edit Fine Records")
    fine_file = get_fine_file_path()
    df_fine = load_csv_from_github(fine_file, FINE_COLUMNS)

    scan_input = st.text_input(
        "QR / Barcode Scan သို့မဟုတ် Employee ID ရိုက်ထည့်ပါ:",
        placeholder="EMP-0056",
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
            st.warning(f"'{scan_input}' နှင့် ကိုက်ညီသော မှတ်တမ်း မတွေ့ပါ။")
        else:
            record_labels = [
                f"#{i+1} | {working_df.at[i, 'Employee ID']} - {working_df.at[i, 'Employee Name']} | {working_df.at[i, 'Fine Category']} ({working_df.at[i, 'Fine Amount']})"
                for i in matched_indices
            ]
            chosen_label = st.selectbox("မှတ်တမ်း ရွေးချယ်ပါ:", record_labels)
            target_idx = matched_indices[record_labels.index(chosen_label)]

            with st.form("edit_fine_record_form"):
                c1, c2 = st.columns(2)
                with c1:
                    ed_id = st.text_input(
                        "Employee ID", value=str(df_fine.at[target_idx, "Employee ID"])
                    )
                    ed_cat = st.text_input(
                        "Fine Category",
                        value=str(df_fine.at[target_idx, "Fine Category"]),
                    )
                    ed_date = st.text_input(
                        "Date", value=str(df_fine.at[target_idx, "Date"])
                    )
                with c2:
                    ed_name = st.text_input(
                        "Employee Name",
                        value=str(df_fine.at[target_idx, "Employee Name"]),
                    )
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
                    df_fine, fine_file, f"Update fine record for {ed_id.strip()}"
                ):
                    st.success("✅ ဒဏ်ငွေမှတ်တမ်းကို ပြင်ဆင်ပြီး GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။")
                    st.rerun()

            if del_ed:
                del_id = df_fine.at[target_idx, "Employee ID"]
                df_fine = df_fine.drop(index=target_idx).reset_index(drop=True)
                if save_csv_to_github(
                    df_fine, fine_file, f"Delete fine record for {del_id}"
                ):
                    st.success("✅ ဒဏ်ငွေမှတ်တမ်းကို ဖျက်ပြီး GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။")
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

    if st.button("Sync All Data Files to GitHub Now (ဖိုင်အားလုံးကို GitHub သို့ စင့်ခ်လုပ်ပါ)"):
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
            st.success("✅ ဒေတာဖိုင်အားလုံးကို GitHub သို့ အောင်မြင်စွာ စင့်ခ်လုပ်ပြီးပါပြီ။")

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.text("Powered by kkf-lang Dev Team")
st.sidebar.text("App Version: 2.0.0 (Full Git-Sync)")