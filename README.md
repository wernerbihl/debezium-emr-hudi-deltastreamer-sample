# Hudi Deltastreamer with Postgres + Debezium + EMR + PySpark + S3

The hardest part of getting real time data from databases to S3 is setting up Debezium correctly. So majority of this course will focus on setting up Debezium and then setting up the rest of the infrastructure to accommodate streaming. Even though this course is focused on streaming from Postgres, it can easily be adapted to any database connection supported by Debezium once set up.

## What we're building

![Preview](https://raw.githubusercontent.com/wernerbihl/debezium-emr-hudi-deltastreamer-sample/master/preview.png)

## Intro

Debezium is a massively scalable realtime database streaming open source project. It achieves this by using Kafka Connectors to hook into each database's binary logstream and sending the changes as Kafka topics. In production environments you should use Kubernetes/AWS EKS to host the required infrastructure for zookeeper, kafka, kafka connect and debezium. There are instructions for setting this up here: https://debezium.io/documentation/reference/stable/operations/kubernetes.html

However, this tutorial will focus on setting up Debezium and it's required services on a single instance for demonstration and development purposes. In our case, we'll use a master EMR node to set up Debezium from scratch. We'll assume only Spark is running on your EMR cluster. You can skip steps for services you already have set up.

## Step 1: Install Java or check that it's installed

When logged into your EMR cluster. Make sure you have java v1.8 or higher.

```
java -version
```

Otherwise install Java. For Amazon Linux 2 on EMR:

```
sudo amazon-linux-extras enable corretto8
sudo yum install java-1.8.0-amazon-corretto
```

## Step 2: Install Zookeeper

### 2.1 Create Zookeeper User

Create zookeeper user. It's ok if username already exists

```
sudo useradd zookeeper -m
```

Add user to sudoers group:

```
sudo usermod -aG wheel zookeeper
```

Create zookeeper data folder and give write access to zookeeper user:

```
sudo mkdir -p /data/zookeeper
sudo chown -R zookeeper:zookeeper /data/zookeeper
```

### 2.2 Install Zookeeper

You can find the latest stable version of Zookeeper here: https://zookeeper.apache.org/releases.html

```
cd /opt
sudo wget https://dlcdn.apache.org/zookeeper/zookeeper-3.7.1/apache-zookeeper-3.7.1-bin.tar.gz
sudo tar -xvf apache-zookeeper-3.7.1-bin.tar.gz
sudo mv apache-zookeeper-3.7.1-bin zookeeper
sudo rm apache-zookeeper-3.7.1-bin.tar.gz
sudo chown -R zookeeper:zookeeper /opt/zookeeper
```

### 2.3 Configure Zookeeper data folder and ports

In the following file: /opt/zookeeper/conf/zoo.cfg

Change the following parameters to avoid ports clashing with other ports running on EMR:

```
# /opt/zookeeper/conf/zoo.cfg
dataDir = /data/zookeeper
clientPort = 20182
admin.serverPort = 80082
```

### 2.4 Run Zookeeper as a service:

Create the following file: /etc/systemd/system/zookeeper.service and add the following to it:

```
# /etc/systemd/system/zookeeper.service
[Unit]
Description=Zookeeper Daemon
Documentation=http://zookeeper.apache.org
Requires=network.target
After=network.target

[Service]
Type=forking
WorkingDirectory=/opt/zookeeper
User=zookeeper
Group=zookeeper
ExecStart=/opt/zookeeper/bin/zkServer.sh start /opt/zookeeper/conf/zoo.cfg
ExecStop=/opt/zookeeper/bin/zkServer.sh stop /opt/zookeeper/conf/zoo.cfg
ExecReload=/opt/zookeeper/bin/zkServer.sh restart /opt/zookeeper/conf/zoo.cfg
TimeoutSec=30
Restart=on-failure

[Install]
WantedBy=default.target
```

Enable and start the service:

```
sudo systemctl daemon-reload
sudo systemctl start zookeeper
sudo systemctl enable zookeeper
```

## Step 3: Install Kafka

### 3.1 Create Kafka User

Create Kafka user. It's ok if username already exists

```
sudo useradd kafka -m
```

Add user to sudoers group:

```
sudo usermod -aG wheel kafka
```

Create Kafka logs folder and give write access to kafka user:

```
sudo mkdir -p /tmp/kafka-logs
sudo chown -R kafka:kafka /tmp/kafka-logs
```

### 3.2 Install Kafka

You can find the latest stable version of Kafka here: https://kafka.apache.org/downloads

```
cd /opt
sudo wget https://downloads.apache.org/kafka/3.3.2/kafka_2.13-3.3.2.tgz
sudo tar -xzf kafka_2.13-3.3.2.tgz
sudo mv kafka_2.13-3.3.2 kafka
sudo rm kafka_2.13-3.3.2.tgz
sudo chown -R kafka:kafka /opt/kafka
```

### 3.3 Configure Kafka

In the following file: /opt/kafka/config/zookeeper.properties, change the data folder and port as set up in step 2.3

```
# /opt/kafka/config/zookeeper.properties
dataDir=/data/zookeeper
clientPort=20182
```

In the following file: /opt/kafka/config/server.properties, change zookeeper connection details as setup in step 2.3

```
#/opt/kafka/config/server.properties

zookeeper.connect=localhost:20182
```

### 3.4 Run Kafka as a service:

Create the following file: /etc/systemd/system/kafka.service and add the following to it:

```
#/etc/systemd/system/kafka.service

[Unit]
Description=Kafka Daemon
Documentation=https://kafka.apache.org/
Requires=network.target
After=network.target

[Service]
Type=forking
WorkingDirectory=/opt/kafka
User=kafka
Group=kafka
ExecStart=/opt/kafka/bin/kafka-server-start.sh -daemon /opt/kafka/config/server.properties
ExecStop=/opt/zookeeper/bin/kafka-server-stop.sh
ExecReload=/opt/zookeeper/bin/kafka-server-stop.sh && /opt/kafka/bin/kafka-server-start.sh -daemon /opt/kafka/config/server.properties
TimeoutSec=30
Restart=on-failure

[Install]
WantedBy=default.target
```

Enable and start the service:

```
sudo systemctl daemon-reload
sudo systemctl start kafka
sudo systemctl enable kafka
```
