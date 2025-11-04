import os
import platform
from typing import Dict, List
from warnings import warn

import pandas as pd
from icecream import ic

SYSTEM_MACHINE = platform.system()
IS_LINUX_MACHINE = SYSTEM_MACHINE == "Linux"

# Load Excel path from environment (set in .env or overridden in main.py)
TUTOR_EXCEL_PATH = os.getenv(
    "TUTOR_EXCEL_PATH",
    r"C:\Users\lexyg\OneDrive\Documents\COLLEGIATE TUTORS\Software Stuff\lexy_python_backend\tutor_course_list_bk.xlsx"
)

print(f"📘 Using Excel file at: {TUTOR_EXCEL_PATH}")
COLLEGIATE_TUTORS_EMAIL_EXT = ".collegiatetutorsllc@gmail.com"

ic(TUTOR_EXCEL_PATH)


def _get_clean_df() -> pd.DataFrame:
    df = pd.read_excel(TUTOR_EXCEL_PATH)

    def strip_lower(df_col):
        return df_col.apply(lambda x: x.strip().lower() if isinstance(x, str) else x)

    df.iloc[:, 0] = strip_lower(df.iloc[:, 0])
    df.iloc[:, 1] = strip_lower(df.iloc[:, 1])
    return df


def get_available_classes() -> List[str]:
    """
    reads excel of tutors and returns list of classes
    """
    df = _get_clean_df()
    classes = [x for x in df.iloc[:, 1].unique() if not pd.isna(x)]
    if "course" in classes:
        classes.remove("course")
    else:
        warn(
            "get_available_classes: did not find 'Course' in excel column 0."
            " Has excel format has been updated and this function will probably not work correctly!!!"
        )

    return classes


def get_tutor_emails(tutors: List[str], _all=False) -> Dict[str, str]:
    """
    Reads Excel and returns a dict of tutor names and emails.
    If no 'Contacts' sheet exists, it will auto-generate emails using tutor names.
    """
    try:
        # Try to read Contacts sheet
        df = pd.read_excel(TUTOR_EXCEL_PATH, sheet_name="Contacts", header=None)
    except ValueError:
        # Fallback: use Sheet1 and auto-generate emails
        print("⚠️ 'Contacts' sheet not found — using Sheet1 and generating default emails.")
        df = pd.read_excel(TUTOR_EXCEL_PATH, sheet_name="Sheet1", header=None)
        df = df.iloc[:, 0:1]  # only tutor names

        tutor_email_dict = {}
        for _, row in df.iterrows():
            name_cell = row.iloc[0]
            if not isinstance(name_cell, str):
                continue
            t = name_cell.strip().lower()
            email = f"{t}@collegiatetutors.com"
            if t in tutors or _all:
                tutor_email_dict[t] = email
        return tutor_email_dict

    # Normal mode (Contacts sheet exists)
    tutor_name_email: pd.DataFrame = df.iloc[:, 0:2]
    tutor_email_dict = {}
    for _, row in tutor_name_email.iterrows():
        name_cell = row.iloc[0]
        email_cell = row.iloc[1]
        if not isinstance(name_cell, str) or not isinstance(email_cell, str):
            continue  # skip blank or invalid rows
        t = name_cell.strip().lower()
        e = email_cell.strip().lower()
        if t in tutors or _all:
            tutor_email_dict[t] = e
    return tutor_email_dict


def get_all_tutors() -> Dict[str, str]:
    """
    Convenience func for getting all tutor emails
    """
    return get_tutor_emails([], _all=True)


def get_tutors_for_class(class_: str) -> List[str]:
    """
    Reads excel of tutors and gives tutors emails for classes
    """
    df = _get_clean_df()
    df = df[df.iloc[:, 1] == class_]
    df = df.iloc[:, 0].unique()
    return [x for x in df if not pd.isna(x)]


if __name__ == "__main__":
    ic(get_tutor_emails(["kirstin", "brian"]))
    tutors = get_all_tutors()
    # ic(tutors)
    classes = get_available_classes()
    # ic(classes)
    for c in classes:
        ic(c, get_tutors_for_class(c))
