pipeline {
    agent any

    environment {
        VENV_DIR = "venv"
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
                source ${VENV_DIR}/bin/activate
                python -c "import flask; print('Flask OK')"
                '''
            }
        }
    }
}
