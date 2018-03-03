FROM jenkins:2.7.1

USER root

RUN apt-get update \
  && apt-get -y install sudo \
  && apt-get install -y gcc build-essential \
  && apt-get install -y python3.4 python3.4-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3.4 python

RUN adduser jenkins sudo

ADD https://raw.githubusercontent.com/pypa/pip/701a80f451a62aadf4eeb21f371b45424821582b/contrib/get-pip.py /root/get-pip.py
RUN python3.4 /root/get-pip.py
RUN pip3 install --upgrade pip
RUN pip3 install -U "virtualenv==15.1.0"
RUN pip3 install -U "Cython==0.27.3"

RUN mkdir /var/log/jenkins
RUN mkdir /var/cache/jenkins
RUN chown -R  jenkins:jenkins /var/log/jenkins
RUN chown -R  jenkins:jenkins /var/cache/jenkins

USER jenkins
ENV JAVA_OPTS="-Xmx4096m -Djenkins.install.runSetupWizard=false"

# install plugins; the plugins.txt file can be exported from Jenkins like this:
# JENKINS_HOST=username:password@myhost.com:port
# curl -sSL "http://$JENKINS_HOST/pluginManager/api/xml?depth=1&xpath=/*/*/shortName|/*/*/version&wrapper=plugins" | perl -pe 's/.*?<shortName>([\w-]+).*?<version>([^<]+)()(<\/\w+>)+/\1 \2\n/g'|sed 's/ /:/' > jenkins-master/conf/plugins.txt

COPY conf/plugins.txt /var/jenkins_home/.
COPY conf/jenkins.plugins.shiningpanda.tools.PythonInstallation.xml /var/jenkins_home/.
RUN /usr/local/bin/plugins.sh /var/jenkins_home/plugins.txt

# "For 2.x-derived images, you may also want to" - we're 2.0 derived, so we want this
RUN echo 2.0 > /usr/share/jenkins/ref/jenkins.install.UpgradeWizard.state

# Put the log file into the log directory, which will be in the data volume
# Move the WAR out of the persisted jenkins data dir
ENV JENKINS_OPTS="--logfile=/var/log/jenkins/jenkins.log --webroot=/var/cache/jenkins/war"