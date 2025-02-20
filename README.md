### Steps-by-step

1. Create virtual environment
2. Installed Django
    > pip install django

3. Installed celery
    > pip install celery

4. Installed Redis
    > pip install redis

5. Create requirements.txt file for installed packages inside django_project_name:
    > pip freeze > requirements.txt

6. Create a django project
    > django-admin startproject project_name


7. Create an Environment variables ".env"
    ENV:
        DEBUG=1
        SECRET_KEY='django-insecure-_n5#*a6%8cf0m)i7+yc!vep71im1zkrgn#)rj3yd9(f5*zude)'
        ALLOWED_HOSTS='localhost,127.0.0.1'
        PYTHONDONTWRITEBYTECODE=1
        PYTHONUNBUFFERED=1


8. Create an entrypoint "entrypoint.sh" for the django project
    django_project_name:
        entrypoints:
            entrypoints.sh:
                #!/bin/ash
                python manage.py migrate
                exec "$@"

9. Update the project settings "settings.py"
    django_project_name:
        django_project_name (sub):
            settings.py:
                import os
                # SECURITY WARNING: keep the secret key used in production secret!
                SECRET_KEY = os.environ.get("SECRET_KEY")

                # SECURITY WARNING: don't run with debug turned on in production!
                DEBUG = os.environ.get("DEBUG")

                ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS").split(",")

                CELERY_BROKER_URL = os.environ.get("CELERY_BROKER", "redis://redis:6379/0")
                CELERY_RESULT_BACKEND = os.environ.get("CELERY_BACKEND", "redis://redis:6379/0")


10. Create Dockerfile for django_project_name.
    django_project_name:
        Dockerfile:
            FROM python:3.12-alpine

            WORKDIR /usr/src/app

            RUN pip install --upgrade pip

            COPY ./requirements.txt /usr/src/app/requirements.txt
            RUN pip install -r requirements.txt

            COPY ./entrypoints/entrypoint.sh /usr/src/app/entrypoints/entrypoint.sh
            COPY . /usr/src/app/

            RUN chmod +x ./entrypoints/entrypoint.sh
            ENTRYPOINT [ "/usr/src/app/entrypoints/entrypoint.sh" ]

11. Add celery script "celery.py" on (sub) django_project_name:
    django_project_name:
        django_project_name (sub):
            celery.py:
                import os
                from celery import Celery

                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djcelery.settings')
                app = Celery("djcelery")
                app.config_from_object("django.conf:settings", namespace="CELERY")
                app.autodiscover_tasks()

12. Declare celery to be accessable to entire projects.
    django_project_name:
        django_project_name (sub):
            __init__.py:
                
                # This will make sure the app is always imported when
                # Django starts so that shared_task will use this app.

                from .celery import app as celery_app

                __all__ = ('celery_app',)

13. Build and run docker image
    > docker-compose -f docker-compose-local.yml up --build -d 

    To shutdown or remove the container:
    > docker-compose -f docker-compose-local.yml down


14. To create new Django App:
    Enter container shell,
    > docker exec -it django /bin/sh 

    You should be inside the "/usr/src/app/". Then run:
    > 

15. 


Reference:
Python Django Celery Course
https://www.youtube.com/watch?v=Dw2thMl1dGY&list=PLOLrQ9Pn6cayGytG1fgUPEsUp3Onol8V7&index=10




### How to Make Data Models Migrations
> python manage.py makemigrations
> python manage.py migrate


### To create a new app within the project directory
1. Go inside the docker container of django.
> docker exec -it django /bin/sh 
2. Create new django app
> python manage.py startapp myapp



### Create superuser admin in django
> python manage.py createsuperuser


