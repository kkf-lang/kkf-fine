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


# Helper function to get correct image URL (GitHub Raw URL)
def get_image_url(path):
  if not path or pd.isna(path):
    return ""
  path_str = str(path).strip()
  # If it's already a full http link, return it
  if path_str.startswith("http://") or path_str.startswith("https://"):
    return path_str
  # Otherwise, map it to GitHub Raw URL (Repo: kkf-lang/kkf-fine, branch: main)
  # ပုံများကို GitHub ၏ main branch အပြင်ဘက် သို့မဟုတ် Employee Photo folder ထဲတွင် ထားရှိမှုအပေါ် မူတည်သည်
  return f"https://raw.githubusercontent.com/kkf-lang/kkf-fine/main/{path_str}"


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
        "Edit/Delete Master Data (ဝန်ထမ်းဒေတာ ပြင်ဆင်/ဖျက်ရန်)",
        "Resign Management (အလုပ်ထွက်စာရင်း)",
        "Excel Bulk Upload (Employee)",
        "Data Entry (Fine System)",
        "View All Records",
        "Search, QR Scan & Edit",
        "Data Backup",
    ],
)

# --- 2. EMPLOYEE MASTER DATA MODULE ---
if menu == "Employee Master Data (ဝန်ထမ်းစာရင်း)":
  st.subheader("👤 ဝန်ထမ်းအချက်အလက်များ ထည့်သွင်းရန်")

  with st.form("emp_master_form", clear_on_submit=True):
    e_id = st.text_input("Employee ID")
    e_name = st.text_input("Name")
    e_dept = st.selectbox("Department", departments)
    e_join_date = st.date_input("Join Date")
    e_photo = st.text_input("Photo (ဥပမာ - Daw Aye Sandar.jpg)")

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
    st.dataframe(st.session_state.employee_master, use_container_width=True)
  else:
    st.info("လက်ရှိတွင် ဝန်ထမ်းစာရင်း မရှိသေးပါ။")

# --- 3. EDIT / DELETE / RESIGN MASTER DATA MODULE ---
elif menu == "Edit/Delete Master Data (ဝန်ထမ်းဒေတာ ပြင်ဆင်/ဖျက်ရန်)":
  st.subheader("🛠️ ဝန်ထမ်း Master Data များကို ပြင်ဆင်ခြင်းနှင့် ဓာတ်ပုံပြသခြင်း")

  if st.session_state.employee_master.empty:
    st.info("ပြင်ဆင်ရန် ဝန်ထမ်းစာရင်း မရှိသေးပါ။")
  else:
    emp_options = {
        f"ID: {row['Employee ID']} | Name: {row['Name']} (Index {idx})": idx
        for idx, row in st.session_state.employee_master.iterrows()
    }

    selected_emp_label = st.selectbox(
        "👉 ပြင်ဆင်လို/ဖျက်လိုသော ဝန်ထမ်းကို ရွေးချယ်ပါ", list(emp_options.keys())
    )

    if selected_emp_label:
      sel_idx = emp_options[selected_emp_label]
      curr_emp = st.session_state.employee_master.loc[sel_idx]

      # ပုံပြသရန်
      img_path = curr_emp["Photo"]
      full_img_url = get_image_url(img_path)
      if full_img_url:
        try:
          st.image(
              full_img_url, width=150, caption=str(curr_emp["Name"])
          )  #[cite: 15]
        except Exception:
          st.warning("ပုံကို ဖွင့်၍မရပါ။ GitHub တွင် ပုံရှိမရှိ စစ်ဆေးပါ။")

      with st.form("edit_master_form"):
        em_id = st.text_input("Employee ID", value=str(curr_emp["Employee ID"]))
        em_name = st.text_input("Name", value=str(curr_emp["Name"]))
        em_dept = st.selectbox(
            "Department",
            departments,
            index=departments.index(curr_emp["Department"])
            if curr_emp["Department"] in departments
            else 0,
        )
        em_join = st.text_input("Join Date", value=str(curr_emp["Join Date"]))
        em_photo = st.text_input("Photo URL", value=str(curr_emp["Photo"]))

        c1, c2, c3 = st.columns(3)
        with c1:
          update_btn = st.form_submit_button("🔄 Update")
        with c2:
          delete_btn = st.form_submit_button("🗑️ Delete")
        with c3:
          resign_btn = st.form_submit_button("🚨 Resign (အလုပ်ထွက်)")

        if update_btn:
          st.session_state.employee_master.loc[sel_idx, "Employee ID"] = em_id
          st.session_state.employee_master.loc[sel_idx, "Name"] = em_name
          st.session_state.employee_master.loc[sel_idx, "Department"] = em_dept
          st.session_state.employee_master.loc[sel_idx, "Join Date"] = em_join
          st.session_state.employee_master.loc[sel_idx, "Photo"] = em_photo
          st.success("ဝန်ထမ်းအချက်အလက်ကို အောင်မြင်စွာ Update လုပ်ပြီးပါပြီ။")
          st.rerun()

        if delete_btn:
          st.session_state.employee_master = (
              st.session_state.employee_master.drop(sel_idx)
              .reset_index(drop=True)
          )
          st.success("ဝန်ထမ်းစာရင်းကို အောင်မြင်စွာ ဖျက်လိုက်ပါပြီ။")
          st.rerun()

        if resign_btn:
          row_to_resign = st.session_state.employee_master.loc[[sel_idx]]
          st.session_state.resign_records = pd.concat(
              [st.session_state.resign_records, row_to_resign], ignore_index=True
          )
          st.session_state.employee_master = (
              st.session_state.employee_master.drop(sel_idx)
              .reset_index(drop=True)
          )
          st.success(
              "ဝန်ထမ်းကို Resign Module သို့ အောင်မြင်စွာ ပြောင်းရွှေ့လိုက်ပါပြီ။"
          )
          st.rerun()

# --- 4. RESIGN MANAGEMENT MODULE ---
elif menu == "Resign Management (အလုပ်ထွက်စာရင်း)":
  st.subheader("🚪 အလုပ်ထွက်သွားသော ဝန်ထမ်းများ (Resign Records)")
  if st.session_state.resign_records.empty:
    st.info("အလုပ်ထွက်ထားသော ဝန်ထမ်းစာရင်း မရှိသေးပါ။")
  else:
    st.dataframe(st.session_state.resign_records, use_container_width=True)

# --- 5. EXCEL BULK UPLOAD FOR EMPLOYEES ---
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

# --- 6. DATA ENTRY (Fine System) ---
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
      full_url = get_image_url(auto_photo)
      if full_url:
        try:
          st.image(full_url, width=120, caption=selected_name)
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

# --- 7. VIEW ALL RECORDS ---
elif menu == "View All Records":
  st.subheader("📊 ထည့်သွင်းထားသော စာရင်း အားလုံး")
  if st.session_state.records.empty:
    st.info("လက်ရှိတွင် စာရင်းသွင်းထားသော အချက်အလက် မရှိသေးပါ။")
  else:
    st.dataframe(st.session_state.records, use_container_width=True)

# --- 8. SEARCH, QR SCAN & EDIT ---
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
            full_url = get_image_url(row["Photo URL"])
            if full_url:
              try:
                st.image(full_url, width=150, caption=row["Name"])
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

# --- 9. DATA BACKUP MODE ---
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