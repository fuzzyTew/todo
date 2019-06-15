#!/bin/bash

git pull

export TZ=America/New_York
today="$(date +"%F %Z")"
year="${today%%-*}"
if [ "x$TORIFY" == "x" ]
then
	if type -p torify >/dev/null
	then
		TORIFY=torify
	else
		TORIFY=
	fi
fi
	
csv="${year}-meds.csv"

echo ''
grep ^.., "$csv" | grep -v CONTAINS | grep -v RECOMMENDED | sort -u
echo ''
echo 'Yay!  Meds time!'
echo ''
$TORIFY git pull 2> /dev/null
echo ''
echo 'Enter meds in the form "ID Dosage".  Hit enter when you take it!'
med='go'
while true
do
	echo ''
	read med dosage notes
	time="$(date -Is)"
	if [ "x$med" == "x" ]; then break; fi
	med="$(echo "$med" | tr '[:lower:]' '[:upper:]')"
	line="$(grep ^"$med", "$csv" | head -n 1)"
	if [ "x$line" == "x" ]
	then
		echo ''
		echo "OOPS !! That med doesn't exist!  You should fix the file afterwards!"
	fi
	line="${line#*, }"
	medname="${line%,*}"
	line="${line#*, }"
	stddose="${line% *}"
	medunit="${line#* }"
	if [ "x$dosage" == "x" ]
	then
		dosage="$stddose"
	fi
	if [ "x$notes" != "x" ]; then
		notes="\"$notes\""
		echo ''
		echo "I'll note this with your med! $notes"
	fi
	echo "$time,$med,$dosage,$notes" >> "$csv"
	git add .. 
	git commit -qm "meds $med $dosage" &
	echo ''
	echo "You took $dosage $medunit of $medname at $time !  Yippee!"
done
echo ''
echo "You rock at meds!  Don't forget to lubricate your eye, brush your teeth, and treat your fissure!"
echo "Uploading ..."
echo ''
$TORIFY git push

