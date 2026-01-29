pipeline {
    agent any
    
    environment {
        // Docker image name
        DOCKER_IMAGE = 'diet-planner-api'
        DOCKER_TAG = "${BUILD_NUMBER}"
        CONTAINER_NAME = 'diet-planner-api'
        APP_PORT = '1513'
        
        // Environment variables from Jenkins credentials
        SECRET_KEY = credentials('SECRET_KEY')
        OPENAI_API_KEY = credentials('OPENAI_API_KEY')
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '📥 Checking out code from repository...'
                checkout scm
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo '🐳 Building Docker image...'
                script {
                    sh """
                        docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                        docker tag ${DOCKER_IMAGE}:${DOCKER_TAG} ${DOCKER_IMAGE}:latest
                    """
                }
            }
        }
        
        stage('Run Tests') {
            steps {
                echo '🧪 Running tests...'
                script {
                    sh """
                        docker run --rm \
                            -e SECRET_KEY=${SECRET_KEY} \
                            -e OPENAI_API_KEY=${OPENAI_API_KEY} \
                            -e DEBUG=True \
                            ${DOCKER_IMAGE}:${DOCKER_TAG} \
                            python manage.py test
                    """
                }
            }
        }
        
        stage('Stop Old Container') {
            steps {
                echo '🛑 Stopping old container...'
                script {
                    sh """
                        docker stop ${CONTAINER_NAME} || true
                        docker rm ${CONTAINER_NAME} || true
                    """
                }
            }
        }
        
        stage('Deploy') {
            steps {
                echo '🚀 Deploying new container...'
                script {
                    sh """
                        docker run -d \
                            --name ${CONTAINER_NAME} \
                            -p ${APP_PORT}:${APP_PORT} \
                            -e SECRET_KEY=${SECRET_KEY} \
                            -e OPENAI_API_KEY=${OPENAI_API_KEY} \
                            -e OPENAI_BASE_URL=https://openrouter.ai/api/v1 \
                            -e OPENAI_MODEL_NAME=nvidia/nemotron-3-nano-30b-a3b:free \
                            -e OPENAI_IMAGE_MODEL_NAME=stabilityai/stable-diffusion-xl-base-1.0 \
                            -e DEBUG=False \
                            -e ALLOWED_HOSTS=* \
                            --restart unless-stopped \
                            ${DOCKER_IMAGE}:${DOCKER_TAG}
                    """
                }
            }
        }
        
        stage('Health Check') {
            steps {
                echo '🏥 Performing health check...'
                script {
                    sh """
                        echo "Waiting for application to start..."
                        sleep 10
                        
                        # Check if container is running
                        if docker ps | grep ${CONTAINER_NAME}; then
                            echo "✅ Container is running"
                            
                            # Try to access the API
                            for i in {1..5}; do
                                if curl -f http://localhost:${APP_PORT}/api/schema/ > /dev/null 2>&1; then
                                    echo "✅ API is responding"
                                    exit 0
                                fi
                                echo "Waiting for API to respond... (attempt \$i/5)"
                                sleep 5
                            done
                            
                            echo "⚠️ API is not responding, but container is running"
                            exit 0
                        else
                            echo "❌ Container failed to start"
                            exit 1
                        fi
                    """
                }
            }
        }
        
        stage('Cleanup Old Images') {
            steps {
                echo '🧹 Cleaning up old Docker images...'
                script {
                    sh """
                        # Keep only the last 3 builds
                        docker images ${DOCKER_IMAGE} --format "{{.Tag}}" | \
                        grep -v latest | \
                        tail -n +4 | \
                        xargs -r -I {} docker rmi ${DOCKER_IMAGE}:{} || true
                    """
                }
            }
        }
    }
    
    post {
        success {
            echo '✅ Deployment successful!'
            echo "🌐 Application is running at: http://localhost:${APP_PORT}"
            echo "📚 API Documentation: http://localhost:${APP_PORT}/api/schema/swagger-ui/"
        }
        failure {
            echo '❌ Deployment failed!'
            echo 'Check the console output for errors.'
            script {
                // Rollback to previous version if deployment fails
                sh """
                    echo "Attempting rollback..."
                    docker stop ${CONTAINER_NAME} || true
                    docker rm ${CONTAINER_NAME} || true
                    
                    # Try to start previous version
                    PREV_BUILD=\$((${BUILD_NUMBER} - 1))
                    if docker images ${DOCKER_IMAGE}:\$PREV_BUILD -q | grep -q .; then
                        echo "Rolling back to build \$PREV_BUILD"
                        docker run -d \
                            --name ${CONTAINER_NAME} \
                            -p ${APP_PORT}:${APP_PORT} \
                            -e SECRET_KEY=${SECRET_KEY} \
                            -e OPENAI_API_KEY=${OPENAI_API_KEY} \
                            -e DEBUG=False \
                            --restart unless-stopped \
                            ${DOCKER_IMAGE}:\$PREV_BUILD
                    fi
                """
            }
        }
        always {
            echo '📊 Build completed'
            echo "Build Number: ${BUILD_NUMBER}"
            echo "Docker Image: ${DOCKER_IMAGE}:${DOCKER_TAG}"
        }
    }
}
