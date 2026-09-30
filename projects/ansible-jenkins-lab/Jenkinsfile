pipeline {
    agent any

    options {
        ansiColor('xterm')
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    parameters {
        booleanParam(name: 'AUTO_APPROVE', defaultValue: false, description: 'Skip the manual approval before deploying')
        string(name: 'LIMIT', defaultValue: 'all', description: 'Hosts or groups to target, e.g. web1')
    }

    environment {
        ANSIBLE_FORCE_COLOR = 'true'
        // ssh refuses a private key readable by others, so work on a private copy
        SSH_KEY = "${WORKSPACE}@tmp/id_ed25519"
    }

    stages {
        stage('Prepare') {
            steps {
                sh '''
                    install -D -m 600 /keys/id_ed25519 "$SSH_KEY"
                    ansible --version
                '''
            }
        }

        stage('Lint') {
            parallel {
                stage('yamllint') {
                    steps { sh 'yamllint .' }
                }
                stage('ansible-lint') {
                    steps { sh 'ansible-lint' }
                }
            }
        }

        stage('Syntax check') {
            steps {
                sh 'ansible-playbook site.yml --syntax-check'
            }
        }

        stage('Connectivity') {
            steps {
                sh 'ansible all -m ansible.builtin.ping --limit "$LIMIT" -e ansible_ssh_private_key_file="$SSH_KEY"'
            }
        }

        stage('Dry run') {
            steps {
                sh 'ansible-playbook site.yml --check --diff --limit "$LIMIT" -e ansible_ssh_private_key_file="$SSH_KEY"'
            }
        }

        stage('Approve') {
            when { expression { !params.AUTO_APPROVE } }
            steps {
                timeout(time: 15, unit: 'MINUTES') {
                    input message: 'Dry run looks good. Deploy to the servers?', ok: 'Deploy'
                }
            }
        }

        stage('Deploy') {
            steps {
                sh 'ansible-playbook site.yml --diff --limit "$LIMIT" -e ansible_ssh_private_key_file="$SSH_KEY"'
            }
        }
    }

    post {
        always {
            sh 'rm -f "$SSH_KEY"'
        }
        success {
            echo 'Deployment finished. Open http://localhost:8081 and http://localhost:8082'
        }
        failure {
            echo 'Pipeline failed. Check the stage logs above.'
        }
    }
}
