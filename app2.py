from io import BytesIO
import pandas as pd
import qrcode
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Employee Fine Management System", page_icon="📋", layout="wide"
)

# --- 1. PASSWORD PROTECTION ---
CORRECT_PASSWORD = "admin123"


def check_password():
  def password_entered():
    if st.session_state["password"] == CORRECT_PASSWORD:
      st.session_state["password_correct"] = True
      del st.session_state["password"]
    else:
      st.session_state["password_correct"] = False

  if "password_correct" not in st.session_state:
    st.markdown("### 🔐 System Login")
    st.text_input(
        "Password ထည့်ပါ", type="password", on_change=password_entered, key="password"
    )
    return False
  elif not st.session_state["password_correct"]:
    st.markdown("### 🔐 System Login")
    st.text_input(
        "Password ထည့်ပါ", type="password", on_change=password_entered, key="password"
    )
    st.error("😕 စကားဝှက် မှားယွင်းနေပါသည်။")
    return False
  else:
    return True


if not check_password():
  st.stop()

# --- MAIN APP ---
st.title("📋 Employee Fine & Record Management System")

# Options
departments = ["Extruding", "Weaving", "Mending-1"]
factories = ["KK1", "KK2"]
fine_descriptions = [
    "ကွမ်းစားခြင်း",
    "ဖုန်းတွေ့ရှိခြင်း",
    "နာကြပ်တွေ့ရှိခြင်း",
    "ဆေးလိပ်မီးခြစ်တွေ့ရှိခြင်း",
    "အလုပ်ချိန်အိပ်နေခြင်း",
    "ဝန်ထမ်းကርድမဆွဲခြင်း",
]

# Session State Initialize
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
          "Photo URL",
      ]
  )

if "employee_master" not in st.session_state:
  st.session_state.employee_master = pd.DataFrame(
      columns=["Photo", "Employee ID", "Name", "Department", "Join Date"]
  )

if "resign_records" not in st.session_state:
  st.session_state.resign_records = pd.DataFrame(
      columns=["Photo", "Employee ID", "Name", "Department", "Join Date"]
  )

# Navigation Menu
menu = st.sidebar.selectbox(
    "Select Mode",
    [
        "Employee Master Data (ဝန်ထမ်းစာရင်း)",
        "Resign Management (အလုပ်ထွက်စာရင်း)",
        "Excel Bulk Upload (Employee)",
        "Data Entry (Fine System)",
        "View All Records",
        "Search, QR Scan & Edit",
        "Data Backup",
    ],
)

# --- 2. EMPLOYEE MASTER DATA MODULE (Master Data & Resign Feature) ---
if menu == "Employee Master Data (ဝန်ထမ်းစာရင်း)":
  st.subheader("👤 ဝန်ထမ်းအချက်အလက်များနှင့် Resign ပြုလုပ်ခြင်း")

  with st.form("emp_master_form", clear_on_submit=True):
    e_id = st.text_input("Employee ID")
    e_name = st.text_input("Name")
    e_dept = st.selectbox("Department", departments)
    e_join_date = st.date_input("Join Date")
    e_photo = st.text_input("Photo (Image URL သို့မဟုတ် ပုံလင့်ခ်)")

    submitted_emp = st.form_submit_button("ဝန်ထမ်းစာရင်း သိမ်းဆည်းမည်")

    if submitted_emp:
      if not e_id or not e_name:
        st.warning("ကျေးဇူးပြု၍ Employee ID နှင့် Name ကို ဖြည့်စွက်ပါ။")
      else:
        new_emp_row = pd.DataFrame({
            "Photo": [e_photo],
            "Employee ID": [e_id],
            "Name": [e_name],
            "Department": [e_dept],
            "Join Date": [str(e_join_date)],
        })
        st.session_state.employee_master = pd.concat(
            [st.session_state.employee_master, new_emp_row], ignore_index=True
        )
        st.success(f"ဝန်ထမ်း ({e_name}) ၏ အချက်အလက်များကို သိမ်းဆည်းပြီးပါပြီ။")

  st.markdown("---")
  st.subheader("📋 လက်ရှိ ဝန်ထမ်း Master စာရင်းများ")

  if not st.session_state.employee_master.empty:
    # st.data_editor ကို အသုံးပြု၍ ဇယားမှ တိုက်ရိုက် ရွေးချယ်ခြင်း သို့မဟုတ် Resign လုပ်ခြင်း
    edited_master_df = st.data_editor(
        st.session_state.employee_master,
        use_container_width=True,
        key="master_editor",
    )

    st.markdown("### 🛑 အလုပ်ထွက်မည့် ဝန်ထမ်းကို Resign ပြုလုပ်ရန်")
    master_indices = st.session_state.employee_master.index.tolist()
    selected_resign_idx = st.selectbox(
        "Resign လုပ်မည့် ဝန်ထမ်းကို ရွေးချယ်ပါ",
        master_indices,
        format_func=lambda x: f"ID: {st.session_state.employee_master.loc[x, 'Employee ID']} | Name: {st.session_state.employee_master.loc[x, 'Name']}",
    )

    if st.button("🚨 Resign သို့ ပို့မည် (အလုပ်ထွက်မည်)"):
      row_to_resign = st.session_state.employee_master.loc[
          [selected_resign_idx]
      ]
      st.session_state.resign_records = pd.concat(
          [st.session_state.resign_records, row_to_resign], ignore_index=True
      )
      st.session_state.employee_master = (
          st.session_state.employee_master.drop(selected_resign_idx)
          .reset_index(drop=True)
      )
      st.success("ဝန်ထမ်းကို Resign Module သို့ အောင်မြင်စွာ ပြောင်းရွှေ့လိုက်ပါပြီ။")
      st.rerun()
  else:
    st.info("လက်ရှိတွင် ဝန်ထမ်းစာရင်း မရှိသေးပါ။")

