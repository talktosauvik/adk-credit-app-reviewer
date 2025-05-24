# Credit Card Application Reviewer Agent

This project implements an AI-powered orchestrator agent for the initial pre-screening, data enrichment, and preliminary decisioning for new credit card applications using the Google Agent Development Kit (ADK).

## 1. Problem Statement

Financial institutions face a high volume of credit card applications daily, primarily submitted via online channels. The initial review stage of these applications is operationally intensive and often a bottleneck. Human reviewers dedicate significant time to manually filter applications against basic, non-negotiable eligibility criteria (e.g., minimum age, fundamental income sufficiency, excessive debt-to-income ratios). This manual triage is not only costly and time-consuming but also introduces potential inconsistencies and delays the progression of viable applications to full underwriting. Consequently, this can negatively impact customer experience, increase operational overhead, and reduce the speed at which competitive credit products can be offered. Furthermore, for applications that pass initial hurdles, the subsequent manual coordination to retrieve and integrate crucial external data, such as credit scores and KYC (Know Your Customer) verification status, further extends processing times and diverts skilled underwriters from complex assessments.

## 2. Solution Statement

An AI-powered Orchestrator Agent will be implemented to automate the initial pre-screening, data enrichment, and preliminary decisioning for new credit card applications. This agent will systematically process each application by:

*   **Data Initialization:** Ensuring a fresh, consistent dataset for each processing batch by re-initializing its in-memory data store from predefined templates at the start of each run.
*   **Sequential Basic Eligibility Checks:** For each application, the agent will first:
    *   Calculate the applicant's age from their date of birth.
    *   Calculate the applicant's Debt-to-Income (DTI) ratio based on stated monthly income and debt payments.
    *   Apply non-negotiable rules: Reject if underage (e.g., < 18 years) or if DTI is too high (e.g., >= 40%).
*   **Conditional Data Enrichment & Initial Fraud Indicators:** For applications that successfully pass the basic eligibility checks, the Orchestrator Agent will then proceed to:
    *   Invoke a dedicated tool to retrieve the applicant's credit score from a simulated credit bureau system (using ApplicationID, CustomerID, and SSN_Last4).
    *   Invoke another dedicated tool to retrieve the applicant's KYC status from a simulated internal KYC database (using ApplicationID and CustomerID). An "Updated" KYC status provides a foundational layer of identity verification, acting as an initial check against obviously fraudulent or synthetic identities. Applications with "Not Updated" or "Unknown" KYC status will be flagged for further scrutiny.
*   **Automated Preliminary Decisioning:** Based on the combination of the initial checks and the retrieved credit score and KYC status, the agent will apply a predefined decision matrix to categorize each application as:
    *   **Approved:** If the credit score is high (e.g., >= 700) and KYC is "Updated."
    *   **Rejected:** If credit score is low (e.g., < 700) and KYC is not "Updated" or "Unknown," or due to earlier age/DTI failures.
    *   **Pending Manual Underwriting Review:** For cases such as good credit score but problematic KYC (a potential fraud flag), or low credit score but good KYC, or if data retrieval for score/KYC fails.
*   **Record Keeping & Notifications:** The agent will:
    *   Log its actions and the final status for each application in an internal processing log (simulated in-memory).
    *   Update the status of the original application records.
    *   Trigger simulated email notifications to applicants regarding the preliminary outcome of their application (Approved, Rejected with reason, or Further Review Needed).
*   **Batch Summary:** Conclude by providing a comprehensive summary of the batch processing results, detailing the number of applications approved, rejected (with a breakdown by primary reason), and sent for manual review.

This automated process will ensure rapid and consistent initial filtering, efficient data gathering, accurate application of business rules, and provides an initial layer of fraud mitigation through KYC status checks. It will free up human underwriters to focus their expertise on applications requiring nuanced judgment (including those flagged for potential fraud), thereby improving overall efficiency, reducing errors, enhancing customer turnaround times, and strengthening risk management.

## Features Summary

*   Automated data initialization for each processing batch.
*   Sequential basic eligibility checks (Age, Debt-to-Income Ratio).
*   Conditional data enrichment (Credit Score & KYC Status via simulated tools).
*   Automated preliminary decisioning based on configurable rules.
*   Logging of actions and final application statuses.
*   Simulated email notifications to applicants.
*   Generation of a comprehensive batch processing summary.

## Project Structure

## Setup

1.  **Clone the repository (if you haven't already):**
    ```bash
    # If cloning from GitHub later:
    # git clone <repository-url>
    # cd credit_app_reviewer
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    *   Copy `.env.example` to a new file named `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Open the `.env` file and fill in your actual `GOOGLE_API_KEY` for the Gemini model.

## Running the Agent Locally
  *   run adk web in side your root folder


## Potential Enhancements & Future Scope

While the current agent provides significant automation for pre-screening, its capabilities can be further enhanced, particularly in the realm of advanced fraud detection and more comprehensive risk assessment. Future iterations could include:

*   **Advanced Fraud Detection Tools & Logic:**
    *   IP Address Tracing & Geolocation Verification: Integrate a tool to check the applicant's IP address against their stated address for inconsistencies (e.g., high-risk regions, proxy usage).
    *   Device Fingerprinting: Incorporate checks for device anomalies or known fraudulent device IDs.
    *   Velocity Checks: Implement logic to detect rapid, multiple applications from the same source (IP, device, email pattern, SSN proximity) within a short timeframe, which can indicate automated fraud attempts.
    *   Data Consistency Checks: Add tools to cross-reference provided information (name, address, SSN) against third-party identity verification services or internal negative lists beyond basic KYC.
    *   Behavioral Analytics Integration: Connect with systems that analyze application behavior for suspicious patterns.
*   **Enhanced Data Integration:**
    *   Open Banking/Account Aggregation: With customer consent, integrate tools to verify stated income and debt directly from financial institutions.
    *   Alternative Credit Data: Incorporate tools to access alternative credit data sources for thin-file applicants.
*   **More Granular Risk Scoring:**
    *   Instead of binary pass/fail on credit score, integrate a more nuanced internal risk scoring model that considers a wider array of variables, including those from the enhanced fraud checks.
*   **Machine Learning for Anomaly Detection:**
    *   Train and deploy a machine learning model (e.g., on Vertex AI) that the agent can call as a tool. This model could be trained on historical application data to identify subtle patterns indicative of fraud or high risk that rule-based systems might miss.
*   **Dynamic Rule Engine:**
    *   Move business rules (age, DTI thresholds, credit score cutoffs, fraud parameters) to an external, easily updatable configuration store or a dedicated business rules engine (BRE), allowing for quicker adjustments without code changes.
*   **Human-in-the-Loop Refinement:**
    *   For applications sent to manual review, capture the underwriter's final decision and reasoning. This feedback can be used to refine the agent's rules, instructions, or retrain any ML models over time.

By incorporating these enhancements, the orchestrator agent can evolve into a more sophisticated system, further improving underwriting efficiency, accuracy, and significantly bolstering the institution's defenses against increasingly complex fraud schemes.
