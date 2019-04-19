pipeline {
    agent any
    options {
        disableConcurrentBuilds()
    }

    stages {

        stage("Build Images") {
            // Builds images that are required for tests
            steps {
                sh "docker build -t riptide_integration_test riptide/tests/docker_image"
                sh "docker build -t riptide_docker_tox test_assets/riptide-docker-tox"
            }
        }

        stage("Tests") {
            steps {
                sh '''#!/bin/bash
                    docker run \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -e USER=$(id -u) \
                        -e DOCKER_GROUP=$(cut -d: -f3 < <(getent group docker)) \
                        -v "/tmp:/tmp" \
                        -v "$(pwd):$(pwd)" \
                        --network host \
                        --workdir $(pwd) \
                        riptide_docker_tox \
                        tox
                '''
            }
        }

        stage('Build') {
            steps {
                // Setup virtual env
                sh "rm -rf .venv || true"
                sh "virtualenv .venv"
                sh ". .venv/bin/activate"

                // Run build
                sh "rm -rf dist build || true"
                sh "pip3 install -r requirements.txt"
                sh "python3 setup.py bdist_wheel"
            }
            post {
                always {
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'dist/*whl', fingerprint: true
                }
            }
        }

        stage('Deploy to PyPI') {
            when {
                branch "release"
            }
            environment {
                TWINE    = credentials('parakoopa-twine-username-password')
            }
            steps {
                sh 'twine -u "$TWINE_USR" -p "$TWINE_PSW" upload dist/*'
            }
        }

    }

}