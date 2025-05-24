import asyncio
from typing import List, Dict, Any, Literal, Optional
from datetime import datetime
import json # For pretty printing JSON in utility

import google.adk.planners
from google.genai import types as genai_types
from pydantic import BaseModel, Field

from google.adk.agents import Agent
from google.adk.tools import FunctionTool

# --- Configuration ---
AGENT_MODEL = "gemini-1.5-pro-preview-0514" # Adjust as needed

# --- Data Models (CreditApplicationInput, CreditScoreRecord, KYCRecord - as before) ---
class CreditApplicationInput(BaseModel): # (Keep as defined before)
    ApplicationID: str
    CustomerID: str
    SubmissionDate: str
    FirstName: str
    LastName: str
    Email: str
    DateOfBirth: str
    EmploymentStatus: str
    GrossMonthlyIncome: float
    TotalMonthlyDebtPayments: float
    RequestedCreditLimit: float
    SSN_Last4: str
    MaritalStatus: str
    AddressCity: str
    AddressState: str
    Age: Optional[int] = None
    DTI: Optional[float] = None
    OrchestratorNotes: Optional[str] = ""
    FinalStatus: Optional[str] = "Pending Review"

class CreditScoreRecord(BaseModel): # (Keep as defined before)
    ApplicationID: str
    CustomerID: str
    SSN_Last4: str
    CreditScore: int
    BureauReportDate: str

class KYCRecord(BaseModel): # (Keep as defined before)
    ApplicationID: str
    CustomerID: str
    KYCStatus: Literal["Updated", "Not Updated", "Unknown"]
    LastKYCVerificationDate: Optional[str] = None


