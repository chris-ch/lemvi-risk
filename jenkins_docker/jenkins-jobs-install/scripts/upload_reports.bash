#!/bin/bash
while ! /usr/bin/wget http://master:8080/jnlpJars/jenkins-cli.jar --output-document=/home/cli/jenkins-cli.jar;
do
    echo sleeping;
    sleep 1;
done;

INPUT="$1"
OLDIFS=$IFS
IFS=,
[ ! -f $INPUT ] && { echo "$INPUT file not found"; exit 99; }
while read report_name report_xml secrets_tag secrets_json
do
    echo uploading "$report_xml" as \""$report_name"\";
    /bin/sed "s/%%$secrets_tag%%/$(sed -e 's/[\&/]/\\&/g' -e 's/$/\\n/' $secrets_json | tr -d '\n')/" conf/"$report_xml" > "$report_xml";
    /usr/bin/java -jar /home/cli/jenkins-cli.jar -s http://master:8080 create-job "$report_name" < "$report_xml";

done < "$INPUT"
IFS=$OLDIFS
