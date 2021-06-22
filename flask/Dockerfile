FROM ubuntu:18.04
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN pip3 install flask pymongo
RUN mkdir /project2
RUN mkdir -p /project2/data
COPY app.py /project2/app.py
ADD data /project2/data
EXPOSE 5000
WORKDIR /project2
ENTRYPOINT [ "python3","-u","app.py" ]