# --- Static Initial Data Template (Golden Source) ---
_initial_new_applications_data_template: List[Dict[str, Any]] = [
    # !!! CRITICAL: PASTE ALL 15 of your initial application dictionaries here !!!
    # Each with "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    {
        "ApplicationID": "APP1001", "CustomerID": "CUST001", "SubmissionDate": "2024-05-28", "FirstName": "John", "LastName": "Smith", "Email": "john.smith@email.fake", "DateOfBirth": "1985-07-15", "EmploymentStatus": "Employed", "GrossMonthlyIncome": 6000.0, "TotalMonthlyDebtPayments": 1500.0, "RequestedCreditLimit": 10000.0, "SSN_Last4": "1234", "MaritalStatus": "Married", "AddressCity": "New York", "AddressState": "NY", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1002", "CustomerID": "CUST002", "SubmissionDate": "2024-05-28", "FirstName": "Alice", "LastName": "Wonder", "Email": "alice.wonder@email.fake", "DateOfBirth": "2008-01-20", "EmploymentStatus": "Student", "GrossMonthlyIncome": 500.0, "TotalMonthlyDebtPayments": 50.0, "RequestedCreditLimit": 1000.0, "SSN_Last4": "5678", "MaritalStatus": "Single", "AddressCity": "Los Angeles", "AddressState": "CA", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1003", "CustomerID": "CUST003", "SubmissionDate": "2024-05-28", "FirstName": "Robert", "LastName": "Jones", "Email": "robert.jones@email.fake", "DateOfBirth": "1990-03-10", "EmploymentStatus": "Employed", "GrossMonthlyIncome": 4000.0, "TotalMonthlyDebtPayments": 2000.0, "RequestedCreditLimit": 8000.0, "SSN_Last4": "9012", "MaritalStatus": "Single", "AddressCity": "Chicago", "AddressState": "IL", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1004", "CustomerID": "CUST004", "SubmissionDate": "2024-05-29", "FirstName": "Maria", "LastName": "Garcia", "Email": "maria.garcia@email.fake", "DateOfBirth": "1995-11-05", "EmploymentStatus": "Self-Employed", "GrossMonthlyIncome": 7000.0, "TotalMonthlyDebtPayments": 1000.0, "RequestedCreditLimit": 15000.0, "SSN_Last4": "3456", "MaritalStatus": "Married", "AddressCity": "Houston", "AddressState": "TX", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1005", "CustomerID": "CUST005", "SubmissionDate": "2024-05-29", "FirstName": "David", "LastName": "Lee", "Email": "david.lee@email.fake", "DateOfBirth": "1970-09-25", "EmploymentStatus": "Retired", "GrossMonthlyIncome": 3000.0, "TotalMonthlyDebtPayments": 500.0, "RequestedCreditLimit": 5000.0, "SSN_Last4": "7890", "MaritalStatus": "Widowed", "AddressCity": "Phoenix", "AddressState": "AZ", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1006", "CustomerID": "CUST006", "SubmissionDate": "2024-05-29", "FirstName": "Susan", "LastName": "Chen", "Email": "susan.chen@email.fake", "DateOfBirth": "1988-02-12", "EmploymentStatus": "Employed", "GrossMonthlyIncome": 8000.0, "TotalMonthlyDebtPayments": 2500.0, "RequestedCreditLimit": 20000.0, "SSN_Last4": "1122", "MaritalStatus": "Single", "AddressCity": "Philadelphia", "AddressState": "PA", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1007", "CustomerID": "CUST007", "SubmissionDate": "2024-05-30", "FirstName": "Michael", "LastName": "Brown", "Email": "michael.brown@email.fake", "DateOfBirth": "2007-06-30", "EmploymentStatus": "Student", "GrossMonthlyIncome": 200.0, "TotalMonthlyDebtPayments": 10.0, "RequestedCreditLimit": 500.0, "SSN_Last4": "3344", "MaritalStatus": "Single", "AddressCity": "San Antonio", "AddressState": "TX", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1008", "CustomerID": "CUST008", "SubmissionDate": "2024-05-30", "FirstName": "Linda", "LastName": "Davis", "Email": "linda.davis@email.fake", "DateOfBirth": "1965-12-01", "EmploymentStatus": "Employed", "GrossMonthlyIncome": 5000.0, "TotalMonthlyDebtPayments": 3000.0, "RequestedCreditLimit": 7000.0, "SSN_Last4": "5566", "MaritalStatus": "Divorced", "AddressCity": "San Diego", "AddressState": "CA", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1009", "CustomerID": "CUST009", "SubmissionDate": "2024-05-30", "FirstName": "James", "LastName": "Wilson", "Email": "james.wilson@email.fake", "DateOfBirth": "1992-04-10", "EmploymentStatus": "Unemployed", "GrossMonthlyIncome": 1000.0, "TotalMonthlyDebtPayments": 100.0, "RequestedCreditLimit": 2000.0, "SSN_Last4": "7788", "MaritalStatus": "Single", "AddressCity": "Dallas", "AddressState": "TX", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1010", "CustomerID": "CUST010", "SubmissionDate": "2024-05-31", "FirstName": "Patricia", "LastName": "Miller", "Email": "patricia.miller@email.fake", "DateOfBirth": "2000-08-19", "EmploymentStatus": "Employed", "GrossMonthlyIncome": 4500.0, "TotalMonthlyDebtPayments": 500.0, "RequestedCreditLimit": 6000.0, "SSN_Last4": "9900", "MaritalStatus": "Married", "AddressCity": "San Jose", "AddressState": "CA", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1011", "CustomerID": "CUST011", "SubmissionDate": "2024-05-31", "FirstName": "Christopher", "LastName": "Moore", "Email": "christopher.moore@email.fake", "DateOfBirth": "1980-10-03", "EmploymentStatus": "Employed", "GrossMonthlyIncome": 9000.0, "TotalMonthlyDebtPayments": 3000.0, "RequestedCreditLimit": 25000.0, "SSN_Last4": "1212", "MaritalStatus": "Married", "AddressCity": "Austin", "AddressState": "TX", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1012", "CustomerID": "CUST012", "SubmissionDate": "2024-05-31", "FirstName": "Jennifer", "LastName": "Taylor", "Email": "jennifer.taylor@email.fake", "DateOfBirth": "1998-05-22", "EmploymentStatus": "Student", "GrossMonthlyIncome": 1500.0, "TotalMonthlyDebtPayments": 200.0, "RequestedCreditLimit": 3000.0, "SSN_Last4": "3434", "MaritalStatus": "Single", "AddressCity": "Jacksonville", "AddressState": "FL", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1013", "CustomerID": "CUST013", "SubmissionDate": "2024-06-01", "FirstName": "Daniel", "LastName": "Anderson", "Email": "daniel.anderson@email.fake", "DateOfBirth": "1978-01-15", "EmploymentStatus": "Employed", "GrossMonthlyIncome": 7500.0, "TotalMonthlyDebtPayments": 4000.0, "RequestedCreditLimit": 12000.0, "SSN_Last4": "5656", "MaritalStatus": "Divorced", "AddressCity": "Fort Worth", "AddressState": "TX", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1014", "CustomerID": "CUST014", "SubmissionDate": "2024-06-01", "FirstName": "Karen", "LastName": "Thomas", "Email": "karen.thomas@email.fake", "DateOfBirth": "1993-11-30", "EmploymentStatus": "Self-Employed", "GrossMonthlyIncome": 12000.0, "TotalMonthlyDebtPayments": 3000.0, "RequestedCreditLimit": 30000.0, "SSN_Last4": "7878", "MaritalStatus": "Married", "AddressCity": "Columbus", "AddressState": "OH", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    },
    {
            "ApplicationID": "APP1015", "CustomerID": "CUST015", "SubmissionDate": "2024-06-01", "FirstName": "Brian", "LastName": "Jackson", "Email": "brian.jackson@email.fake", "DateOfBirth": "2003-07-07", "EmploymentStatus": "Employed", "GrossMonthlyIncome": 3500.0, "TotalMonthlyDebtPayments": 1000.0, "RequestedCreditLimit": 4000.0, "SSN_Last4": "9090", "MaritalStatus": "Single", "AddressCity": "Charlotte", "AddressState": "NC", "FinalStatus": "Pending Review", "OrchestratorNotes": ""
    }
]

