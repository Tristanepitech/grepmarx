FROM nikolaik/python-nodejs:python3.10-nodejs20-slim

WORKDIR /opt/grepmarx

ENV FLASK_APP run.py

RUN apt-get upgrade -y --fix-missing
RUN apt-get update

RUN apt-get install git-all -y
RUN git config --global user.email "you@example.com"
RUN git config --global user.name "Your Name"
# Supervisord install & configuration
RUN apt-get install -y supervisor
RUN mkdir -p /var/log/supervisor
COPY supervisord-docker.conf /etc/supervisor/conf.d/supervisord.conf

# Copy required files into the container
COPY entrypoint.sh run.py gunicorn-cfg.py requirements.txt requirements-pgsql.txt ./
COPY .env-docker .env
COPY nginx nginx
COPY app app
COPY migrations migrations
RUN mkdir data

# Install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements-pgsql.txt

# Dependency scan (cdxgen / depscan) requirements
# RUN apt-get update -y --fix-missing
# RUN apt-get install -y npm openjdk-21-jdk maven gradle golang composer --fix-missing
# RUN apt-get clean
# RUN npm install -g @cyclonedx/cdxgen@11.1.4

# Application Inspector dependencies (dotnet runtime)
# RUN apt-get install wget gpg -y
# RUN wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg && install -D -o root -g root -m 644 microsoft.gpg /usr/share/keyrings/microsoft.gpg && rm -f microsoft.gpg
# RUN wget https://packages.microsoft.com/config/debian/13/packages-microsoft-prod.deb -O packages-microsoft-prod.deb 
# RUN dpkg -i packages-microsoft-prod.deb
# RUN rm packages-microsoft-prod.deb
# RUN apt-get update --fix-missing
# RUN apt-get install -y dotnet-runtime-9.0

# Downloaded packages cleaning
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

EXPOSE 5000
#EXPOSE 443

RUN chmod u+x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
