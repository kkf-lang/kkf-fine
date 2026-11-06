from io import BytesIO
import pandas as pd
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
st.write(
    "Data များကို နာမည်/ID ဖြင့် သို့မဟုတ် QR Code ဖြင့် ရှာဖွေ၍ Update/Delete"
    " ပြုလုပ်ခြင်းစနစ်။"
)

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
      ]
  )

# Navigation Menu
menu = st.sidebar.selectbox(
    "Select Mode", ["Data Entry", "Search, Edit & Delete", "Data Backup"]
)

# --- 2. DATA ENTRY MODE ---
if menu == "Data Entry":
  st.subheader("➕ ဝန်ထမ်းပြစ်ချက်/ဒဏ်ငွေ အချက်အလက်များ ထည့်သွင်းရန်")

  with st.form("fine_form", clear_on_submit=True):
    employee_id = st.text_input("Employee ID")
    name = st.text_input("Name")

    col1, col2 = st.columns(2)
    with col1:
      department = st.selectbox("Department", departments)
      factory = st.selectbox("Factory", factories)
    with col2:
      date = st.date_input("Date")
      chief = st.text_input("Chief (တာဝန်ခံ)")

    fine_description = st.selectbox("Fine Description", fine_descriptions)
    reported_by = st.text_input("Reported by (တင်ပြသူ/စစ်ဆေးသူ)")

    submitted = st.form_submit_button("စာရင်းသွင်းမည် (Submit)")

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
        }
        df_new = pd.DataFrame(new_data)
        st.session_state.records = pd.concat(
            [st.session_state.records, df_new], ignore_index=True
        )
        st.success("ဒဏ်ငွေစာရင်းကို အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။")

# --- 3. SEARCH (TEXT & QR CODE), EDIT & DELETE MODE ---
elif menu == "Search, Edit & Delete":
  st.subheader("🔍 Data ရှာဖွေခြင်း (Name, ID သို့မဟုတ် QR Code ဖြင့်)")

  if st.session_state.records.empty:
    st.info("လက်ရှိတွင် စာရင်းသွင်းထားသော အချက်အလက် မရှိသေးပါ။")
  else:
    # Search Options: Text Search or QR Code Search
    search_type = st.radio(
        "ရှာဖွေမည့် ပုံစံကို ရွေးချယ်ပါ",
        ["Text Search (နာမည်/ID ဖြင့်)", "QR Code Search (QR ဖြင့်)"],
    )

    search_query = ""
    if search_type == "Text Search (နာမည်/ID ဖြင့်)":
      search_query = st.text_input(
          "🔎 ရှာလိုသော Employee ID သို့မဟုတ် Name ကို ရိုက်ထည့်ပါ"
      )
    else:
      # QR Code input (USB Barcode/QR Scanner သို့မဟုတ် Mobile Camera ဖြင့် scan ဖတ်ရာမှ ရလာမည့် text)
      search_query = st.text_input(
          "📷 QR Code ကို Scanner ဖြင့် ဖတ်ပါ (သို့မဟုတ် Code စာသားကို"
          " ထည့်ပါ)"
      )

    df_to_show = st.session_state.records.copy()
    if search_query:
      # Employee ID သို့မဟုတ် Name တွင် ရှာဖွေရန်
      mask = df_to_show["Employee ID"].astype(str).str.contains(
          search_query, case=False, na=False
      ) | df_to_show["Name"].astype(str).str.contains(
          search_query, case=False, na=False
      )
      df_to_show = df_to_show[mask]

    st.write(f"တွေ့ရှိရသော စာရင်း အရေအတွက်: **{len(df_to_show)}** ခု")

    if not df_to_show.empty:
      row_options = {
          f"Index {idx} | ID: {row['Employee ID']} | Name: {row['Name']} | Dept: {row['Department']}": idx
          for idx, row in df_to_show.iterrows()
      }

      selected_label = st.selectbox(
          "👉 ပြင်ဆင်ရန် သို့မဟုတ် ဖျက်ရန် လိုအပ်သော စာရင်းကို ရွေးချယ်ပါ",
          options=list(row_options.keys()),
      )

      if selected_label:
        selected_index = row_options[selected_label]
        current_row = st.session_state.records.loc[selected_index]

        st.markdown("---")
        st.markdown("### ✍️ ရွေးချယ်ထားသော Data များကို ပြင်ဆင်ရန် (သို့) ဖျက်ရန်")

        with st.form("update_delete_form"):
          up_emp_id = st.text_input(
              "Employee ID", value=current_row["Employee ID"]
          )
          up_name = st.text_input("Name", value=current_row["Name"])

          c1, c2 = st.columns(2)
          with c1:
            up_dept = st.selectbox(
                "Department",
                departments,
                index=(
                    departments.index(current_row["Department"])
                    if current_row["Department"] in departments
                    else 0
                ),
            )
            up_fact = st.selectbox(
                "Factory",
                factories,
                index=(
                    factories.index(current_row["Factory"])
                    if current_row["Factory"] in factories
                    else 0
                ),
            )
          with c2:
            up_chief = st.text_input("Chief", value=current_row["Chief"])
            up_fine = st.selectbox(
                "Fine Description",
                fine_descriptions,
                index=(
                    fine_descriptions.index(current_row["Fine Description"])
                    if current_row["Fine Description"] in fine_descriptions
                    else 0
                ),
            )

          up_reported = st.text_input(
              "Reported by", value=current_row["Reported by"]
          )

          col_u, col_d = st.columns(2)
          with col_u:
            update_submitted = st.form_submit_button("🔄 Update (ပြင်ဆင်မည်)")
          with col_d:
            delete_submitted = st.form_submit_button("🗑️ Delete (ဖျက်မည်)")

          if update_submitted:
            st.session_state.records.loc[selected_index, "Employee ID"] = (
                up_emp_id
            )
            st.session_state.records.loc[selected_index, "Name"] = up_name
            st.session_state.records.loc[selected_index, "Department"] = up_dept
            st.session_state.records.loc[selected_index, "Factory"] = up_fact
            st.session_state.records.loc[selected_index, "Chief"] = up_chief
            st.session_state.records.loc[selected_index, "Fine Description"] = (
                up_fine
            )
            st.session_state.records.loc[selected_index, "Reported by"] = (
                up_reported
            )
            st.success("အချက်အလက်များကို အောင်မြင်စွာ