_credit_bureau_scores_template: List[Dict[str, Any]] = [
    {"ApplicationID": "APP1001", "CustomerID": "CUST001", "SSN_Last4": "1234", "CreditScore": 750, "BureauReportDate": "2024-05-27"},
    {"ApplicationID": "APP1004", "CustomerID": "CUST004", "SSN_Last4": "3456", "CreditScore": 780, "BureauReportDate": "2024-05-28"},
    {"ApplicationID": "APP1005", "CustomerID": "CUST005", "SSN_Last4": "7890", "CreditScore": 680, "BureauReportDate": "2024-05-28"},
    {"ApplicationID": "APP1006", "CustomerID": "CUST006", "SSN_Last4": "1122", "CreditScore": 710, "BureauReportDate": "2024-05-28"},
    {"ApplicationID": "APP1009", "CustomerID": "CUST009", "SSN_Last4": "7788", "CreditScore": 550, "BureauReportDate": "2024-05-29"},
    {"ApplicationID": "APP1010", "CustomerID": "CUST010", "SSN_Last4": "9900", "CreditScore": 720, "BureauReportDate": "2024-05-30"},
    {"ApplicationID": "APP1011", "CustomerID": "CUST011", "SSN_Last4": "1212", "CreditScore": 790, "BureauReportDate": "2024-05-30"},
    {"ApplicationID": "APP1012", "CustomerID": "CUST012", "SSN_Last4": "3434", "CreditScore": 650, "BureauReportDate": "2024-05-30"},
    {"ApplicationID": "APP1014", "CustomerID": "CUST014", "SSN_Last4": "7878", "CreditScore": 735, "BureauReportDate": "2024-05-31"},
    {"ApplicationID": "APP1015", "CustomerID": "CUST015", "SSN_Last4": "9090", "CreditScore": 690, "BureauReportDate": "2024-05-31"}
]

_kyc_database_template: List[Dict[str, Any]] = [
    {"ApplicationID": "APP1001", "CustomerID": "CUST001", "KYCStatus": "Updated", "LastKYCVerificationDate": "2024-01-10"},
    {"ApplicationID": "APP1004", "CustomerID": "CUST004", "KYCStatus": "Updated", "LastKYCVerificationDate": "2023-12-05"},
    {"ApplicationID": "APP1005", "CustomerID": "CUST005", "KYCStatus": "Not Updated", "LastKYCVerificationDate": "2022-03-15"},
    {"ApplicationID": "APP1006", "CustomerID": "CUST006", "KYCStatus": "Unknown", "LastKYCVerificationDate": None},
    {"ApplicationID": "APP1009", "CustomerID": "CUST009", "KYCStatus": "Not Updated", "LastKYCVerificationDate": "2021-07-20"},
    {"ApplicationID": "APP1010", "CustomerID": "CUST010", "KYCStatus": "Updated", "LastKYCVerificationDate": "2024-02-20"},
    {"ApplicationID": "APP1011", "CustomerID": "CUST011", "KYCStatus": "Updated", "LastKYCVerificationDate": "2024-03-01"},
    {"ApplicationID": "APP1012", "CustomerID": "CUST012", "KYCStatus": "Unknown", "LastKYCVerificationDate": None},
    {"ApplicationID": "APP1014", "CustomerID": "CUST014", "KYCStatus": "Updated", "LastKYCVerificationDate": "2023-11-11"},
    {"ApplicationID": "APP1015", "CustomerID": "CUST015", "KYCStatus": "Not Updated", "LastKYCVerificationDate": "2022-08-01"}
]

# --- Mock Data Store (Mutable, will be reset each run by the agent) ---
mock_db: Dict[str, List[Dict[str, Any]]] = {
    "new_credit_applications": [],
    "credit_bureau_scores": [],
    "kyc_database": [],
    "processed_applications_log": [],
    "needs_manual_review_applications": []
}

# --- Helper Functions (Internal - as before) ---
def _calculate_age(date_of_birth_str: str) -> int: # (Keep as defined before)
    dob = datetime.strptime(date_of_birth_str, "%Y-%m-%d")
    today = datetime.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def _calculate_dti(gross_monthly_income: float, total_monthly_debt: float) -> Optional[float]: # (Keep as defined before)
    if gross_monthly_income is None or gross_monthly_income == 0:
        return None
    return round((total_monthly_debt / gross_monthly_income) * 100, 2)

