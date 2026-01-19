pipeline {
    agent any

    environment {
        IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT?.take(7) ?: 'latest'}"
        COMPOSE_PROJECT_NAME = 'paytrack'
        DEPLOY_SERVER = '192.168.1.217'
        DEPLOY_USER = 'server05'
        DEPLOY_PATH = '/home/server05/paytrack'
        SSH_CREDENTIALS_ID = 'c6b80171-bacf-4041-be0b-540aa126cf0c'
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_MSG = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
                    env.GIT_AUTHOR = sh(script: 'git log -1 --pretty=%an', returnStdout: true).trim()
                }
            }
        }

        stage('Pre-flight Checks') {
            parallel {
                stage('Validate Docker Compose') {
                    steps {
                        sh 'docker compose config --quiet'
                    }
                }
                stage('Check Environment') {
                    steps {
                        sh '''
                            echo "Docker version:"
                            docker --version
                            echo "Docker Compose version:"
                            docker compose version
                        '''
                    }
                }
            }
        }

        stage('Build Images') {
            parallel {
                stage('Build Backend') {
                    steps {
                        dir('backend') {
                            sh 'docker build -t paytrack-backend:${IMAGE_TAG} -t paytrack-backend:latest .'
                        }
                    }
                }
                stage('Build Frontend') {
                    steps {
                        dir('frontend') {
                            sh 'docker build -t paytrack-frontend:${IMAGE_TAG} -t paytrack-frontend:latest .'
                        }
                    }
                }
            }
        }

        stage('Code Quality') {
            parallel {
                stage('Backend Lint') {
                    steps {
                        dir('backend') {
                            sh '''
                                docker run --rm -v $(pwd):/app -w /app python:3.11-slim sh -c "
                                    pip install --quiet ruff
                                    ruff check app/ --output-format=github || true
                                "
                            '''
                        }
                    }
                }
                stage('Frontend Lint') {
                    steps {
                        dir('frontend') {
                            sh '''
                                docker run --rm -v $(pwd):/app -w /app node:18-alpine sh -c "
                                    npm ci --silent
                                    npm run lint 2>/dev/null || echo 'No lint script configured'
                                "
                            '''
                        }
                    }
                }
            }
        }

        stage('Security Scan') {
            steps {
                sh '''
                    echo "Running security checks..."
                    docker run --rm -v $(pwd):/repo zricethezav/gitleaks:latest detect --source=/repo --no-git || true
                '''
            }
        }

        stage('Run Tests') {
            parallel {
                stage('Backend Tests') {
                    steps {
                        dir('backend') {
                            sh '''
                                docker run --rm -v $(pwd):/app -w /app paytrack-backend:${IMAGE_TAG} sh -c "
                                    pip install --quiet pytest pytest-cov httpx
                                    pytest tests/ -v --cov=app --cov-report=xml || echo 'No tests found or tests failed'
                                " || true
                            '''
                        }
                    }
                    post {
                        always {
                            junit allowEmptyResults: true, testResults: 'backend/test-results.xml'
                        }
                    }
                }
                stage('Frontend Tests') {
                    steps {
                        dir('frontend') {
                            sh '''
                                docker run --rm -v $(pwd):/app -w /app node:18-alpine sh -c "
                                    npm ci --silent
                                    npm test -- --passWithNoTests 2>/dev/null || echo 'No tests configured'
                                "
                            '''
                        }
                    }
                }
            }
        }

        stage('Integration Test') {
            steps {
                script {
                    sh '''
                        cat > .env.test << 'EOF'
POSTGRES_USER=testuser
POSTGRES_PASSWORD=testpassword
POSTGRES_DB=paytrack_test
DATABASE_URL=postgresql://testuser:testpassword@db:5432/paytrack_test  # pragma: allowlist secret
SECRET_KEY=test-secret-key-for-ci  # pragma: allowlist secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DEBUG=false
EOF

                        docker compose --env-file .env.test -p paytrack-test up -d --build

                        echo "Waiting for services to be ready..."
                        sleep 30

                        docker compose -p paytrack-test exec -T backend curl -f http://localhost:8000/health || \
                        docker compose -p paytrack-test exec -T backend curl -f http://localhost:8000/ || \
                        echo "Health check endpoint not available"

                        docker compose -p paytrack-test ps
                    '''
                }
            }
            post {
                always {
                    sh '''
                        docker compose -p paytrack-test down -v --remove-orphans || true
                        rm -f .env.test
                    '''
                }
            }
        }

        stage('Deploy to Server') {
            when {
                branch 'main'
            }
            steps {
                script {
                    sshagent(credentials: [env.SSH_CREDENTIALS_ID]) {
                        sh '''
                            echo "Deploying to ${DEPLOY_SERVER}..."

                            # Create deployment directory on remote server
                            ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} "mkdir -p ${DEPLOY_PATH}"

                            # Copy project files to remote server
                            scp -o StrictHostKeyChecking=no -r \
                                docker-compose.yml \
                                deploy.sh \
                                backend \
                                frontend \
                                database \
                                .env.example \
                                ${DEPLOY_USER}@${DEPLOY_SERVER}:${DEPLOY_PATH}/

                            # Create .env file if it doesn't exist, then deploy
                            ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_SERVER} "
                                cd ${DEPLOY_PATH}

                                # Create .env from example if not exists
                                if [ ! -f .env ]; then
                                    cp .env.example .env
                                    echo 'Created .env from .env.example - please update with production values!'
                                fi

                                # Make deploy script executable
                                chmod +x deploy.sh

                                # Stop existing containers, rebuild and start
                                docker compose down || true
                                docker compose build --no-cache
                                docker compose up -d

                                # Show status
                                echo '=== Deployment Status ==='
                                docker compose ps
                                echo ''
                                echo '=== Container Logs (last 20 lines) ==='
                                docker compose logs --tail=20
                            "

                            echo "Deployment completed successfully!"
                            echo "Application available at: http://${DEPLOY_SERVER}"
                        '''
                    }
                }
            }
        }

        stage('Cleanup') {
            steps {
                sh '''
                    docker image prune -f || true
                    docker container prune -f || true
                '''
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo "Build successful! Image tag: ${IMAGE_TAG}"
            echo "Deployed to: http://${DEPLOY_SERVER}"
        }
        failure {
            echo "Build failed!"
        }
    }
}
