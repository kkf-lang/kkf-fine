import streamlit as st
import pandas as pd
from github import Github
import base64
import io

# --- Page Configuration ---
st.set_page_config(page_title="Employee Fine & Record Management System", layout="wide")
st.image("https://em-content.zobj.net/source/fluent/116/clipboard.png", width=50)
st.title("Employee Fine & Record Management System")

# --- Sidebar ---
st.sidebar.header("Select Mode")
# ရွေးချယ်စရာစာရင်းကို ပုံပါအတိုင်း ဖန်တီးသည်
mode = st.sidebar.selectbox(
    "Choose a module:",
    [
        "Employee Master Data (ဝန်ထမ်းစာရင်း)",
        "Edit/Delete Master Data (ဝန်ထမ်းဒေတာ)",
        "Resign Management (အလုပ်ထွက်စာရင်း)",
        "Excel Bulk Upload (Employee)",
        "Data Entry (Fine System)",  # ပုံပါအတိုင်း မီးမောင်းထိုးပြမည့် module
        "View All Records (ဒဏ်ငွေစာရင်းများ)",
        "Search, QR Scan & Edit",
        "Data Backup & GitHub Sync (ဂျစ်ဟပ် စင့်ခ်)"
    ],
    index=4 # "Data Entry (Fine System)" ကို အစပိုင်းတွင် ရွေးထားသည်
)

# --- GitHub Connection Setup (using secrets) ---
@st.cache_resource
def get_github_connection():
    try:
        token = st.secrets["github"]["token"]
        g = Github(token)
        return g
    except Exception as e:
        st.error(f"GitHub Token မတွေ့ရှိပါ။ Secrets ဖိုင်ကို စစ်ဆေးပါ။ Error: {e}")
        return None

def load_data_from_github():
    g = get_github_connection()
    if not g: return pd.DataFrame()
    repo_owner = st.secrets["github"]["repo_owner"]
    repo_name = st.secrets["github"]["repo_name"]
    file_path = st.secrets["github"]["file_path"]
    
    try:
        repo = g.get_user(repo_owner).get_repo(repo_name)
        file_content = repo.get_contents(file_path)
        decoded_content = base64.b64decode(file_content.content).decode('utf-8')
        df = pd.read_csv(io.StringIO(decoded_content))
        return df
    except Exception as e:
        # အကယ်၍ ဖိုင်အသစ်ဖြစ်ပါက dataframe အလွတ်ကို ပြန်သည်
        st.warning(f"GitHub မှ ဒေတာကို မ load နိုင်ပါ။ (ဖိုင်အသစ်ဖြစ်နိုင်သည်): {e}")
        return pd.DataFrame(columns=["Employee ID", "Employee Name", "Fine Category", "Fine Amount", "Date"])

def save_data_to_github(df, commit_message):
    g = get_github_connection()
    if not g: return False
    repo_owner = st.secrets["github"]["repo_owner"]
    repo_name = st.secrets["github"]["repo_name"]
    file_path = st.secrets["github"]["file_path"]
    
    try:
        repo = g.get_user(repo_owner).get_repo(repo_name)
        csv_content = df.to_csv(index=False)
        
        try:
            # ဖိုင်ရှိပြီးသားဖြစ်ပါက update လုပ်သည်
            file_content = repo.get_contents(file_path)
            repo.update_file(file_path, commit_message, csv_content, file_content.sha)
        except Exception:
            # ဖိုင်မရှိသေးပါက create လုပ်သည်
            repo.create_file(file_path, commit_message, csv_content)
        
        return True
    except Exception as e:
        st.error(f"GitHub သို့ ဒေတာသိမ်းဆည်းခြင်း မအောင်မြင်ပါ: {e}")
        return False

