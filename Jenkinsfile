    pipeline {
        agent any

        environment {
            NODE_ENV = 'production'

            // OpenAI credentials - add these in Jenkins: Manage Jenkins → Credentials → (your domain) → Add
            // Required credential IDs: OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL_NAME, OPENAI_IMAGE_MODEL_NAME
            OPENAI_API_KEY         = credentials('OPENAI_API_KEY')
            OPENAI_BASE_URL        = credentials('OPENAI_BASE_URL')
            OPENAI_MODEL_NAME      = credentials('OPENAI_MODEL_NAME')
            OPENAI_IMAGE_MODEL_NAME = credentials('OPENAI_IMAGE_MODEL_NAME')
        }

        stages {

            stage('Allow Only main & dev') {
                steps {
                    script {
                        // Manual runs or non-multibranch jobs don't set BRANCH_NAME; default to main
                        if (env.BRANCH_NAME == null || env.BRANCH_NAME == '') {
                            env.BRANCH_NAME = 'main'
                        }
                        if (env.BRANCH_NAME != 'main' && env.BRANCH_NAME != 'dev') {
                            error("Not allowed to build branch: ${env.BRANCH_NAME}")
                        }
                    }
                }
            }

            stage('Set Port and Container Name') {
                steps {
                    script {
                        env.HOST_PORT = '6969'
                        env.CONTAINER_PORT = '8080'
                        if (env.BRANCH_NAME == 'main') {
                            env.CONTAINER_NAME = 'diet-planner-api-main'
                        } else {
                            env.CONTAINER_NAME = 'diet-planner-api-dev'
                        }
                        echo "Using HOST_PORT: ${env.HOST_PORT}, CONTAINER_NAME: ${env.CONTAINER_NAME}"
                    }
                }
            }

            stage('Build Docker Image') {
                steps {
                    sh '''
                        docker build -f Dockerfile.production -t diet-planner-api:${BRANCH_NAME} .
                        echo "✅ Docker image built successfully"
                    '''
                }
            }

            stage('Deploy') {
                steps {
                    sh '''
                        # Forcefully stop and remove any existing container with this name
                        docker stop "$CONTAINER_NAME" 2>/dev/null || true
                        docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
                        
                        # Also handle docker compose cleanup if it was used previously
                        docker compose down 2>/dev/null || true
                        
                        # Wait a moment to ensure cleanup is complete
                        sleep 2
                        
                        # Verify container is removed
                        if docker ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
                            echo "Warning: Container still exists, forcing removal..."
                            docker rm -f "$CONTAINER_NAME" || true
                        fi

                        docker run -d \
                            --name "$CONTAINER_NAME" \
                            -p "$HOST_PORT:$CONTAINER_PORT" \
                            -e DEBUG=False \
                            -e OPENAI_API_KEY="$OPENAI_API_KEY" \
                            -e OPENAI_BASE_URL="$OPENAI_BASE_URL" \
                            -e OPENAI_MODEL_NAME="$OPENAI_MODEL_NAME" \
                            -e OPENAI_IMAGE_MODEL_NAME="$OPENAI_IMAGE_MODEL_NAME" \
                            -e DATABASE_PATH="/app/db_data/db.sqlite3" \
                            -v diet_planner_db:/app/db_data \
                            --restart always \
                            diet-planner-api:"$BRANCH_NAME"
                    '''
                }
            }
        }

        post {
            always {
                echo "Pipeline execution completed for branch: ${env.BRANCH_NAME}"
            }
            success {
                echo "✅ BUILD SUCCESS - Application deployed on port ${env.HOST_PORT}"
            }
            failure {
                echo "Pipeline failed. Check logs for details."
            }
        }
    }
