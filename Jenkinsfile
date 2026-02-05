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
                python3 -m venv $VENV_DIR
                . $VENV_DIR/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Verify Flask App') {
            steps {
                sh '''
                . $VENV_DIR/bin/activate
                python3 -c "import flask; print('Flask OK')"
                '''
            }
        }
    }
}
