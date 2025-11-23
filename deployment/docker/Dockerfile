FROM python:3.11-alpine
LABEL authors="cappe"

RUN mkdir /src
WORKDIR /src

COPY ./src /src

RUN pip install --no-cache -r requirements/requirements.txt
RUN pip install --no-cache -r requirements.txt

RUN python manage.py collectstatic --noinput

EXPOSE 8000
ENTRYPOINT ["python", "manage.py", "runserver", "8000"]