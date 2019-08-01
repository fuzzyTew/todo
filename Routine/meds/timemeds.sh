#!/bin/bash

routine="$1"

export TZ=America/New_York
today="$(date +"%F %Z")"
year="${today%%-*}"

ttrackdir="../ttrack"
ttrackfile="${ttrackdir}/time_details.csv"

git pull

echo "$(date +%s),start,RESPONS,Meds" >> "$ttrackfile"

skipmatch=0
if [ "Antibiotic" == "$routine" ]
then
	skipmatch=-1
fi

csv="${year}-meds.csv"

{
	sleep 0.4
	echo "I'll fill in values for your $routine meds!" > /dev/tty
	echo '' > /dev/tty
	cat "$csv" | {
		while read line
		do
			if [ "$line" == "$routine Meds" ]
			then
				break
			fi
		done
		while read line
		do
			if [ "x$line" == "x" ]
			then
				break
			fi
			medid="${line%%,*}"
			line="${line#*, }"
			medname="${line%%,*}"
			line="${line#*, }"
			fulldosage="${line%%,*}"
			dosage="${fulldosage%% *}"
			notes="${line#*, }"
			if (( $(shuf -i 0-1 --random-source=/dev/random | head -n 1) == skipmatch )) 
			then
				echo "I recommend SKIPPING the next med if you want !" > /dev/tty
			fi
			if [ "$notes" == "$line" ]
			then
				notes=''
				echo "Have $fulldosage of $medname, then hit enter !" > /dev/tty
				echo "Type 'skip' if you skip this med." > /dev/tty
				read skip </dev/tty
				if [ "x$skip" = "x" ]
				then
					echo "$medid" "$dosage"
				elif [ "x$skip" = "xskip" ]
				then
					echo "SKIPPED!" > /dev/tty
				else
					echo "What does '$skip' mean? fix the record !!!" > /dev/tty
					echo "$medid" "$dosage" "skipped? '$skip' entered"
				fi
			else
				echo "Have $fulldosage ($notes) of $medname, then hit enter !" >/dev/tty
				echo "Type 'skip' if you skip this med." > /dev/tty
				read skip </dev/tty
				if [ "x$skip" == "x" ]
				then
					echo "$medid" "$dosage" "$notes"
					echo "$(date +%s),heartbeat,RESPONS,Meds" >> "$ttrackfile"
				elif [ "x$skip" == "skip" ]
				then
					echo "SKIPPED!" > /dev/tty
				else
					echo "What does '$skip' mean? fix the record !!!" > /dev/tty
					echo "$medid" "$dosage" "$notes ... skipped? '$skip' entered"
				fi
			fi
			sleep 0.3
		done
	}
	echo "$(date +%s),stop,RESPONS,Meds" >> "$ttrackfile"
} | "$(dirname "$0")/havemed.sh" | grep -v 'ID Dosage'
