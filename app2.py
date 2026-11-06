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

# Sample Master Employee Database (Employee ID ဖြင့် အချက်အလက် ခေါ်ရန်)
if "employee_master" not in st.session_state:
  st.session_state.employee_master = {
      "140001": {
          "Name": "U Hein Zar",
          "Department": "Extruding",
          "Chief": "GA",
          "Photo URL": "https://via.placeholder.com/150",
      },
      "140002": {
          "Name": "Daw Mya Mya",
          "Department": "Weaving",
          "Chief": "U Ba",
          "Photo URL": "https://via.placeholder.com/150",
      },
  }

# Navigation Menu
menu = st.sidebar.selectbox(
    "Select Mode",
    [
        "Data Entry (Auto-Fill)",
        "Search, QR Scan & Edit",
        "Excel Bulk Upload",
        "Data Backup",
    ],
)

# --- 2. DATA ENTRY MODE WITH AUTO-FILL ---
if menu == "Data Entry (Auto-Fill)":
  st.subheader(
      "➕ ဝန်ထမ်းပြစ်ချက်/ဒဏ်ငွေ အချက်အလက်များ ထည့်သွင်းရန် (ID ဖြင့် Auto-Fill)"
  )

  # Employee ID input ထည့်ခြင်း (Session State ဖြင့် တန်ဖိုးကို မှတ်ထားမည်)
  if "input_emp_id" not in st.session_state:
    st.session_state.input_emp_id = ""

  emp_id_input = st.text_input(
      "Employee ID ရိုက်ထည့်ပါ (သို့မဟုတ် Scan ဖတ်ပါ)", key="emp_id_text"
  )

  # အကယ်၍ ID ရိုက်ထည့်လိုက်ပါက Master Data ထဲမှ အလိုအလျောက် ရှာယူမည်
  auto_name = ""
  auto_dept = departments[0]
  auto_chief = ""
  auto_photo = ""

  if emp_id_input in st.session_state.employee_master:
    emp_info = st.session_state.employee_master[emp_id_input]
    auto_name = emp_info["Name"]
    auto_dept = emp_info["Department"]
    auto_chief = emp_info["Chief"]
    auto_photo = emp_info["Photo URL"]

    st.success(
        f"✅ Employee ID ({emp_id_input}) ၏ အချက်အလက်များကို တွေ့ရှိပါပြီ။"
    )
    if auto_photo:
      st.image(auto_photo, width=120, caption=auto_name)
  elif emp_id_input != "":
    st.warning(
        "⚠️ ဤ ID ကို Master Data ထဲတွင် မတွေ့ရသေးပါ။ အောက်ပါ Form တွင်"
        " အသစ်ဖြည့်သွင်းနိုင်ပါသည်။"
    )

  with st.form("fine_form"):
    employee_id = st.text_input("Employee ID", value=emp_id_input)
    name = st.text_input("Name", value=auto_name)

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
      chief = st.text_input("Chief (တာဝန်ခံ)", value=auto_chief)

    fine_description = st.selectbox("Fine Description", fine_descriptions)
    reported_by = st.text_input("Reported by (တင်ပြသူ/စစ်ဆေးသူ)")
    photo_url = st.text_input("Photo URL", value=auto_photo)

    submitted = st.form_submit_button("စာရင်းသွင်းမည် (Submit)")

    if submitted:
      if not employee_id or not name:
        st.warning("ကျေးဇူးပြု၍ Employee ID နှင့် Name ကို ဖြည့်စွက်ပေးပါ။")
      else:
        # Master Data ထဲသို့ပါ အလိုအလျောက် မှတ်သားပေးမည်
        st.session_state.employee_master[employee_id] = {
            "Name": name,
            "Department": department,
            "Chief": chief,
            "Photo URL": photo_url,
        }

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
        st.success(
            "ဒဏ်ငွေစာရင်းနှင့် ဝန်ထမ်းအချက်အလက်ကို အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။"
        )

