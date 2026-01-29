pipeline {
    agent any

    environment {
        OPENAI_API_KEY = credentials('OPENAI_API_KEY')
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Start Backend (Local)') {
            steps {
                sh '''
                cd $WORKSPACE

                echo "Using OPENAI_API_KEY (length: ${#OPENAI_API_KEY})"

                if [ ! -d "venv" ]; then
                    python3 -m venv venv
                fi

                source venv/bin/activate
                pip install -r requirements.txt

                python manage.py migrate

                echo "Backend setup completed (not running server)"
                '''
            }
        }
    }

    post {
        success {
            echo '✅ BUILD SUCCESS on Linux Jenkins'
        }
        failure {
            echo '❌ BUILD FAILED'
        }
    }
}