# --- 3. RESIGN MANAGEMENT MODULE (Update, Resign Edit & Delete) ---
elif menu == "Resign Management (အလုပ်ထွက်စာရင်း)":
  st.subheader("🚪 အလုပ်ထွက်သွားသော ဝန်ထမ်းများ (Resign Records)")

  if st.session_state.resign_records.empty:
    st.info("အလုပ်ထွက်ထားသော ဝန်ထမ်းစာရင်း မရှိသေးပါ။")
  else:
    st.dataframe(st.session_state.resign_records, use_container_width=True)

    st.markdown("---")
    st.subheader(
        "🛠️ Resign Data များကို ပြင်ဆင်ရန် (Update) သို့မဟုတ် ဖျက်ရန် (Delete)"
    )

    resign_indices = st.session_state.resign_records.index.tolist()
    selected_r_idx = st.selectbox(
        "ပြင်ဆင်လို/ဖျက်လိုသော Resign စာရင်းကို ရွေးချယ်ပါ",
        resign_indices,
        format_func=lambda x: f"ID: {st.session_state.resign_records.loc[x, 'Employee ID']} | Name: {st.session_state.resign_records.loc[x, 'Name']}",
    )

    if selected_r_idx is not None:
      curr_resign = st.session_state.resign_records.loc[selected_r_idx]

      with st.form("resign_edit_form"):
        r_id = st.text_input(
            "Employee ID", value=str(curr_resign["Employee ID"])
        )
        r_name = st.text_input("Name", value=str(curr_resign["Name"]))
        r_dept = st.selectbox(
            "Department",
            departments,
            index=departments.index(curr_resign["Department"])
            if curr_resign["Department"] in departments
            else 0,
        )
        r_join = st.text_input("Join Date", value=str(curr_resign["Join Date"]))
        r_photo = st.text_input("Photo URL", value=str(curr_resign["Photo"]))

        c_u, c_d = st.columns(2)
        with c_u:
          update_r_btn = st.form_submit_button("🔄 Update Resign Data")
        with c_d:
          delete_r_btn = st.form_submit_button("🗑️ Delete Resign Data")

        if update_r_btn:
          st.session_state.resign_records.loc[selected_r_idx, "Employee ID"] = (
              r_id
          )
          st.session_state.resign_records.loc[selected_r_idx, "Name"] = r_name
          st.session_state.resign_records.loc[selected_r_idx, "Department"] = (
              r_dept
          )
          st.session_state.resign_records.loc[selected_r_idx, "Join Date"] = (
              r_join
          )
          st.session_state.resign_records.loc[selected_r_idx, "Photo"] = r_photo
          st.success("Resign data ကို အောင်မြင်စွာ Update လုပ်ပြီးပါပြီ။")
          st.rerun()

        if delete_r_btn:
          st.session_state.resign_records = (
              st.session_state.resign_records.drop(selected_r_idx)
              .reset_index(drop=True)
          )
          st.success("Resign data ကို အောင်မြင်စွာ ဖျက်လိုက်ပါပြီ။")
          st.rerun()

# --- 4. EXCEL BULK UPLOAD FOR EMPLOYEES ---
elif menu == "Excel Bulk Upload (Employee)":
  st.subheader("📤 Excel ဖြင့် ဝန်ထမ်းဒေတာများ တင်သွင်းရန်")
  uploaded_emp_excel = st.file_uploader(
      "ဝန်ထမ်း Excel ဖိုင်ကို ရွေးချယ်ပါ (.xlsx)", type=["xlsx"]
  )
  if uploaded_emp_excel is not None:
    df_emp_excel = pd.read_excel(uploaded_emp_excel)
    st.write("တင်သွင်းလာသော ဝန်ထမ်း Data များ:", df_emp_excel.head())

    if st.button("📥 ဤဝန်ထမ်း Data များကို သိမ်းမည်"):
      st.session_state.employee_master = pd.concat(
          [st.session_state.employee_master, df_emp_excel], ignore_index=True
      )
      st.success("ဝန်ထမ်း Data များ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။")

