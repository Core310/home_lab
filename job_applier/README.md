# ApplyPilot Automated Job Application Pipeline

A hybrid, CSV-driven autonomous job application pipeline managed via Ansible.

---

## Architecture Overview

```text
job_applier/
├── run.sh                          # 1-click execution wrapper (with auto sudo elevation)
├── site.yml                        # Master Ansible playbook
├── files/
│   ├── applypilot_runner.py        # Python CSV batch orchestrator & state updater
│   ├── plain_text_resume.yaml      # Master structured resume template
│   ├── config.yaml                 # ApplyPilot & runner configuration
│   ├── .env.example                # LLM API keys & ATS password secrets template
│   └── jobs.csv                    # CSV job target & status tracking sheet
├── app/                            # Generated operational directory on D drive
│   ├── .venv/                      # Isolated Python virtual environment
│   ├── repo/                       # Cloned ApplyPilot upstream repository
│   ├── jobs.csv                    # Live tracking sheet
│   ├── plain_text_resume.yaml      # Live resume data
│   ├── config.yaml                 # Live configuration
│   ├── .env                        # Live API secrets
│   └── run_batch.sh                # Executable batch runner
└── README.md
```

---

## Quick Start Guide

### 1. Deploy the Environment
Run the setup playbook:
```bash
./run.sh
```

### 2. Configure Your Resume & API Keys
1. Edit **`app/plain_text_resume.yaml`** with your personal information, work experience, education, and demographic answers.
2. Edit **`app/.env`** and add your LLM API keys (e.g. Anthropic Claude, OpenAI, or Gemini):
   ```env
   ANTHROPIC_API_KEY=sk-ant-api03-...
   WORKDAY_PASSWORD=YourUniversalWorkdayPassword123!
   ```

### 3. Add Target Job Links
Open **`app/jobs.csv`** and paste job links you want to apply for:
```csv
Target URL,Job Title,Company,Status,Date Applied,Notes
https://boards.greenhouse.io/example/jobs/1234567,DevOps Engineer,Acme Cloud,Pending,,
https://jobs.lever.co/example/9876543,Site Reliability Engineer,NextGen Systems,Pending,,
```

### 4. Run the Batch Orchestrator
To simulate without submitting:
```bash
cd app && ./run_batch.sh --dry-run
```

To run live applications:
```bash
cd app && ./run_batch.sh
```

---

## Command-Line Options

```bash
python3 applypilot_runner.py [OPTIONS]

Options:
  -c, --csv PATH       Path to jobs.csv file (default: jobs.csv)
  -r, --resume PATH    Path to plain_text_resume.yaml (default: plain_text_resume.yaml)
  --config PATH        Path to config.yaml (default: config.yaml)
  -l, --limit INT      Max number of pending applications to process (default: all)
  -d, --delay INT      Seconds to wait between applications (default: 5)
  --dry-run            Simulate execution without submitting forms
  --headless           Run browser in headless mode (default: True)
```
