#!/bin/bash
while ! /usr/bin/wget http://master:8080/jnlpJars/jenkins-cli.jar --output-document=/home/cli/jenkins-cli.jar;
do
    echo sleeping;
    sleep 1;
done;
echo Ready: uploading "$2" as \""$1"\";


echo /bin/sed "s/%%lemvi_risk_secrets%%/$(sed -e 's/[\&/]/\\&/g' -e 's/$/\\n/' /run/secrets/lemvi_risk_secrets.json | tr -d '\n')/" conf/job-lemvi-margin-report.xml > "$2";
/bin/sed "s/%%lemvi_risk_secrets%%/$(sed -e 's/[\&/]/\\&/g' -e 's/$/\\n/' /run/secrets/lemvi_risk_secrets.json | tr -d '\n')/" conf/job-lemvi-margin-report.xml > "$2";
/usr/bin/java -jar /home/cli/jenkins-cli.jar -s http://master:8080 create-job "$1" < "$2";