# --- 5. DATA ENTRY (Fine System) ---
elif menu == "Data Entry (Fine System)":
  st.subheader("➕ ဝန်ထမ်းပြစ်ချက်/ဒဏ်ငွေ အချက်အလက်များ ထည့်သွင်းရန်")

  emp_names = (
      st.session_state.employee_master["Name"].tolist()
      if not st.session_state.employee_master.empty
      else []
  )
  selected_name = st.selectbox(
      "ဝန်ထမ်းအမည် (Name) ကို ရွေးချယ်ပါ", ["-- Select Name --"] + emp_names
  )

  auto_id = ""
  auto_dept = departments[0]
  auto_photo = ""

  if selected_name != "-- Select Name --":
    matched_emp = st.session_state.employee_master[
        st.session_state.employee_master["Name"] == selected_name
    ]
    if not matched_emp.empty:
      auto_id = str(matched_emp.iloc[0]["Employee ID"])
      auto_dept = str(matched_emp.iloc[0]["Department"])
      auto_photo = str(matched_emp.iloc[0]["Photo"])

      st.success(f"✅ ဝန်ထမ်း ({selected_name}) ၏ အချက်အလက်များကို တွေ့ရှိပါပြီ။")
      if auto_photo and auto_photo != "nan":
        try:
          st.image(auto_photo, width=120, caption=selected_name)
        except Exception:
          pass

  with st.form("fine_form"):
    name = st.text_input(
        "Name", value=selected_name if selected_name != "-- Select Name --" else ""
    )
    employee_id = st.text_input("Employee ID", value=auto_id)

    col1, col2 = st.columns(2)
    with col1:
      department = st.selectbox(
          "Department",
          departments,
          index=departments.index(auto_dept)
          if auto_dept in departments
          else 0,
      )
      factory = st.selectbox("Factory", factories)
    with col2:
      date = st.date_input("Date")
      chief = st.text_input("Chief (တာဝန်ခံ)")

    fine_description = st.selectbox("Fine Description", fine_descriptions)
    reported_by = st.text_input("Reported by (တင်ပြသူ/စစ်ဆေးသူ)")
    photo_url = st.text_input("Photo URL", value=auto_photo)

    submitted = st.form_submit_button("ဒဏ်ငွေစာရင်း သိမ်းဆည်းမည်")

    if submitted:
      if not employee_id or not name:
        st.warning("ကျေးဇူးပြု၍ Employee ID နှင့် Name ကို ဖြည့်စွက်ပေးပါ။")
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
            "Photo URL": [photo_url],
        }
        df_new = pd.DataFrame(new_data)
        st.session_state.records = pd.concat(
            [st.session_state.records, df_new], ignore_index=True
        )
        st.success("ဒဏ်ငွေစာရင်းကို အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။")

# --- 6. VIEW ALL RECORDS ---
elif menu == "View All Records":
  st.subheader("📊 ထည့်သွင်းထားသော စာရင်း အားလုံး")
  if st.session_state.records.empty:
    st.info("လက်ရှိတွင် စာရင်းသွင်းထားသော အချက်အလက် မရှိသေးပါ။")
  else:
    st.dataframe(st.session_state.records, use_container_width=True)

# --- 7. SEARCH, QR SCAN & EDIT ---
elif menu == "Search, QR Scan & Edit":
  st.subheader("🔍 QR Code / ID ဖြင့် ရှာဖွေခြင်းနှင့် ဓာတ်ပုံပြသခြင်း")
  if st.session_state.records.empty:
    st.info("လက်ရှိတွင် စာရင်းသွင်းထားသော အချက်အလက် မရှိသေးပါ။")
  else:
    scan_input = st.text_input(
        "📷 QR Code Scan ဖတ်ပါ သို့မဟုတ် Employee ID/Name ရိုက်ထည့်ပါ"
    )
    if scan_input:
      matched = st.session_state.records[
          st.session_state.records["Employee ID"]
          .astype(str)
          .str.contains(scan_input, case=False, na=False)
          | st.session_state.records["Name"]
          .astype(str)
          .str.contains(scan_input, case=False, na=False)
      ]
      if not matched.empty:
        for idx, row in matched.iterrows():
          col_img, col_info = st.columns([1, 2])
          with col_img:
            if pd.notna(row["Photo URL"]) and str(row["Photo URL"]).strip() != "":
              try:
                st.image(str(row["Photo URL"]), width=150, caption=row["Name"])
              except Exception:
                st.warning("ပုံပြသ၍ မရပါ။")
            else:
              st.warning("ဓာတ်ပုံ မရှိပါ")

            img = qrcode.make(str(row["Employee ID"]))
            buf = BytesIO()
            img.save(buf)
            st.image(
                buf.getvalue(), width=100, caption=f"QR: {row['Employee ID']}"
            )
          with col_info:
            st.write(
                f"**Employee ID:** {row['Employee ID']} | **Name:**"
                f" {row['Name']}"
            )
            st.write(
                f"**Department:** {row['Department']} | **Factory:**"
                f" {row['Factory']}"
            )
            st.write(
                f"**Date:** {row['Date']} | **Chief:** {row['Chief']}"
            )
            st.write(
                f"**Fine Description:** {row['Fine Description']} |"
                f" **Reported by:** {row['Reported by']}"
            )
          st.markdown("---")

# --- 8. DATA BACKUP MODE ---
elif menu == "Data Backup":
  st.subheader("📥 Data Download & Backup")
  if not st.session_state.records.empty:
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