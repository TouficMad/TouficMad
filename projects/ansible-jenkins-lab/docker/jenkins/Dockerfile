FROM jenkins/jenkins:lts-jdk17

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv openssh-client curl \
 && apt-get clean && rm -rf /var/lib/apt/lists/* \
 && python3 -m venv /opt/ansible \
 && /opt/ansible/bin/pip install --no-cache-dir ansible-core==2.17.5 ansible-lint==24.9.2 yamllint==1.35.1
ENV PATH="/opt/ansible/bin:${PATH}"

USER jenkins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY casc.yaml /var/jenkins_home/casc.yaml
ENV CASC_JENKINS_CONFIG=/var/jenkins_home/casc.yaml \
    JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
