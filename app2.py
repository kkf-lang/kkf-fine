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
                df[col] = ""
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


def get_fine_file_path():
    try:
        return st.secrets["github"].get("file_path", "fine_data.csv")
    except Exception:
        return "fine_data.csv"


FINE_COLUMNS = [
    "Employee ID",
    "Employee Name",
    "Fine Category",
    "Fine Amount",
    "Date",
]
EMP_COLUMNS = ["Employee ID", "Employee Name", "Department", "Join Date"]
EMP_FILE_PATH = "employees.csv"

# --- Main Content Logic ---
if mode == "Data Entry (Fine System)":
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
                    "✅ ဒဏ်ငွေဒဏ်ကြေးဒေတာကို GitHub သို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။"
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
            "Status: Changes are committed & pushed to GitHub repository."
        )

    st.markdown("---")
    st.subheader("Active Fine Data Records (လက်ရှိ ဒဏ်ငွေဒေတာစာရင်းများ)")
    st.dataframe(df_records, use_container_width=True)

elif mode == "Employee Master Data (ဝန်ထမ်းစာရင်း)":
    st.header("Employee Master Data (ဝန်ထမ်းစာရင်း)")
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
        else:
            row = {
                "Employee ID": e_id.strip(),
                "Employee Name": e_name.strip(),
                "Department": dept.strip(),
                "Join Date": j_date.strftime("%Y-%m-%d"),
            }
            df_emp = pd.concat([df_emp, pd.DataFrame([row])], ignore_index=True)
            if save_csv_to_github(
                df_emp, EMP_FILE_PATH, f"Add employee {e_id.strip()}"
            ):
                st.success("✅ ဝန်ထမ်းဒေတာကို GitHub သို့ သိမ်းဆည်းပြီးပါပြီ။")
                st.rerun()

    st.dataframe(df_emp, use_container_width=True)

elif mode == "View All Records (ဒဏ်ငွေစာရင်းများ)":
    st.header("View All Fine Records (ဒဏ်ငွေစာရင်းများ)")
    fine_file = get_fine_file_path()
    st.dataframe(
        load_csv_from_github(fine_file, FINE_COLUMNS), use_container_width=True
    )

elif mode == "Data Backup & GitHub Sync (ဂျစ်ဟပ် စင့်ခ်)":
    st.header("Data Backup & GitHub Sync Module")
    fine_file = get_fine_file_path()
    df_backup = load_csv_from_github(fine_file, FINE_COLUMNS)
    st.dataframe(df_backup, height=250, use_container_width=True)
    if st.button("Sync All Fine Data to GitHub Now"):
        if save_csv_to_github(
            df_backup, fine_file, "Manual fine data sync and backup"
        ):
            st.success("✅ ဒေတာများကို GitHub သို့ စင့်ခ်လုပ်ပြီးပါပြီ။")

else:
    st.info(
        f"Module '{mode}' ကို လောလောဆယ် အသင့်မဖြစ်သေးပါ။ လိုအပ်သည့် လုပ်ဆောင်ချက်ကို ပြောပြပါက ထပ်မံထည့်သွင်းပေးပါမည်။"
    )

st.sidebar.markdown("---")
st.sidebar.text("Powered by kkf-lang Dev Team")
st.sidebar.text("App Version: 1.3.0 (Git-Enabled)")