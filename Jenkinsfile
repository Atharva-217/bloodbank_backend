pipeline {
    agent any

    environment {
        VENV_DIR = "venv"
        IMAGE_NAME = "bloodbank-app"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Virtual Environment') {
            steps {
                sh '''
                python3 -m venv ${VENV_DIR}
                ${VENV_DIR}/bin/python -m ensurepip --upgrade
                ${VENV_DIR}/bin/python -m pip install --upgrade pip
                ${VENV_DIR}/bin/python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Verify Dependencies') {
            steps {
                sh '''
                . ${VENV_DIR}/bin/activate
                python -c "import flask; print('Flask OK')"
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                sudo docker build -t ${IMAGE_NAME} .
                '''
            }
        }

        stage('Run Docker Container') {
            steps {
                sh '''
                sudo docker rm -f bloodbank-container || true
                sudo docker run -d -p 5000:5000 --name bloodbank-container ${IMAGE_NAME}
                '''
            }
        }

    }
}
