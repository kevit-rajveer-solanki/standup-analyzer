# Standup Attendance Extractor

## Project Overview

The Standup Attendance Extractor is a two-part application designed to analyze attendance for online standup meetings using the Microsoft Graph API. It provides insights into meeting attendance, identifies high-performing attendees, and generates team-specific attendance reports.

- **Backend (FastAPI):** Handles authentication with the Microsoft Graph API, retrieves meeting attendance records, resolves user and meeting details, and processes the raw data.
- **Frontend (Streamlit):** Offers a user-friendly interface for inputting required parameters (authentication token, organizer email, meeting link, date range) and visualizes the processed attendance data through various reports and charts.

## How to Run the Project

Follow these steps to set up and run the Standup Attendance Extractor:

### Prerequisites

*   Python 3.8+
*   `pip` (Python package installer)
*   Access to Microsoft Graph API with an application token that has the necessary permissions to read online meeting attendance reports and user details.

### 1. Set up the Python Virtual Environment

It's recommended to use a virtual environment to manage dependencies.

```bash
python -m venv myenv
source myenv/bin/activate  # On Windows, use `myenv\Scripts\activate`
```

### 2. Install Dependencies

Install the required Python packages for both the backend and frontend.

```bash
pip install -r requirements.txt
```

### 3. Run the Backend

Navigate to the project directory and start the FastAPI backend server.

```bash
uvicorn backend:app --host 0.0.0.0 --port 8000
```

The backend will run on `http://localhost:8000`. Keep this terminal open.

### 4. Run the Frontend

Open a **new terminal**, activate your virtual environment, and then start the Streamlit frontend application.

```bash
source myenv/bin/activate  # On Windows, use `myenv\Scripts\activate`
streamlit run frontend.py
```

This will open the Streamlit application in your web browser, usually at `http://localhost:8501`.

### 5. Using the Application

1.  **Paste Application Token:** In the Streamlit sidebar, enter your Microsoft Graph API application bearer token.
2.  **Enter Meeting Details:** Provide the email address of the meeting organizer and the full meeting link.
3.  **Select Date Range:** Choose the start and end dates for the attendance analysis.
4.  **Generate Report:** Click the "Generate Report" button to fetch and visualize the attendance data.

The application will then display a quarterly snapshot, high-performer list, team-wise reports, and raw attendance data.