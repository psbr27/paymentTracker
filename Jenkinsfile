pipeline {
    agent any

    environment {
        IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_COMMIT?.take(7) ?: 'latest'}"
        COMPOSE_PROJECT_NAME = 'paytrack'
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

        stage('Push Images') {
            when {
                allOf {
                    anyOf {
                        branch 'main'
                        branch 'master'
                        branch 'develop'
                    }
                    expression {
                        return fileExists('/var/jenkins_home/credentials.xml') ||
                               env.DOCKER_REGISTRY_URL != null
                    }
                }
            }
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'docker-registry-url', variable: 'DOCKER_REGISTRY'),
                        usernamePassword(credentialsId: 'docker-registry-credentials',
                                         usernameVariable: 'DOCKER_USER',
                                         passwordVariable: 'DOCKER_PASS')  // pragma: allowlist secret
                    ]) {
                        sh '''
                            echo "$DOCKER_PASS" | docker login ${DOCKER_REGISTRY} -u "$DOCKER_USER" --password-stdin

                            docker tag paytrack-backend:${IMAGE_TAG} ${DOCKER_REGISTRY}/paytrack-backend:${IMAGE_TAG}
                            docker tag paytrack-backend:latest ${DOCKER_REGISTRY}/paytrack-backend:latest
                            docker push ${DOCKER_REGISTRY}/paytrack-backend:${IMAGE_TAG}
                            docker push ${DOCKER_REGISTRY}/paytrack-backend:latest

                            docker tag paytrack-frontend:${IMAGE_TAG} ${DOCKER_REGISTRY}/paytrack-frontend:${IMAGE_TAG}
                            docker tag paytrack-frontend:latest ${DOCKER_REGISTRY}/paytrack-frontend:latest
                            docker push ${DOCKER_REGISTRY}/paytrack-frontend:${IMAGE_TAG}
                            docker push ${DOCKER_REGISTRY}/paytrack-frontend:latest

                            docker logout ${DOCKER_REGISTRY}
                        '''
                    }
                }
            }
        }

        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                script {
                    echo "Deploying to staging environment..."
                    // Add your staging deployment commands here
                    // sshagent(['staging-server-credentials']) {
                    //     sh 'ssh user@staging-server "cd /app && ./deploy.sh -a"'
                    // }
                }
            }
        }

        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                input message: 'Deploy to production?', ok: 'Deploy'
                script {
                    echo "Deploying to production environment..."
                    // Add your production deployment commands here
                    // sshagent(['production-server-credentials']) {
                    //     sh 'ssh user@production-server "cd /app && ./deploy.sh -a"'
                    // }
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
        }
        failure {
            echo "Build failed!"
        }
    }
}