# --- Tool Functions ---
def initialize_run_data() -> str:
    """
    Initializes/resets the in-memory database for a new processing run.
    This should be the VERY FIRST tool called by the agent in its workflow.
    It copies data from static templates to the active mock_db.
    """
    print("\n[TOOL EXECUTED] initialize_run_data: Resetting mock DB for new run.")
    # Deep copy from templates to ensure fresh data
    mock_db["new_credit_applications"] = [dict(app) for app in _initial_new_applications_data_template]
    mock_db["credit_bureau_scores"] = [dict(score) for score in _credit_bureau_scores_template]
    mock_db["kyc_database"] = [dict(kyc) for kyc in _kyc_database_template]
    
    # Clear dynamic lists
    mock_db["processed_applications_log"] = []
    mock_db["needs_manual_review_applications"] = []
    
    initial_pending_count = sum(1 for app in mock_db["new_credit_applications"] if app.get("FinalStatus") == "Pending Review")
    print(f"Mock DB initialized. 'new_credit_applications' count: {len(mock_db['new_credit_applications'])} ({initial_pending_count} pending).")
    print(f"'credit_bureau_scores' count: {len(mock_db['credit_bureau_scores'])}")
    print(f"'kyc_database' count: {len(mock_db['kyc_database'])}")
    return f"Successfully initialized run data. {initial_pending_count} applications are ready for review in 'new_credit_applications'."

# (get_new_applications, get_credit_score_from_bureau, get_kyc_details_from_db,
#  update_application_record_and_log, send_credit_decision_email - keep these functions as defined before)

def get_new_applications() -> List[Dict[str, Any]]:
    """
    Retrieves all new credit card applications that are pending review from the active mock_db.
    """
    print(f"\n[TOOL EXECUTED] get_new_applications: Reading from active 'new_credit_applications'")
    # Ensure the data has been initialized by the agent calling initialize_run_data first
    if not mock_db["new_credit_applications"] and _initial_new_applications_data_template:
        print("Warning: 'new_credit_applications' is empty. Agent might need to call 'initialize_run_data' first if this is unexpected.")

    pending_apps = [
        dict(app) for app in mock_db["new_credit_applications"]
        if app.get("FinalStatus") == "Pending Review"
    ]
    print(f"Found {len(pending_apps)} new applications pending review in active mock_db.")
    return pending_apps

def get_credit_score_from_bureau(application_id: str, customer_id: str, ssn_last4: str) -> Optional[Dict[str, Any]]:
    print(f"\n[TOOL EXECUTED] get_credit_score_from_bureau: For AppID '{application_id}', CustID '{customer_id}', SSN_Last4 '{ssn_last4}'")
    for score_record in mock_db["credit_bureau_scores"]: # Read from active mock_db
        if (score_record["ApplicationID"] == application_id and
            score_record["CustomerID"] == customer_id and
            score_record["SSN_Last4"] == ssn_last4):
            print(f"Credit score found for AppID '{application_id}': {score_record['CreditScore']}")
            return {"ApplicationID": application_id, "CreditScore": score_record["CreditScore"]}
    print(f"Credit score NOT FOUND for AppID '{application_id}'.")
    return None

def get_kyc_details_from_db(application_id: str, customer_id: str) -> Optional[Dict[str, Any]]:
    print(f"\n[TOOL EXECUTED] get_kyc_details_from_db: For AppID '{application_id}', CustID '{customer_id}'")
    for kyc_record in mock_db["kyc_database"]: # Read from active mock_db
        if (kyc_record["ApplicationID"] == application_id and
            kyc_record["CustomerID"] == customer_id):
            print(f"KYC status found for AppID '{application_id}': {kyc_record['KYCStatus']}")
            return {"ApplicationID": application_id, "KYCStatus": kyc_record["KYCStatus"]}
    print(f"KYC status NOT FOUND for AppID '{application_id}'.")
    return None

def update_application_record_and_log(
    application_id: str,
    final_status: Literal["Approved", "Rejected - Underage", "Rejected - DTI Exceeds Threshold", "Rejected - Credit Score and KYC", "Pending Manual Review - KYC", "Pending Manual Review - Credit Score"],
    orchestrator_notes: str
) -> str:
    print(f"\n[TOOL EXECUTED] update_application_record_and_log: For AppID '{application_id}' with status '{final_status}'")
    app_to_update_index = -1
    app_data_in_new_list = None

    # Find in the active "new_credit_applications" list
    for i, app in enumerate(mock_db["new_credit_applications"]):
        if app["ApplicationID"] == application_id:
            app_to_update_index = i
            app_data_in_new_list = app 
            break
    
    if app_data_in_new_list is not None:
        app_data_in_new_list["FinalStatus"] = final_status
        app_data_in_new_list["OrchestratorNotes"] = orchestrator_notes
        
        mock_db["processed_applications_log"].append(dict(app_data_in_new_list))

        if "Pending Manual Review" in final_status:
            mock_db["needs_manual_review_applications"].append(dict(app_data_in_new_list))
            print(f"Application '{application_id}' updated to '{final_status}' and logged. Flagged for manual review.")
            return f"Application '{application_id}' logged with status '{final_status}' and sent for manual review. Notes: {orchestrator_notes}"
        
        print(f"Application '{application_id}' updated to '{final_status}' and logged.")
        return f"Application '{application_id}' logged with status '{final_status}'. Notes: {orchestrator_notes}"
    else:
        # This case should ideally not happen if agent fetches from the same list it updates
        # but good to have a log.
        print(f"Error: Application '{application_id}' not found in 'new_credit_applications' for update. It might have already been fully processed or was never in the active list.")
        return f"Error: Could not find application '{application_id}' in the active processing list to update status."


