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
        python3 -m venv venv
        venv/bin/python -m pip install --upgrade pip
        venv/bin/pip install -r requirements.txt
        '''
    }
}

        stage('Verify Flask App') {
            steps {
                steps {
                    sh '''
                    venv/bin/python -c "import flask; print('Flask OK')"
                    '''
            }
        }
    }
}