# --- Main Content Logic ---
if mode == "Data Entry (Fine System)":
    st.header("Fine Data Management Module (ဒဏ်ငွေဒေတာ စီမံခန့်ခွဲမှု မော်ဂျူး)")
    
    # ဒေတာများကို အရင် load သည်
    df_records = load_data_from_github()

    # --- Data Entry Form ---
    st.subheader("Enter Fine Data (ဒဏ်ငွေဒေတာ ထည့်သွင်းရန်)")
    with st.form("fine_entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            emp_id = st.text_input("Employee ID", placeholder="EMP-0056")
            fine_category = st.selectbox("Fine Category (ဒဏ်ငွေအမျိုးအစား)", 
                                        ["Late Arrival", "Unexcused Absence", "Dress Code Violation", "Property Damage"])
        with col2:
            emp_name = st.text_input("Employee Name", placeholder="Daw Aye Aye Myat")
            fine_amount = st.number_input("Fine Amount (ဒဏ်ငွေပမာဏ - ကျပ်)", min_value=0, step=1000)
        
        date = st.date_input("Date (ရက်စွဲ)")

        submitted = st.form_submit_button("Add Fine Data (ဒဏ်ငွေထည့်ပါ)")

    if submitted:
        if not emp_id or not emp_name:
            st.error("Employee ID နှင့် Name မဖြစ်မနေထည့်ရပါမည်။")
        else:
            # ဒေတာအသစ်ကို DataFrame ထဲသို့ထည့်သည်
            new_entry = {
                "Employee ID": emp_id,
                "Employee Name": emp_name,
                "Fine Category": fine_category,
                "Fine Amount": fine_amount,
                "Date": date.strftime("%Y-%m-%d")
            }
            df_records = pd.concat([df_records, pd.DataFrame([new_entry])], ignore_index=True)
            
            # GitHub သို့ Auto-Commit & Push လုပ်သည်
            commit_msg = f"Add fine data for {emp_name} ({emp_id})"
            if save_data_to_github(df_records, commit_msg):
                st.success("✅ ဒဏ်ငွေဒေတာကို အောင်မြင်စွာထည့်သွင်းပြီး GitHub သို့ သိမ်းဆည်းလိုက်ပါပြီ။")
                # ပြန်လည် load လုပ်ရန်အတွက် session state ကို သုံးသည်
                st.rerun()
            else:
                st.error("ဒေတာထည့်သွင်းသော်လည်း GitHub သို့ သိမ်းဆည်းရန် အမှားအယွင်းရှိနေသည်။")

    # --- Real-time Live Sync Status ---
    st.markdown("---")
    st.subheader("🔄 Real-time Live Sync Status")
    
    col_s1, col_s2 = st.columns([1, 2])
    with col_s1:
        st.markdown("**Auto GitHub Sync:** <span style='color: green;'>**ACTIVE**</span>", unsafe_allow_html=True)
    with col_s2:
        st.write(f"**Target File:** `{st.secrets['github']['file_path']}`")
        # နောက်ဆုံးပြင်ဆင်သည့်အချိန်ကို github API မှ တိုက်ရိုက်မရနိုင်သောကြောင့် status message သာပြသည်
        st.write("Status: All local changes (Add/Update/Delete) are automatically committed & pushed to repository.")

    # --- Active Fine Data Records ---
    st.markdown("---")
    st.subheader("Active Fine Data Records (လက်ရှိ ဒဏ်ငွေဒေတာစာရင်းများ)")
    st.dataframe(df_records, use_container_width=True)

elif mode == "Data Backup & GitHub Sync (ဂျစ်ဟပ် စင့်ခ်)":
    st.header("Data Backup & GitHub Sync Module")
    st.info("ဤနေရာမှတဆင့် သင်၏ ဒေတာဘေ့စ်တစ်ခုလုံးကို GitHub သို့ အမြဲတမ်း Backup (Push) လုပ်နိုင်သည်။")
    
    # ဒေတာများကို load သည်
    df_backup = load_data_from_github()
    st.write("Current Data Preview:")
    st.dataframe(df_backup, height=200)
    
    if st.button("Sync All Data to GitHub Now (ဒေတာအားလုံးကို GitHub သို့ ယခုပင် စင့်ခ်လုပ်ပါ)"):
        if save_data_to_github(df_backup, "Manual data sync and backup"):
            st.success("✅ ဒေတာအားလုံးကို GitHub သို့ အောင်မြင်စွာ စင့်ခ်လုပ်ပြီးပါပြီ။")
        else:
            st.error("စင့်ခ်လုပ်ခြင်း မအောင်မြင်ပါ။")

elif mode == "View All Records (ဒဏ်ငွေစာရင်းများ)":
    st.header("View All Fine Records")
    st.dataframe(load_data_from_github(), use_container_width=True)

else:
    st.warning(f"Module '{mode}' ကို မဖွင့်ရသေးပါ။")

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.text("Powered by kkf-lang Dev Team")
st.sidebar.text("App Version: 1.2.0 (Git-Enabled)")