def send_credit_decision_email(
    email_address: str,
    customer_first_name: str,
    customer_last_name: str,
    decision_status: str, 
    reason: Optional[str] = None
) -> str:
    # (Function definition as before - no changes needed here)
    print(f"\n[TOOL EXECUTED] send_credit_decision_email: To '{email_address}' for {customer_first_name} {customer_last_name}")
    subject = f"Your Credit Card Application Status - Ref: {customer_last_name.upper()}"
    body = f"Dear {customer_first_name} {customer_last_name},\n\n"

    if decision_status == "Approved":
        body += "Congratulations! We are pleased to inform you that your credit card application has been approved.\n"
        body += "Further details regarding your new card will follow shortly.\n"
    elif decision_status == "Rejected":
        body += "Thank you for your interest in our credit card. After careful consideration, we regret to inform you that we cannot approve your application at this time.\n"
        if reason:
            body += f"Reason: {reason}\n"
    elif decision_status == "Further Review Needed":
        body += "Thank you for your application. It has passed initial checks but requires further review by our underwriting team.\n"
        body += "We will contact you if any additional information is needed, or with a final decision in the coming days.\n"
        if reason: 
             body += f"Note: {reason}\n"
    else: 
        body += f"Regarding your recent credit card application, the status is: {decision_status}.\n"
        if reason:
             body += f"Details: {reason}\n"

    body += "\nSincerely,\nThe Credit Card Application Team"

    print(f"--- SIMULATED EMAIL TO: {email_address} ---")
    print(f"Subject: {subject}")
    print(body)
    print("-------------------------------------------")
    return f"Email regarding '{decision_status}' simulated for {customer_first_name} {customer_last_name} at {email_address}."


# --- ADK Tool Definitions ---
initialize_run_data_tool = FunctionTool(func=initialize_run_data) # New tool
get_new_applications_tool = FunctionTool(func=get_new_applications)
get_credit_score_tool = FunctionTool(func=get_credit_score_from_bureau)
get_kyc_details_tool = FunctionTool(func=get_kyc_details_from_db)
update_application_log_tool = FunctionTool(func=update_application_record_and_log)
send_email_tool = FunctionTool(func=send_credit_decision_email)

