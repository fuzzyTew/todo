#!/bin/bash

quiz_startsecs=$(($(date +%s)))
file="00-Organizer.txt"
needed=7
pat='^I*[0-9]\.* '
tmp=$(mktemp)
echo 0 0  > "$tmp"
while
	read correct total < "$tmp"
	(( correct < needed ))
do
	grep "$pat"  "$file" | sort -R | head -n 1 |
	{
		read prefix descr
		echo "$file '$prefix': what's the rest?"
		read rest < /dev/tty
		read correct total < "$tmp"
		total=$((total + 1))
		if [ "$rest" = "$descr" ]
		then
			echo "Exactly!  Well done!"
			correct=$((correct + 1))
		else
			echo "Not quite right ... it was:"
			echo "$descr"
			echo "enter to continue"
			read < /dev/tty
			clear
		fi
		echo "$correct" "$total" > "$tmp"
	}
done
quiz_endsecs=$(($(date +%s)))
quiz_duration=$((quiz_endsecs - quiz_startsecs))
read correct total < "$tmp"
quiz_pct=$(( correct * 100 / total))
echo "Quiz PCT=$(( correct * 100 / total))"
printf "Total Duration=%d:%02d\n" $((quiz_duration/60)) $((quiz_duration%60))
rm "$tmp"
