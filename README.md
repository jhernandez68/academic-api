Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations accounts subjects notifications reports
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

JWT
POST /api/auth/token/

Swagger
/swagger

Core routes
POST /api/accounts/create_user/
POST /api/accounts/{id}/assign_role/
POST /api/subjects/{id}/assign_instructor/
POST /api/subjects/student/enroll/
GET /api/subjects/student/history/
GET /api/subjects/student/enrolled/
GET /api/subjects/student/approved/
GET /api/subjects/student/failed/
GET /api/subjects/student/gpa/
GET /api/subjects/instructor/assigned_subjects/
GET /api/subjects/instructor/students/?subject_id=
POST /api/subjects/instructor/grade/
POST /api/subjects/instructor/close/
GET /api/notifications/
GET /api/reports/student/{id}/
GET /api/reports/instructor/{id}/

Docker
cp .env.example .env
docker-compose up --build