# --- Agent Configuration ---
agent_instructions = """
You are an AI Orchestrator Agent responsible for the initial pre-screening and data enrichment of credit card applications.
Your goal is to efficiently process applications based on defined business rules.
The current date for Age calculation is {current_date}. # This one is fine as it's pre-filled

**Overall Workflow for a processing run/session:**

1.  **Initialize Data for Run:**
    a.  **VERY FIRST STEP, DO THIS ONLY ONCE PER RUN/SESSION:** Call the `initialize_run_data` tool. This prepares a fresh set of applications for processing.
    b.  Confirm to the user that data initialization is complete and state how many applications are ready from the tool's response.

2.  **Greet User & Fetch Applications (after initialization):**
    a. Greet the user (if not already done after initialization).
    b. Call the `get_new_applications` tool to retrieve a list of all credit card applications currently in 'Pending Review' status from the now-initialized active data.
    c. Inform the user how many applications were fetched. If zero (even after initialization), inform the user and conclude for now.
    d. Ask the user if they want to proceed with processing these applications. If not, conclude.

3.  **YOU MUST Process Each Application Sequentially ->a, b,c,d,e and f:** For each application retrieved:
    a.  **Extract Applicant Info:** Get `ApplicationID`, `CustomerID`, `FirstName`, `LastName`, `Email`, `DateOfBirth`, `GrossMonthlyIncome`, `TotalMonthlyDebtPayments`, `SSN_Last4`.
    b.  **Calculate Derived Fields:** From the application data, internally calculate:
        *   `Age` (from `DateOfBirth`). Use the current date provided above for calculation.
        *   `DTI` (Debt-to-Income Ratio) = (`TotalMonthlyDebtPayments` / `GrossMonthlyIncome`) * 100. If `GrossMonthlyIncome` is 0, null, or not provided, DTI is considered incalculable or effectively infinite (fail).
    c.  **Initial Eligibility Check - Age:**
        *   If `Age` < 18:
            i.  Determine the calculated Age. Call `update_application_record_and_log` with the correct `application_id`, `final_status`="Rejected - Underage", and for `orchestrator_notes` construct a string like "Applicant is underage (XX years old)." replacing XX with the calculated Age.
            ii. Call `send_credit_decision_email` with applicant's `Email`, `FirstName`, `LastName`, `decision_status`="Rejected", and `reason`="Applicant is below the minimum age requirement of 18 years.".
            iii.Continue to the next application.
    d.  **Initial Eligibility Check - DTI:**
        *   If `DTI` >= 40.0 or DTI is incalculable (due to zero/missing income):
            i.  Determine the calculated DTI. Call `update_application_record_and_log` with `application_id`, `final_status`="Rejected - DTI Exceeds Threshold", and for `orchestrator_notes` construct a string like "DTI is XX.X% (or incalculable), exceeding 40% limit." replacing XX.X with the calculated DTI.
            ii. Call `send_credit_decision_email` with applicant's `Email`, `FirstName`, `LastName`, `decision_status`="Rejected", and for `reason` construct a string like "Debt-to-Income ratio (XX.X%) exceeds the acceptable limit of 40%, or income information is insufficient." replacing XX.X with the calculated DTI.
            iii.Continue to the next application.
    # === IMPORTANT: This entire block (e & f) MUST complete for the CURRENT application ===
    # === BEFORE you consider moving to the next application in the list. ===        
    e.  **Data Enrichment (If Initial Checks Passed):**
        i.  Call `get_credit_score_from_bureau` using `ApplicationID`, `CustomerID`, and `SSN_Last4`.
        ii. Call `get_kyc_details_from_db` using `ApplicationID` and `CustomerID`.
        iii. Store the retrieved `CreditScore` (integer or null if not found) and `KYCStatus` (string or null if not found). If a tool returns None or an error for these, the value is effectively "Not Found" or "Unknown".

    f.  **Final Decision Logic (Based on Enriched Data):**
        *   **Case 1: Credit Score >= 700 AND KYCStatus == "Updated"**
            Call `update_application_record_and_log` with `final_status`="Approved", and for `orchestrator_notes` construct a string like "Approved: CreditScore=YYY, KYCStatus=Updated." replacing YYY with the retrieved CreditScore.
            Call `send_credit_decision_email` for "Approved".
        *   **Case 2: Credit Score >= 700 AND (KYCStatus == "Not Updated" OR KYCStatus == "Unknown" OR KYCStatus is Not Found/Null)**
            Determine the retrieved CreditScore and KYCStatus. Call `update_application_record_and_log` with `final_status`="Pending Manual Review - KYC", and for `orchestrator_notes` construct a string like "Manual Review: CreditScore=YYY, KYCStatus=ZZZ needs update/verification." replacing YYY and ZZZ.
            Call `send_credit_decision_email` for "Further Review Needed", `reason`="KYC details require verification.".
        *   **Case 3: Credit Score < 700 (and Credit Score is Found) AND KYCStatus == "Updated"**
            Determine the retrieved CreditScore. Call `update_application_record_and_log` with `final_status`="Pending Manual Review - Credit Score", and for `orchestrator_notes` construct a string like "Manual Review: CreditScore=YYY (below 700), KYCStatus=Updated." replacing YYY.
            Call `send_credit_decision_email` for "Further Review Needed", `reason`="Application requires further review due to credit score.".
        *   **Case 4: Credit Score < 700 (and Credit Score is Found) AND (KYCStatus == "Not Updated" OR KYCStatus == "Unknown" OR KYCStatus is Not Found/Null)**
            Determine the retrieved CreditScore and KYCStatus. Call `update_application_record_and_log` with `final_status`="Rejected - Credit Score and KYC", and for `orchestrator_notes` construct a string like "Rejected: CreditScore=YYY (below 700), KYCStatus=ZZZ not updated/unknown." replacing YYY and ZZZ.
            Call `send_credit_decision_email` for "Rejected", `reason`="Credit score and/or KYC information did not meet requirements.".
        *   **Case 5: Credit Score is Not Found/Null AND KYCStatus == "Updated"**
            Call `update_application_record_and_log` with `final_status`="Pending Manual Review - Credit Score", `orchestrator_notes`="Manual Review: CreditScore=Not Found, KYCStatus=Updated.".
            Call `send_credit_decision_email` for "Further Review Needed", `reason`="Unable to retrieve credit score; KYC is updated.".
        *   **Case 6: Credit Score is Not Found/Null AND (KYCStatus == "Not Updated" OR KYCStatus == "Unknown" OR KYCStatus is Not Found/Null)**
            Determine the retrieved KYCStatus. Call `update_application_record_and_log` with `final_status`="Rejected - Credit Score and KYC", and for `orchestrator_notes` construct a string like "Rejected: CreditScore=Not Found, KYCStatus=ZZZ not updated/unknown." replacing ZZZ.
            Call `send_credit_decision_email` for "Rejected", `reason`="Credit score could not be retrieved and/or KYC information not updated.".

4.  **Provide Summary:** After processing all applications in the batch, provide a conversational summary:
    *   "I have processed X applications from the current batch."
    *   "Y applications were Approved."
    *   "Z applications were Rejected (you can state reasons if easily summarized, e.g., M for DTI, N for Age)."
    *   "W applications have been sent for Manual Review."

5.  **Conclude:** Thank the user and end the current processing interaction.
You MUST use the provided tools for actions. Do not invent data not retrievable by tools. Be methodical.
""".replace("{current_date}", datetime.today().strftime("%Y-%m-%d")) # This replacement for {current_date} is fine.

