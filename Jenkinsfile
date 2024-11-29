pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS = credentials('docker-repo-credential')
        DOCKER_USERNAME = "${DOCKER_CREDENTIALS_USR}"
        GITHUB_TOKEN = credentials('github-access-token')
        SSH_CREDENTIALS = credentials('flex-server-pem')
        REMOTE_USER = credentials('remote-user')
        BASTION_HOST = credentials('bastion-host')
        REMOTE_HOST = credentials('dev-news-host')
        SLACK_CHANNEL = '#backend-jenkins'
        IMAGE_NAME = "${DOCKER_USERNAME}/flex-be-news"
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    checkout scm
                }
            }
        }

        stage('Docker Build & Push') {
            steps {
                script {
                    def dockerImage = docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
                    docker.withRegistry('https://registry.hub.docker.com', 'docker-repo-credential') {
                        dockerImage.push()
                        dockerImage.push('latest')
                    }
                    slackSend(channel: SLACK_CHANNEL, message: "🐳 NEWS-SERVICE Docker image built and pushed for Build #${env.BUILD_NUMBER}.")
                }
            }
        }

        stage('Deploy to Remote Server') {
            steps {
                sshagent(credentials: ['flex-server-pem']) {
                    script {
                        sh """
                            ssh -J ${REMOTE_USER}@${BASTION_HOST} ${REMOTE_USER}@${REMOTE_HOST} '
                                set -e

                                export IMAGE_TAG=${IMAGE_TAG}

                                # Update docker-compose file with new image tag
                                sed -i "s|image: ${IMAGE_NAME}:.*|image: ${IMAGE_NAME}:${IMAGE_TAG}|" docker-compose-news.yml    

                                docker compose -f docker-compose-news.yml pull
                                docker compose -f docker-compose-news.yml up -d
                                docker compose -f docker-compose-news.yml ps
                            '
                        """
                        slackSend(channel: SLACK_CHANNEL, message: "🚀 NEWS-SERVICE Deployment SUCCEED for Build #${env.BUILD_NUMBER}.")
                    }
                }
            }

            post {
                success {
                    echo "Deployment completed successfully."
                }
                failure {
                    slackSend(channel: SLACK_CHANNEL, message: "⛔️ NEWS-SERVICE Deployment FAILED for Build #${env.BUILD_NUMBER}.")
                }
            }
        }
    }
}