pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Start Backend (Local)') {
            steps {
                bat '''
                cd %WORKSPACE%
                if not exist venv (
                    python -m venv venv
                )
                call venv\\Scripts\\activate
                pip install -r requirements.txt
                python manage.py migrate
                start cmd /k python manage.py runserver 0.0.0.0:8001
                '''
            }
        }
    }

    post {
        success {
            echo '✅ Backend started locally for Flutter'
        }
    }
}
