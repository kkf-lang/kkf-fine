from io import BytesIO
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Employee Fine Management System", page_icon="🔒", layout="centered"
)

# --- 1. PASSWORD PROTECTION (စကားဝှက်စစ်ဆေးခြင်း) ---
# လိုအပ်သလို စကားဝှက်ကို ပြောင်းလဲအသုံးပြုနိုင်ပါသည်။
CORRECT_PASSWORD = "admin123"


def check_password():
  """Returns True if the user entered the correct password."""

  def password_entered():
    if st.session_state["password"] == CORRECT_PASSWORD:
      st.session_state["password_correct"] = True
      del st.session_state["password"]  # don't store password
    else:
      st.session_state["password_correct"] = False

  if "password_correct" not in st.session_state:
    # First run, show input for password
    st.markdown("### 🔐 System Login")
    st.text_input(
        "Password ထည့်ပါ", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state and not st.session_state[
        "password_correct"
    ]:
      st.error("😕 စကားဝှက် မှားယွင်းနေပါသည်။ ထပ်မံကြိုးစားပါ။")
    return False
  elif not st.session_state["password_correct"]:
    # Password incorrect, show input again
    st.markdown("### 🔐 System Login")
    st.text_input(
        "Password ထည့်ပါ", type="password", on_change=password_entered, key="password"
    )
    st.error("😕 စကားဝှက် မှားယွင်းနေပါသည်။ ထပ်မံကြိုးစားပါ။")
    return False
  else:
    # Password correct
    return True


if not check_password():
  st.stop()  # စကားဝှက် မှန်ကန်မှသာ အောက်ပါ App ကို ဆက်ဖွင့်မည်

# --- MAIN APP ---
st.title("📋 Employee Fine & Record Management System")
st.write("ဒေတာအရန်သိမ်းဆည်းခြင်း၊ စစ်ထုတ်ခြင်းနှင့် ဒေါင်းလုဒ်ဆွဲနိုင်သော စနစ်။")

# ပုံပါ အချက်အလက်များ (Pre-defined Options)[cite: 1]
departments = ["Extruding", "Weaving", "Mending-1"]  #[cite: 1]
factories = ["KK1", "KK2"]  #[cite: 1]
fine_descriptions = [
    "ကွမ်းစားခြင်း",
    "ဖုန်းတွေ့ရှိခြင်း",
    "နာကြပ်တွေ့ရှိခြင်း",
    "ဆေးလိပ်မီးခြစ်တွေ့ရှိခြင်း",
    "အလုပ်ချိန်အိပ်နေခြင်း",
    "ဝန်ထမ်းကርድမဆွဲခြင်း",
]  #[cite: 1]

# Session State တွင် စာရင်းများ သိမ်းဆည်းရန် Initialize လုပ်ခြင်း
if "records" not in st.session_state:
  st.session_state.records = pd.DataFrame(
      columns=[
          "Employee ID",
          "Name",
          "Department",
          "Factory",
          "Date",
          "Chief",
          "Fine Description",
          "Reported by",
      ]
  )

# --- 2. DATA INPUT FORM ---
with st.form("fine_form", clear_on_submit=True):
  st.subheader("➕ ဝန်ထမ်းပြစ်ချက်/ဒဏ်ငွေ အချက်အလက်များ ထည့်သွင်းရန်")

  employee_id = st.text_input("Employee ID")  #[cite: 1]
  name = st.text_input("Name")  #[cite: 1]

  col1, col2 = st.columns(2)
  with col1:
    department = st.selectbox("Department", departments)  #[cite: 1]
    factory = st.selectbox("Factory", factories)  #[cite: 1]
  with col2:
    date = st.date_input("Date")  #[cite: 1]
    chief = st.text_input("Chief (တာဝန်ခံ)")  #[cite: 1]

  fine_description = st.selectbox(
      "Fine Description", fine_descriptions
  )  #[cite: 1]
  reported_by = st.text_input(
      "Reported by (တင်ပြသူ/စစ်ဆေးသူ)"
  )  #[cite: 1]

  submitted = st.form_submit_button("စာရင်းသွင်းမည် (Submit)")

  if submitted:
    if not employee_id or not name:
      st.warning(
          "ကျေးဇူးပြု၍ Employee ID နှင့် Name ကို ဖြည့်စွက်ပေးပါ။"
      )  #[cite: 1]
    else:
      new_data = {
          "Employee ID": [employee_id],
          "Name": [name],
          "Department": [department],
          "Factory": [factory],
          "Date": [str(date)],
          "Chief": [chief],
          "Fine Description": [fine_description],
          "Reported by": [reported_by],
      }
      df_new = pd.DataFrame(new_data)
      st.session_state.records = pd.concat(
          [st.session_state.records, df_new], ignore_index=True
      )
      st.success("ဒဏ်ငွေစာရင်းကို အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။")

st.markdown("---")

# --- 3. FILTER SECTION (စစ်ထုတ်ခြင်း) ---
st.subheader("🔍 စာရင်းများ စစ်ထုတ်ရန် (Filter)")

if not st.session_state.records.empty:
  f_col1, f_col2, f_col3 = st.columns(3)

  with f_col1:
    selected_dept = st.selectbox(
        "Department အလိုက် စစ်ထုတ်ရန်",
        ["အားလုံး"] + list(st.session_state.records["Department"].unique()),
    )
  with f_col2:
    selected_factory = st.selectbox(
        "Factory အလိုက် စစ်ထုတ်ရန်",
        ["အားလုံး"] + list(st.session_state.records["Factory"].unique()),
    )
  with f_col3:
    selected_fine = st.selectbox(
        "Fine Description အလိုက် စစ်ထုတ်ရန်",
        ["အားလုံး"] + list(st.session_state.records["Fine Description"].unique()),
    )

  # Filtering Logic
  df_filtered = st.session_state.records.copy()
  if selected_dept != "အားလုံး":
    df_filtered = df_filtered[df_filtered["Department"] == selected_dept]
  if selected_factory != "အားလုံး":
    df_filtered = df_filtered[df_filtered["Factory"] == selected_factory]
  if selected_fine != "အားလုံး":
    df_filtered = df_filtered[
        df_filtered["Fine Description"] == selected_fine
    ]

  st.write(f"ပြသရန် ရလဒ် စုစုပေါင်း: **{len(df_filtered)}** ခု")
  st.dataframe(df_filtered, use_container_width=True)

  # --- 4. DOWNLOAD & BACKUP SECTION (ဒေါင်းလုဒ်ဆွဲခြင်း နှင့် အရန်သိမ်းဆည်းခြင်း) ---
  st.markdown("---")
  st.subheader("📥 Download & Data Backup")

  d_col1, d_col2 = st.columns(2)

  with d_col1:
    # CSV Download (Filtered or All)
    csv_data = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📄 CSV ဖိုင်ဖြင့် ဒေါင်းလုဒ်လုပ်ရန်",
        data=csv_data,
        file_name="filtered_employee_fines.csv",
        mime="text/csv",
    )

  with d_col2:
    # Excel Backup Download
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
      st.session_state.records.to_excel(
          writer, sheet_name="All_Records", index=False
      )
    excel_data = output.getvalue()

    st.download_button(
        label="💾 Excel ဖြင့် Data Backup ရယူရန်",
        data=excel_data,
        file_name="employee_fines_backup.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

  # --- 5. UPLOAD BACKUP (အရန်သိမ်းထားသော ဖိုင်ကို ပြန်လည်တင်သွင်းရန်) ---
  st.markdown("---")
  st.subheader("ຸ Upload & Restore Backup")
  uploaded_backup = st.file_uploader(
      "ယခင်က Backup လုပ်ထားသော Excel/CSV ဖိုင်ကို ပြန်လည်တင်ရန်",
      type=["csv", "xlsx"],
  )
  if uploaded_backup is not None:
    if uploaded_backup.name.endswith(".csv"):
      restored_df = pd.read_csv(uploaded_backup)
    else:
      restored_df = pd.read_excel(uploaded_backup)

    if st.button("🔄 Data များကို Restore လုပ်မည်"):
      st.session_state.records = restored_df
      st.success("Data များကို အောင်မြင်စွာ ပြန်လည်ဖော်ဆောင်ပြီးပါပြီ။")
      st.rerun()

else:
  st.info("လက်လောဆယ်တွင် စာရင်းသွင်းထားသော အချက်အလက် မရှိသေးပါ။")