root_agent = Agent(
    model="gemini-2.5-flash-preview-04-17",
    name="credit_card_application_orchestrator_v2",
    description="Orchestrates pre-screening of credit card applications with data reset.",
    instruction=agent_instructions,
    tools=[
        initialize_run_data_tool, # Added new tool
        get_new_applications_tool,
        get_credit_score_tool,
        get_kyc_details_tool,
        update_application_log_tool,
        send_email_tool,
    ],
    planner=google.adk.planners.BuiltInPlanner(
        thinking_config=genai_types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=24500 # Slightly increased for the extra init step
        )
    )
)

# --- Utility Function for Display (not an ADK tool) ---
def display_processed_applications_summary():
    # (Function definition as before - no changes needed here)
    print("\n--- Summary of Processed Applications (from mock_db['processed_applications_log']) ---")
    if not mock_db["processed_applications_log"]:
        print("No applications have been processed and logged yet in this run.")
        return

    print(f"Total applications in processed_applications_log: {len(mock_db['processed_applications_log'])}")
    print("-" * 120)
    print(f"{'ApplicationID':<12} | {'CustomerID':<10} | {'FirstName':<12} | {'LastName':<12} | {'FinalStatus':<40} | {'Notes'}")
    print("-" * 120)
    for app in mock_db["processed_applications_log"]:
        notes = app.get('OrchestratorNotes', 'N/A')
        notes_display = (notes[:50] + '...') if notes and len(notes) > 53 else notes
        print(f"{app.get('ApplicationID', 'N/A'):<12} | {app.get('CustomerID', 'N/A'):<10} | {app.get('FirstName', 'N/A'):<12} | {app.get('LastName', 'N/A'):<12} | {app.get('FinalStatus', 'N/A'):<40} | {notes_display}")
    print("-" * 120)

    print("\nApplications in needs_manual_review_applications:")
    if mock_db["needs_manual_review_applications"]:
        for app in mock_db["needs_manual_review_applications"]:
            print(f"  - {app.get('ApplicationID')}: Status='{app.get('FinalStatus')}', Notes='{app.get('OrchestratorNotes')}'")
    else:
        print("  No applications flagged for manual review in this run.")
    print("-" * 100)

def display_full_mock_db_snapshot_and_summary():
    print("\n\n--- Mock DB State & Processing Summary After Agent Run ---")

    print("\n1. Final State of 'new_credit_applications' list (Original Source Data Updates):")
    print("   This shows the status of applications that were initially in 'Pending Review'.")
    if mock_db.get("new_credit_applications"):
        print("-" * 150) # Adjusted width for new column
        print(f"{'ApplicationID':<12} | {'CustomerID':<10} | {'FirstName':<12} | {'LastName':<12} | {'InitialStatus':<15} | {'FinalStatus':<40} | {'OrchestratorNotes'}")
        print("-" * 150)
        
        pending_in_new_list_count = 0
        
        # Iterate through the current state of mock_db["new_credit_applications"]
        # which was initialized from _initial_new_applications_data_template by the agent
        for current_app_state in mock_db.get("new_credit_applications", []):
            app_id = current_app_state.get('ApplicationID')
            
            # Find the corresponding original record in the template to confirm its initial status
            # This assumes the agent's initialize_run_data tool correctly copied everything.
            original_app_in_template = next(
                (app_template for app_template in _initial_new_applications_data_template 
                 if app_template.get("ApplicationID") == app_id), 
                None
            )
            
            initial_status_display = original_app_in_template.get("FinalStatus", "N/A in template") if original_app_in_template else "N/A (Not found in template)"

            notes = current_app_state.get('OrchestratorNotes', '')
            notes_display = (notes[:40] + '...') if notes and len(notes) > 43 else notes # Adjusted truncation
            
            print(
                f"{app_id:<12} | "
                f"{current_app_state.get('CustomerID', 'N/A'):<10} | "
                f"{current_app_state.get('FirstName', 'N/A'):<12} | "
                f"{current_app_state.get('LastName', 'N/A'):<12} | "
                f"{initial_status_display:<15} | " # Showing it was 'Pending Review' from template
                f"{current_app_state.get('FinalStatus', 'N/A'):<40} | " # Showing the new status
                f"\"{notes_display}\""
            )
            if current_app_state.get("FinalStatus") == "Pending Review":
                pending_in_new_list_count +=1
        print("-" * 150)
        print(f"  Number of apps still 'Pending Review' in 'new_credit_applications' (after processing): {pending_in_new_list_count} (should be 0 if all fetched applications were processed by the agent)")
    else:
        print("  'new_credit_applications' list in mock_db is empty or not found (agent might not have initialized it via tool yet).")
    print("-" * 70)


    print("\n2. Content of 'processed_applications_log' (Chronological Log of Processed Apps):")
    if not mock_db.get("processed_applications_log"):
        print("  'processed_applications_log' is empty.")
    else:
        print(f"  Total applications in processed_applications_log: {len(mock_db['processed_applications_log'])}")
        print("-" * 120) # Adjusted width
        print(f"{'ApplicationID':<12} | {'CustomerID':<10} | {'FirstName':<12} | {'LastName':<12} | {'FinalStatus':<40} | {'OrchestratorNotes'}")
        print("-" * 120)
        for app in mock_db["processed_applications_log"]:
            notes = app.get('OrchestratorNotes', 'N/A')
            notes_display = (notes[:30] + '...') if notes and len(notes) > 33 else notes # Adjusted truncation
            print(f"{app.get('ApplicationID', 'N/A'):<12} | {app.get('CustomerID', 'N/A'):<10} | {app.get('FirstName', 'N/A'):<12} | {app.get('LastName', 'N/A'):<12} | {app.get('FinalStatus', 'N/A'):<40} | {notes_display}")
        print("-" * 120)
    print("-" * 70)

    print("\n3. Content of 'needs_manual_review_applications':")
    if not mock_db.get("needs_manual_review_applications"):
        print("  'needs_manual_review_applications' is empty.")
    else:
        print(f"  Total applications in needs_manual_review_applications: {len(mock_db['needs_manual_review_applications'])}")
        for app in mock_db["needs_manual_review_applications"]:
            print(f"  - AppID: {app.get('ApplicationID')}, Status='{app.get('FinalStatus')}', Notes='{app.get('OrchestratorNotes')}'")
    print("-" * 70)
