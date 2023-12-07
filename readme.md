# LieSense Checker (Backend)

Verifying Genuine Licenses in a Digital World.

This project is a part of classwork of CMPE281 (Cloud Technologies by Prof. [Sanjay Garje](https://www.linkedin.com/in/sanjaygarje/)) at [San Jose State University](https://www.sjsu.edu), California, USA.

Team Members:
-	Saharat Saengsawang
- Akanksha Vallabh Pingle
-	Tonja Jean
-	Sanjay Sathyarapu

![Screenshot of id matching record](https://github.com/saharatss-sjsu/CMPE281-P2-BackEnd/blob/main/screenshots/Screenshot%202023-11-30%20at%204.29.58%E2%80%AFPM.jpg?raw=true)

## AWS Components

(Mandatory):
- Amazon Elastic Compute Cloud (EC2)
- Amazon Simple Storage Service (S3)
- Amazon Relational Database Service (RDS)

(Additional):
- Amazon Route 53
- Amazon Elastic Load Balancing (ELB)
- Amazon Auto Scaling Group
- Amazon Elastic Block Store (EBS)
- Amazon CloudFront
- Amazon Lambda
- Amazon Rekognition
- Amazon Virtual Private Cloud (VPC)
- Amazon Identity and Access Management (IAM)
- Amazon Certificate Manager (ACM)
 
## Installation

Software requirements:
- [mysqlclient](https://pypi.org/project/mysqlclient/)
- Python 3.11
- Python packages from [requirements.txt](https://github.com/saharatss-sjsu/CMPE281-P2-BackEnd/blob/main/setup/requirements.txt)

Or run setup script on linux environment:

```bash
#!/bin/bash

# This file is used for running in EC2 instance user data

sudo apt update
sudo apt upgrade -y

# Install necessary linux packages

sudo apt install python3-pip -y
sudo apt install python3-dev default-libmysqlclient-dev build-essential -y
sudo apt install libssl-dev -y
sudo apt install mysql-client-core-8.0 -y
sudo apt install pkg-config -y
sudo apt install unzip -y

# Set environment variable for the workspace and file download path

export PROJECT_BASEPATH=/home/ubuntu
export PROJECT_DOWNLOAD=https://license-media.saharatss.org/server
export PROJECT_FILENAME=server_backend_t0ht676t5W4qpsaJPYwR.zip
export PROJECT_SERVICE_NAME=cmpe281_backend.service

# Unxip

cd $PROJECT_BASEPATH
wget $PROJECT_DOWNLOAD/$PROJECT_FILENAME
unzip $PROJECT_FILENAME
rm $PROJECT_FILENAME

# Install python packages

cd CMPE281-P2-Backend
pip3 install -r setup/requirements.txt

# Create a script for running the server and define AWS S3 access credential

touch run.sh
echo "
export DEBUG=False
export AWS_S3_ACCESS_KEY_ID=
export AWS_S3_SECRET_ACCESS_KEY=
export AWS_S3_BUCKET_NAME=
export AWS_S3_REGION_NAME=
export AWS_S3_SIGNATURE_VERSION=s3v4
python3 $PROJECT_BASEPATH/CMPE281-P2-Backend/manage.py runserver 0:8000
" > run.sh

# Copy the systemctl service script and Start the service

cp setup/$PROJECT_SERVICE_NAME /etc/systemd/system/$PROJECT_SERVICE_NAME
sudo systemctl daemon-reload
sudo systemctl enable $PROJECT_SERVICE_NAME
sudo systemctl start $PROJECT_SERVICE_NAME

echo "Setup done!!"
```

In case of running the project locally, skip creating a script and start systemctl service, but run the command below directly within the project folder.

```bash
export DEBUG=True
export AWS_S3_ACCESS_KEY_ID=
export AWS_S3_SECRET_ACCESS_KEY=
export AWS_S3_BUCKET_NAME=
export AWS_S3_REGION_NAME=
export AWS_S3_SIGNATURE_VERSION=s3v4
python3 ../manage.py runserver 0:8000
```

Also create MqSQL connection configuration file in `{project_dir}/credentials/mysql.cnf`

```
[client]
host     = 
database = 
user     = 
password = 
default-character-set = utf8
```