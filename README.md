\# Manufacturing Production \& Quality Control System



A FastAPI backend application for managing manufacturing operations, production planning, material inventory, quality inspection, machine maintenance, approvals, audit logs, and operational reporting.



\## 1. Project Overview



The system supports manufacturing workflows across these modules:



\- User authentication and role-based authorization

\- Plant and production-line management

\- Product and raw-material management

\- Bill of Materials (BOM)

\- Machine management

\- Production orders and production batches

\- Worker and shift management

\- Quality inspections and defect tracking

\- Machine maintenance and downtime tracking

\- Inventory movements

\- Production approval workflow

\- Dashboard and reports

\- Audit logs

\- Notifications

\- Security and performance controls



\## 2. Technology Stack



\- Python

\- FastAPI

\- Pydantic

\- SQLAlchemy ORM

\- SQLite database

\- JWT authentication

\- Pytest

\- Uvicorn

\- Alembic migrations, where configured

\- Docker, where configured



\## 3. Project Structure



```text

manufacturing-production-quality-control/

├── app/

│   ├── api/

│   ├── core/

│   ├── db/

│   ├── middleware/

│   ├── models/

│   ├── repositories/

│   ├── schemas/

│   ├── services/

│   ├── utils/

│   └── main.py

├── docs/

│   └── database\_er\_diagram.md

├── tests/

├── .env.example

├── .gitignore

├── README.md

├── alembic.ini                 # If configured

├── alembic/                    # If configured

├── Dockerfile                  # If configured

├── docker-compose.yml          # If configured

├── requirements.txt            # If present

└── manufacturing.db            # Local SQLite database; do not commit

```



The actual directory contents may differ depending on the files present in the repository.



\## 4. Prerequisites



Install:



\- Python 3.11 or a compatible version supported by the project dependencies

\- pip

\- Git, if cloning the repository

\- Docker, if using the Docker configuration



\## 5. Installation on Windows



Open PowerShell in the project directory.



```powershell

cd C:\\Users\\admin\\manufacturing-production-quality-control

```



Create a virtual environment if you do not already have one:



```powershell

python -m venv venv

```



Activate it:



```powershell

.\\venv\\Scripts\\Activate.ps1

```



Install dependencies using the project requirements file if it exists:



```powershell

pip install -r requirements.txt

```



If the requirements file is not present, install the project's actual dependencies before running the application. Do not install a different JWT or password-hashing library without checking the imports used by this project.



\## 6. Environment Configuration



Copy the example configuration:



```powershell

Copy-Item .env.example .env

notepad .env

```



Replace the JWT secret placeholder with a strong random value.



For example, to generate a random secret in PowerShell:



```powershell

$secret = \[Convert]::ToBase64String(

&#x20;   (1..48 | ForEach-Object { Get-Random -Maximum 256 })

)

$secret

```



Copy the generated value into your local `.env` file.



\*\*Configuration note:\*\* A `.env` file is not automatically loaded by Python. The application must load it explicitly or use environment variables supplied by the operating system or deployment platform. Confirm the settings implementation in `app/db/database.py` and `app/core/security.py`.



Never commit a real `.env` file or production secret to Git.



\## 7. Database



The default local database is SQLite:



```text

sqlite:///./manufacturing.db

```



The database file is normally created relative to the application's working directory when the database initialization code creates the schema.



Before starting with a fresh database, check the project's initialization and migration procedures. Avoid deleting an existing database containing test data or records you need.



\### Alembic migrations



If the Alembic configuration and migrations are present, apply them using:



```powershell

alembic upgrade head

```



To inspect the current migration revision:



```powershell

alembic current

```



Run these commands only after confirming that Alembic is configured for this project's database.



\## 8. Run the Application



From the project root, activate the virtual environment and run:



```powershell

uvicorn app.main:app --reload

```



The local API server should be available at:



```text

http://127.0.0.1:8000

```



Stop the development server with `Ctrl+C`.



\## 9. API Documentation



\### Swagger UI



http://127.0.0.1:8000/docs



Use Swagger UI to authenticate, supply request bodies, execute API operations, and inspect response status codes and JSON.



\### ReDoc



http://127.0.0.1:8000/redoc



The available API operations are generated from the FastAPI application.



\## 10. Main API Areas



The project includes endpoints for the following functional areas:



| Area | Purpose |

|---|---|

| Authentication | Registration, login, tokens, user access |

| Plants | Manage manufacturing plants |

| Production lines | Manage production lines |

| Products | Manage manufactured products |

| Raw materials | Manage materials and stock information |

| BOM | Define materials required for products |

| Machines | Manage production equipment |

| Production orders | Plan and track production work |

| Production batches | Track batch execution and output |

| Workers and shifts | Manage staff assignments and shifts |

| Quality inspections | Record quality checks |

| Defects | Track production defects |

| Maintenance and downtime | Record maintenance activities and machine downtime |

| Inventory movements | Track material inventory changes |

| Production approvals | Review and approve production work |

| Dashboard and reports | Review operational metrics |

| Audit logs | Review recorded system activities |

| Notifications | Create and manage notifications |



Use Swagger to confirm the exact paths, required roles, request fields, and response schemas implemented in the current version.



\## 11. Testing



Run the complete automated test suite:



```powershell

pytest -q

```



For more detailed output:



```powershell

pytest -v

```



The latest recorded full test run during development reported \*\*263 passed\*\*. Run the tests again before submission and update this section with the latest actual result.



\## 12. End-to-End Demo Workflow



Use valid IDs returned by earlier API responses when testing dependent endpoints.



A recommended demonstration sequence is:



1\. Register a user and log in.

2\. Create a plant.

3\. Create a production line under that plant.

4\. Create a product and raw materials.

5\. Create a Bill of Materials for the product.

6\. Register machines and workers.

7\. Create a production order.

8\. Create a production batch for the order.

9\. Assign workers and shifts as required.

10\. Start the batch and record production output.

11\. Perform a quality inspection.

12\. Record defects if applicable.

13\. Complete the required production approval workflow.

14\. Verify inventory movements.

15\. Record machine maintenance or downtime when applicable.

16\. Review the dashboard, reports, audit logs, and notifications.



Follow the actual endpoint requirements and allowed status transitions in Swagger. Capture successful responses for the final demonstration.



\## 13. Docker



If the repository contains a valid `Dockerfile` and Compose configuration, build and start the application using the project's configured Compose file:



```powershell

docker compose up --build

```



Otherwise, run the application locally using the instructions above. Docker deployment should be verified before describing it as a tested deployment option.



\## 14. Security Notes



\- Use a strong, unique JWT signing secret.

\- Do not commit credentials or production secrets.

\- Keep dependencies updated.

\- Use HTTPS in production.

\- Restrict access through role-based authorization.

\- Validate input and handle errors safely.

\- Configure production database credentials outside source code.

\- Review security and performance warnings before production deployment.



The default development configuration must not be treated as production-ready without the required security review.



\## 15. Submission Deliverables



Prepare and verify these items before submission:



1\. Complete FastAPI source code

2\. Database ER diagram

3\. Alembic migrations

4\. Swagger documentation

5\. Postman collection

6\. Unit and integration tests

7\. Docker configuration

8\. `.env.example`

9\. `README.md`

10\. Git repository

11\. API screenshots

12\. End-to-end demonstration





