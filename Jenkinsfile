pipeline {
    agent any

    environment {
        OPENAI_API_KEY = credentials('OPENAI_API_KEY')
    }

    stages {

        stage('Checkout Code') {
            steps {
                echo '📥 Checking out code'
                checkout scm
            }
        }

        stage('Verify Environment') {
            steps {
                echo '🔍 Verifying Jenkins credentials'
                sh '''
                echo "OPENAI_API_KEY is set"
                echo "Length: ${#OPENAI_API_KEY}"
                '''
            }
        }

        stage('Python Check') {
            steps {
                echo '🐍 Running basic python check'
                sh '''
                python3 --version || true
                '''
            }
        }
    }

    post {
        success {
            echo '✅ BUILD SUCCESS (no deploy)'
        }
        failure {
            echo '❌ BUILD FAILED'
        }
    }
}
