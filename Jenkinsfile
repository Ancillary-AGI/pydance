pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        DOCKER_REGISTRY = 'pydance'
        IMAGE_NAME = 'framework'
        SONAR_PROJECT_KEY = 'pydance-framework'
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 60, unit: 'MINUTES')
        timestamps()
    }
    
    triggers {
        pollSCM('H/5 * * * *')
        cron('H 2 * * *') // Nightly builds
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.GIT_COMMIT_SHORT = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    env.BUILD_VERSION = "${env.BUILD_NUMBER}-${env.GIT_COMMIT_SHORT}"
                }
            }
        }
        
        stage('Setup Environment') {
            parallel {
                stage('Python Setup') {
                    steps {
                        sh '''
                            python3 -m venv venv
                            . venv/bin/activate
                            pip install --upgrade pip
                            pip install -r requirements.txt
                            pip install pytest pytest-cov bandit safety black isort flake8 mypy
                        '''
                    }
                }
                
                stage('Node.js Setup') {
                    steps {
                        dir('pydance-client') {
                            sh '''
                                npm ci
                                npm audit --audit-level moderate
                            '''
                        }
                    }
                }
            }
        }
        
        stage('Code Quality') {
            parallel {
                stage('Linting') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            black --check src/ tests/ || exit 1
                            isort --check-only src/ tests/ || exit 1
                            flake8 src/ tests/ --output-file=flake8-report.txt || true
                            mypy src/ --junit-xml=mypy-report.xml || true
                        '''
                    }
                    post {
                        always {
                            publishTestResults testResultsPattern: 'mypy-report.xml'
                            archiveArtifacts artifacts: 'flake8-report.txt', allowEmptyArchive: true
                        }
                    }
                }
                
                stage('Security Scan') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            bandit -r src/ -f json -o bandit-report.json || true
                            safety check --json --output safety-report.json || true
                        '''
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: '*-report.json', allowEmptyArchive: true
                        }
                    }
                }
            }
        }
        
        stage('Testing') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            pytest tests/unit/ --cov=src/pydance --cov-report=xml --cov-report=html --junit-xml=unit-test-results.xml
                        '''
                    }
                    post {
                        always {
                            publishTestResults testResultsPattern: 'unit-test-results.xml'
                            publishCoverage adapters: [coberturaAdapter('coverage.xml')], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
                        }
                    }
                }
                
                stage('Integration Tests') {
                    steps {
                        script {
                            docker.image('postgres:15').withRun('-e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=pydance_test') { postgres ->
                                docker.image('redis:7').withRun() { redis ->
                                    sh '''
                                        . venv/bin/activate
                                        export DATABASE_URL="postgresql://postgres:postgres@${POSTGRES_PORT_5432_TCP_ADDR}:${POSTGRES_PORT_5432_TCP_PORT}/pydance_test"
                                        export REDIS_URL="redis://${REDIS_PORT_6379_TCP_ADDR}:${REDIS_PORT_6379_TCP_PORT}/0"
                                        pytest tests/integration/ --junit-xml=integration-test-results.xml
                                    '''
                                }
                            }
                        }
                    }
                    post {
                        always {
                            publishTestResults testResultsPattern: 'integration-test-results.xml'
                        }
                    }
                }
                
                stage('Performance Tests') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            python scripts/test_framework.py
                            pytest tests/performance/ --junit-xml=performance-test-results.xml
                        '''
                    }
                    post {
                        always {
                            publishTestResults testResultsPattern: 'performance-test-results.xml'
                        }
                    }
                }
                
                stage('Client Tests') {
                    steps {
                        dir('pydance-client') {
                            sh '''
                                npm test -- --reporter=xunit --outputFile=../client-test-results.xml
                                npm run build
                                npm run test:integration
                            '''
                        }
                    }
                    post {
                        always {
                            publishTestResults testResultsPattern: 'client-test-results.xml'
                        }
                    }
                }
            }
        }
        
        stage('SonarQube Analysis') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                    changeRequest()
                }
            }
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                        . venv/bin/activate
                        sonar-scanner \
                            -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                            -Dsonar.sources=src/ \
                            -Dsonar.tests=tests/ \
                            -Dsonar.python.coverage.reportPaths=coverage.xml \
                            -Dsonar.python.xunit.reportPath=*-test-results.xml
                    '''
                }
            }
        }
        
        stage('Build Package') {
            steps {
                sh '''
                    . venv/bin/activate
                    python -m build
                    twine check dist/*
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'dist/*', fingerprint: true
                }
            }
        }
        
        stage('Docker Build') {
            steps {
                script {
                    def image = docker.build("${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_VERSION}")
                    
                    if (env.BRANCH_NAME == 'main' || env.BRANCH_NAME == 'develop') {
                        docker.withRegistry('https://registry.hub.docker.com', 'dockerhub-credentials') {
                            image.push()
                            image.push('latest')
                        }
                    }
                }
            }
        }
        
        stage('Deploy') {
            parallel {
                stage('Deploy to Staging') {
                    when {
                        branch 'develop'
                    }
                    steps {
                        script {
                            // Deploy to staging environment
                            sh '''
                                echo "Deploying version ${BUILD_VERSION} to staging"
                                # Add staging deployment commands
                                kubectl set image deployment/pydance-staging pydance=${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_VERSION} --namespace=staging
                                kubectl rollout status deployment/pydance-staging --namespace=staging
                            '''
                        }
                    }
                }
                
                stage('Deploy to Production') {
                    when {
                        tag pattern: "v\\d+\\.\\d+\\.\\d+", comparator: "REGEXP"
                    }
                    steps {
                        input message: 'Deploy to production?', ok: 'Deploy'
                        script {
                            // Deploy to production environment
                            sh '''
                                echo "Deploying version ${BUILD_VERSION} to production"
                                # Add production deployment commands
                                kubectl set image deployment/pydance-prod pydance=${DOCKER_REGISTRY}/${IMAGE_NAME}:${BUILD_VERSION} --namespace=production
                                kubectl rollout status deployment/pydance-prod --namespace=production
                            '''
                        }
                    }
                }
            }
        }
        
        stage('Publish') {
            when {
                tag pattern: "v\\d+\\.\\d+\\.\\d+", comparator: "REGEXP"
            }
            steps {
                withCredentials([string(credentialsId: 'pypi-token', variable: 'PYPI_TOKEN')]) {
                    sh '''
                        . venv/bin/activate
                        twine upload dist/* --username __token__ --password ${PYPI_TOKEN}
                    '''
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        
        success {
            emailext (
                subject: "✅ Build Success: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Build ${env.BUILD_NUMBER} completed successfully.\n\nBuild URL: ${env.BUILD_URL}",
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'dev-team@pydance.com'}"
            )
        }
        
        failure {
            emailext (
                subject: "❌ Build Failed: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Build ${env.BUILD_NUMBER} failed.\n\nBuild URL: ${env.BUILD_URL}\n\nPlease check the logs and fix the issues.",
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'dev-team@pydance.com'}"
            )
        }
        
        unstable {
            emailext (
                subject: "⚠️ Build Unstable: ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: "Build ${env.BUILD_NUMBER} is unstable.\n\nBuild URL: ${env.BUILD_URL}\n\nSome tests may have failed.",
                to: "${env.CHANGE_AUTHOR_EMAIL ?: 'dev-team@pydance.com'}"
            )
        }
    }
}