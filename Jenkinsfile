#!/usr/bin/groovy

@Library(['github.com/indigo-dc/jenkins-pipeline-library@release/2.1.0']) _

def projectConfig

pipeline {
    agent any

    environment {
        dockerhub_credentials = "o3as-dockerhub-vykozlov"
    }

    stages {
        stage('SQA baseline dynamic stages') {
            environment {
                // get jenkins user id and group
                jenkins_user_id = sh (returnStdout: true, script: 'id -u').trim()
                jenkins_user_group = sh (returnStdout: true, script: 'id -g').trim()
            }
            steps {
                // execute 'backend' pipeline
                script {
                    projectConfig = pipelineConfig()
                    buildStages(projectConfig)
                }
            }
            post {
                always {
                    // BE: publish stylecheck (flake8) report:
                    recordIssues(
                        enabledForFailure: true, aggregatingResults: true,
                        tool: pyLint(pattern: 'tmp/flake8.log',
                                     reportEncoding:'UTF-8',
                                     name: 'BE - CheckStyle')
                    )

                    // BE: publish coverage report (only BE, works??):
                    cobertura(
                        coberturaReportFile: 'tmp/be-coverage.xml',
                        enableNewApi: true,
                        failUnhealthy: false, failUnstable: false, onlyStable: false
                    )

                    // BE: publish bandit report:
                    // according to https://vdwaa.nl/openstack-bandit-jenkins-integration.html
                    // XML output of bandit can be parsed as JUnit
                    recordIssues(
                        enabledForFailure: true, aggregatingResults: true,
                        tool: junitParser(pattern: 'tmp/bandit.xml',
                                           reportEncoding:'UTF-8',
                                           name: 'BE - Bandit')
                    )
                }
                cleanup {
                    cleanWs()
                }
            }
        }
    }
}
