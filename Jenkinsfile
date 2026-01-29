pipeline {
    agent any

    stages {

        stage('Pull Latest Code') {
            steps {
                sh '''
                cd /var/www/diet_planner
                git pull origin main
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                cd /var/www/diet_planner
                source venv/bin/activate
                pip install -r requirements.txt
                '''
            }
        }

        stage('Run Migrations') {
            steps { shivaktishba
                sh '''
                cd /var/www/diet_planner
                source venv/bin/activate
                python manage.py migrate
                '''
            }
        }

        stage('Collect Static') {
            steps {
                sh '''
                cd /var/www/diet_planner
                source venv/bin/activate
                python manage.py collectstatic --noinput
                '''
            }
        }

        stage('Restart Django') {
            steps {
                sh '''
                systemctl restart diet_planner
                '''
            }
        }
    }

    post {
        success {
            echo '✅ Django deployed successfully'
        }
        failure {
            echo '❌ Django deployment failed'
        }
    }
}