# --- 3. SEARCH, QR SCAN, FILTER & EDIT/DELETE MODE ---
elif menu == "Search, QR Scan & Edit":
  st.subheader("🔍 QR Code / ID ဖြင့် ရှာဖွေခြင်းနှင့် ဓာတ်ပုံပြသခြင်း")

  if st.session_state.records.empty:
    st.info("လက်ရှိတွင် စာရင်းသွင်းထားသော အချက်အလက် မရှိသေးပါ။")
  else:
    f1, f2 = st.columns(2)
    with f1:
      filter_dept = st.selectbox(
          "Filter Department",
          ["အားလုံး"] + list(st.session_state.records["Department"].unique()),
      )
    with f2:
      filter_fine = st.selectbox(
          "Filter Fine Description",
          ["အားလုံး"] + list(
              st.session_state.records["Fine Description"].unique()
          ),
      )

    df_filtered = st.session_state.records.copy()
    if filter_dept != "အားလုံး":
      df_filtered = df_filtered[df_filtered["Department"] == filter_dept]
    if filter_fine != "အားလုံး":
      df_filtered = df_filtered[df_filtered["Fine Description"] == filter_fine]

    scan_input = st.text_input(
        "📷 QR Code Scan ဖတ်ပါ သို့မဟုတ် Employee ID ရိုက်ထည့်ပါ"
    )

    if scan_input:
      matched = df_filtered[
          df_filtered["Employee ID"].astype(str).str.contains(
              scan_input, case=False, na=False
          )
      ]
      if not matched.empty:
        st.success(f"တွေ့ရှိရသော ဝန်ထမ်း စုစုပေါင်း: {len(matched)} ဦး")
        for idx, row in matched.iterrows():
          col_img, col_info = st.columns([1, 2])
          with col_img:
            if pd.notna(row["Photo URL"]) and row["Photo URL"].strip() != "":
              st.image(row["Photo URL"], width=150, caption=row["Name"])
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
      else:
        st.warning("ဤ ID ဖြင့် မှတ်တễm မတွေ့ရှိပါ။")

    # Edit & Delete Section
    st.subheader("🛠️ Data ပြင်ဆင်ရန် (သို့) ဖျက်ရန်")
    row_options = {
        f"Index {idx} | ID: {row['Employee ID']} | Name: {row['Name']}": idx
        for idx, row in df_filtered.iterrows()
    }
    if row_options:
      sel_label = st.selectbox(
          "ပြင်ဆင်လိုသော စာရင်းကို ရွေးချယ်ပါ", list(row_options.keys())
      )
      sel_idx = row_options[sel_label]
      curr = st.session_state.records.loc[sel_idx]

      with st.form("edit_form"):
        u_id = st.text_input("Employee ID", value=curr["Employee ID"])
        u_name = st.text_input("Name", value=curr["Name"])
        u_dept = st.selectbox(
            "Department",
            departments,
            index=departments.index(curr["Department"])
            if curr["Department"] in departments
            else 0,
        )
        u_fact = st.selectbox(
            "Factory",
            factories,
            index=factories.index(curr["Factory"])
            if curr["Factory"] in factories
            else 0,
        )
        u_chief = st.text_input("Chief", value=curr["Chief"])
        u_fine = st.selectbox(
            "Fine Description",
            fine_descriptions,
            index=fine_descriptions.index(curr["Fine Description"])
            if curr["Fine Description"] in fine_descriptions
            else 0,
        )
        u_rep = st.text_input("Reported by", value=curr["Reported by"])
        u_photo = st.text_input("Photo URL", value=curr["Photo URL"])

        c_up, c_del = st.columns(2)
        with c_up:
          up_btn = st.form_submit_button("🔄 Update")
        with c_del:
          del_btn = st.form_submit_button("🗑️ Delete")

        if up_btn:
          st.session_state.records.loc[sel_idx, "Employee ID"] = u_id
          st.session_state.records.loc[sel_idx, "Name"] = u_name
          st.session_state.records.loc[sel_idx, "Department"] = u_dept
          st.session_state.records.loc[sel_idx, "Factory"] = u_fact
          st.session_state.records.loc[sel_idx, "Chief"] = u_chief
          st.session_state.records.loc[sel_idx, "Fine Description"] = u_fine
          st.session_state.records.loc[sel_idx, "Reported by"] = u_rep
          st.session_state.records.loc[sel_idx, "Photo URL"] = u_photo
          st.success("အောင်မြင်စွာ Update လုပ်ပြီးပါပြီ။")
          st.rerun()

        if del_btn:
          st.session_state.records = st.session_state.records.drop(
              sel_idx
          ).reset_index(drop=True)
          st.success("အောင်မြင်စွာ ဖျက်လိုက်ပါပြီ။")
          st.rerun()

# --- 4. EXCEL BULK UPLOAD MODE ---
elif menu == "Excel Bulk Upload":
  st.subheader("📤 Excel ဖိုင်ဖြင့် Data များ တစ်ခါတည်း တင်သွင်းရန်")
  uploaded_excel = st.file_uploader(
      "Excel ဖိုင်ကို ရွေးချယ်ပါ (.xlsx)", type=["xlsx"]
  )
  if uploaded_excel is not None:
    df_excel = pd.read_excel(uploaded_excel)
    st.write("တင်သွင်းလာသော Data များ:", df_excel.head())

    if st.button("📥 ဤ Data များကို System ထဲသို့ ထည့်မည်"):
      st.session_state.records = pd.concat(
          [st.session_state.records, df_excel], ignore_index=True
      )
      st.success("Excel မှ Data များကို အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ။")

# --- 5. DATA BACKUP MODE ---
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