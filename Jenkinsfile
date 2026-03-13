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

          sstage('Setup Python Virtual Environment') {
            steps {
                sh '''
                python3 -m venv venv
                venv/bin/python -m ensurepip --upgrade
                venv/bin/python -m pip install --upgrade pip
                venv/bin/python -m pip install -r requirements.txt
                '''
            }
        }
            steps {
                sh '''
                venv/bin/python -c "import flask; print('Flask OK')"
                '''
            }
        }

    }
}
