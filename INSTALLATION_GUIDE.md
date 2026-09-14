# Fraud Detection System: Installation and User Guide

This guide is written for someone who has never used a programming project before. Follow the **Quick Demo** section first. It lets you open the dashboard without setting up the back-end services.

## 1. What this project does

The system is a fraud investigation dashboard. It includes:

- A web dashboard for viewing alerts, transactions, risk scores, biometrics, and fraud networks.
- A Python machine-learning service that scores transactions.
- A Spring Boot gateway for login and live dashboard requests.
- Optional MySQL and Kafka services for storing transactions and processing events.

## 2. Install the required programs

### Quick Demo requirements

Install these two programs on the computer:

1. **Git for Windows**: https://git-scm.com/download/win
2. **Node.js LTS**: https://nodejs.org/

After installing Node.js, restart the computer or open a new PowerShell window.

### Full live-system requirements

Install these as well:

- **Python 3.11**: https://www.python.org/downloads/
  - During installation, tick **Add Python to PATH**.
- **Java JDK 17**: https://adoptium.net/
- **Apache Maven**: https://maven.apache.org/download.cgi
- **Docker Desktop**: https://www.docker.com/products/docker-desktop/

Docker Desktop must be open before starting MySQL and Kafka.

## 3. Download the project

Open **PowerShell**:

1. Click the Windows Start button.
2. Type `PowerShell`.
3. Open **Windows PowerShell**.
4. Run these commands:

```powershell
cd $HOME\Desktop
git clone https://github.com/a12975735-dev/fraud.git
cd fraud
```

The project is now in a folder called `fraud` on the Desktop.

## 4. Quick Demo: easiest way to open the dashboard

This mode does not require Python, Java, Docker, MySQL, Kafka, or a database.

From the project folder, run:

```powershell
cd investigator-dashboard
npm install
npm run dev
```

Leave this PowerShell window open. It is running the website.

Open the address shown in the terminal. It is normally:

**http://localhost:5173**

On the login screen, click **Quick Demo Sign-In**. Do not use the regular gateway login in this mode. The demo account works without any back-end services and includes sample alerts and transactions.

### Stop the Quick Demo

Return to the PowerShell window and press `Ctrl+C` once.

## 5. Full live setup

The full setup uses four running services. Keep one PowerShell window open for each service.

### Step 1: Start MySQL and Kafka

From the project folder:

```powershell
docker compose up -d mysql kafka
```

Check that they are running:

```powershell
docker compose ps
```

Both services should show a running or healthy status.

### Step 2: Install Python packages

From the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run this once in PowerShell, then repeat the activation command:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### Step 3: Start the Python machine-learning API

Open a new PowerShell window and run:

```powershell
cd $HOME\Desktop\fraud
.\.venv\Scripts\Activate.ps1
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

Leave this window open. This service calculates fraud risk scores.

To check it, open this address in a browser:

**http://127.0.0.1:8000/**

You should see a message saying that the Fraud Detection Scoring API is running.

### Step 4: Start the credit and biometrics API

Open another PowerShell window and run:

```powershell
cd $HOME\Desktop\fraud
.\.venv\Scripts\Activate.ps1
python -m src.flask_api
```

Leave this window open. This service uses port `5000`.

### Step 5: Start the Spring Boot gateway

Open another PowerShell window and run:

```powershell
cd $HOME\Desktop\fraud\spring-gateway
$env:DB_URL="jdbc:mysql://localhost:3306/frauddetection"
$env:DB_USERNAME="fraud_gateway_user"
$env:DB_PASSWORD="change-me-local-password"
$env:SCORING_SERVICE_URL="http://localhost:8000"
$env:FLASK_SERVICE_URL="http://localhost:5000"
mvn spring-boot:run
```

Leave this window open. The gateway uses port `8081`.

### Step 6: Start the dashboard

Open one more PowerShell window and run:

```powershell
cd $HOME\Desktop\fraud\investigator-dashboard
npm install
npm run dev
```

Open the address shown in the terminal, normally:

**http://localhost:5173**

For live login, use:

- Username: `admin`
- Password: `demo-admin`

The **Quick Demo Sign-In** button is also available if you want to use the dashboard without live services.

## 6. What to click in the dashboard

- **Dashboard**: summary of risk and recent activity.
- **Transactions**: enter or review a transaction and run AI scoring.
- **Alerts**: review suspicious activity.
- **Biometric Monitor**: view behavioral biometrics demonstrations.
- **Investigation**: inspect an individual case.
- **Graph Network**: view links between devices, accounts, and beneficiaries.
- **Reports**: view available analysis reports.
- **Settings**: view dashboard settings.

## 7. Stopping the full system

For each PowerShell window running a service, press `Ctrl+C` once.

Then stop MySQL and Kafka from the project folder:

```powershell
docker compose down
```

The database data is kept in a Docker volume. Running `docker compose up -d mysql kafka` later will reuse it.

## 8. Common problems

### “npm is not recognized”

Node.js is not installed correctly, or PowerShell was open before Node.js was installed. Install Node.js LTS and open a new PowerShell window.

### “python is not recognized”

Install Python 3.11 and select **Add Python to PATH** during installation. Open a new PowerShell window afterward.

### The browser says “connection refused”

The dashboard service is not running. Return to the PowerShell window where `npm run dev` was started and check for an error. Start it again with:

```powershell
cd $HOME\Desktop\fraud\investigator-dashboard
npm run dev
```

Use the exact URL printed by Vite. If port `5173` is busy, Vite may choose `5174` or another port.

### Regular login does not work

Regular login requires the Spring Boot gateway on port `8081`. For a no-setup preview, use **Quick Demo Sign-In** instead.

### Docker services do not start

Open Docker Desktop, wait until it says it is running, and then retry:

```powershell
docker compose up -d mysql kafka
```

### A port is already in use

Close the other application using that port, or stop an old copy of the service with `Ctrl+C`. The expected ports are `3306` for MySQL, `9092` for Kafka, `5000` for Flask, `8000` for FastAPI, `8081` for Spring Boot, and `5173` for the dashboard.

## 9. Important note about training data

The large processed CSV training files are intentionally not stored in GitHub because GitHub rejects files larger than 100 MB. The dashboard demo and the included trained model files work without those CSV files. Keep the CSV files locally if you need to retrain the models.
