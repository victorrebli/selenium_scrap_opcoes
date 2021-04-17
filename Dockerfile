#Sistema Operacional
FROM ubuntu:20.04
#FROM ubuntu:18.04
ENV PYTHONUNBUFFERED True
ENV TZ=Europe/Kiev
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
#Dependências do sistema
RUN apt-get update -y
RUN apt-get install -y python3-dev python3-pip build-essential
#RUN apt-get install -y gconf-service libasound2 libatk1.0-0
RUN apt-get install -y gconf-service libasound2 libatk1.0-0 libcairo2 libcups2 libfontconfig1 libgdk-pixbuf2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libxss1 fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils
RUN apt-get install -y wget
# Install Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install

#Pacotes do Python
COPY requirements.txt /requirements.txt
#ENV APP_HOME /app
#WORKDIR $APP_HOME
#COPY . .

RUN pip3 install --upgrade pip #Atualização do gerenciador de pacotes
RUN pip3 install -r requirements.txt  #Instalação dos pacotes listados
#RUN pip3 install jupyter #Instalação do pacote jupyter notebook
#Diretório do usuário docker
RUN mkdir -p /home/user
WORKDIR /home/user
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . .
ENTRYPOINT ["python3","main.py"]
