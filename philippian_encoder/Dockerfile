FROM python:3.12-alpine

WORKDIR /usr/src/app

RUN pip install --upgrade pip

COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

COPY ./entrypoints/entrypoint.sh /usr/src/app/entrypoints/entrypoint.sh
COPY . /usr/src/app/

RUN chmod +x ./entrypoints/entrypoint.sh
ENTRYPOINT [ "/usr/src/app/entrypoints/entrypoint.sh" ]
