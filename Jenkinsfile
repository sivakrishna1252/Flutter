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

        stage('Local Backend Setup (Server Jenkins)') {
            steps {
                sh '''
                cd $WORKSPACE

                echo "Using OPENAI_API_KEY (length: ${#OPENAI_API_KEY})"

                if [ ! -d venv ]; then
                    python3 -m venv venv
                fi

                . venv/bin/activate
                pip install -r requirements.txt
                python manage.py migrate

                echo "Backend setup completed"
                '''
            }
        }
    }

    post {
        success {
            echo '✅ BUILD SUCCESS'
        }
        failure {
            echo '❌ BUILD FAILED'
        }
    }
}