# --- Main Execution (Async for testing) ---
async def run_agent_workflow():
    print("--- Credit Card Application Orchestrator Agent Initializing for a Run ---")
    # Note: The agent itself is now instructed to call the 'initialize_run_data' tool
    # as its very first step when it starts processing. So, we don't explicitly
    # reset or initialize mock_db here before invoking the agent.
    # The initial state of mock_db (empty lists) is set when the module loads.

    # The agent's first action, guided by instructions, will be to populate mock_db.
    # We can print the state of mock_db *before* the agent call if we want to be verbose,
    # but it will be empty or as it was from a previous script run if not re-initialized.
    # For a clean demo via `python agent.py`, the module-level mock_db starts fresh.

    print(f"State of mock_db BEFORE agent invocation (should be reset by agent's first tool call):")
    print(f"  Initial 'new_credit_applications' count: {len(mock_db.get('new_credit_applications', []))}")
    print(f"  Initial 'processed_applications_log' count: {len(mock_db.get('processed_applications_log', []))}")
    print(f"  Initial 'needs_manual_review_applications' count: {len(mock_db.get('needs_manual_review_applications', []))}")
    print("-" * 70)

    initial_user_query = (
        "Hello, I'd like to process the new batch of credit card applications. "
        "Please start by preparing the data for this run, then proceed with the review."
    )
    
    print(f"Invoking Agent with initial prompt: '{initial_user_query}'")
    
    # Assuming 'root_agent' is your globally defined Agent instance
    final_agent_response = await root_agent.run(
        prompt=initial_user_query
    )
    
    print("-" * 70)
    print("--- Agent Workflow Run Complete ---")

    if final_agent_response and final_agent_response.output:
        print("\nAgent's Final Conversational Output (expected to be from generate_final_processing_summary tool):")
        print(final_agent_response.output) 
    else:
        print("\nAgent did not return a final conversational output, or the output was empty.")
    
    # Now, display the detailed snapshot and summary from the mock_db's state
    # *after* the agent has run and (presumably) modified it.
    # The 'display_full_mock_db_snapshot_and_summary' function is defined elsewhere in the file.
    display_full_mock_db_snapshot_and_summary()

    # An additional check for clarity on the original 'new_credit_applications' list
    # The 'display_full_mock_db_snapshot_and_summary' function already does a good job of this.
    # We can add a simple count here too.
    pending_count_in_new_list_final = 0
    if mock_db.get("new_credit_applications"):
        pending_count_in_new_list_final = sum(
            1 for app in mock_db["new_credit_applications"] if app.get("FinalStatus") == "Pending Review"
        )
    print(f"\nVerification: Number of apps still 'Pending Review' in 'new_credit_applications' after run: {pending_count_in_new_list_final} (should be 0 if all were processed).")
    print("-" * 70)

if __name__ == "__main__":
    # CRITICAL: Ensure _initial_new_applications_data_template, 
    # _credit_bureau_scores_template, and _kyc_database_template 
    # are fully populated with your 15/10/10 records respectively at the module level.
    
    # Perform the data template population checks
    if not (_initial_new_applications_data_template and 
            len(_initial_new_applications_data_template) >= 15 and
            _credit_bureau_scores_template and 
            len(_credit_bureau_scores_template) >= 10 and
            _kyc_database_template and 
            len(_kyc_database_template) >= 10):
        print("FATAL: One or more data templates (_initial_new_applications_data_template, "
              "_credit_bureau_scores_template, _kyc_database_template) "
              "are not fully populated as expected (15, 10, 10 records respectively). Please check the script. Exiting.")
        # exit() # You might want to uncomment this to actually stop if data is missing for critical runs.
    else:
        print("Initial data templates appear to be populated with the required number of records.")
        print("Starting agent workflow. The agent will initialize its run data as its first step...")
        
        # No explicit reset call here; the agent's first instructed action is to call
        # the initialize_run_data_tool.
        asyncio.run(run_agent_workflow())

        print("\nScript execution finished.")