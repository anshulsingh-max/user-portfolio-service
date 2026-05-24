FROM python:3.14

RUN mkdir -p /opt/services/user-portfolio-service/src
ENV PYTHONDONTWRITEBYTECODE 1

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY . /opt/services/user-portfolio-service/src
WORKDIR /opt/services/user-portfolio-service/src
RUN chmod +x /opt/services/user-portfolio-service/src/scripts/docker-run.sh

# expose the port 80
EXPOSE 80
CMD ["/opt/services/user-portfolio-service/src/scripts/docker-run.sh"]
