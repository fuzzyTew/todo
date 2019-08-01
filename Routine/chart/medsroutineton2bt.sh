#!/bin/bash

# store recorded times teeth brushed in morning
cut -d , -f 1,18 ../routine/201*-routine.csv | grep ....-..-..,1 > bt-routine.csv
# store recorded times teeth brushed in evening
cut -d , -f 1,54 ../routine/201*-routine.csv | grep ....-..-..,1 >> bt-routine.csv

# store recorded times nicotine taken
grep -h N[124] ../meds/201*-meds.csv | tr T , | cut -d , -f 1,3,4,5 | grep ....-..-.., > n-meds.csv

# remove nicotine times from routine times
cut -d , -f 1 n-meds.csv | while read date
do
  grep -v "$date" bt-routine.csv > bt-routine-2.csv
  mv bt-routine-2.csv bt-routine.csv
done

# create list of toothbrush times
{
  cut -d , -f 1 bt-routine.csv
  # this used to be where aux entries were removed
  cat n-meds.csv | cut -d , -f 1
} | sort > bt.csv

# make folders for separating data
for ((yr=2018; yr < $(date +%G); yr ++))
do
	for ((wk=1; wk <=52; wk ++))
	do
		mkdir -p ${yr}-wk$(printf %02d $wk)
	done
done
curwk=$(date +%V)
curwk=${curwk#0}
for ((wk=1; wk < curwk; wk ++))
do
	mkdir -p $(date +%G)-wk$(printf %02d $wk)
done

# accumulate toothbrushes/wk
cat bt.csv | while read day
do
  wk=$(date -d "$day" +%G-wk%V)
  mkdir -p "$wk"
  if ! [ -e "$wk"/brushes ]
  then
    a=1
  else
    a=$(($(<"$wk"/brushes) + 1))
  fi
  echo $((a)) > "$wk"/brushes
done

# accumulate nmg/wk
tr , ' ' < n-meds.csv | while read day ntype nratio extra
do
  wk=$(date -d "$day" +%G-wk%V)
  npct=$(($(printf %0.2f "$nratio" | sed 's/^0//g; s/\.//g')))
  ntotalmg=$(($(echo "$ntype" | sed 's/[^0-9]//g')))
  nmicrog=$((npct * ntotalmg * 10))
  mkdir -p "$wk"
  if ! [ -e "$wk"/nct ]
  then
    nct=1
    naccum=$((nmicrog))
  else
    if [ x"$extra" = x"" ]
    then
      nct=$(($(<"$wk"/nct) + 1))
    fi
    naccum=$(($(<"$wk"/naccum) + nmicrog))
  fi
  echo $((nct)) > "$wk"/nct
  echo $((naccum)) > "$wk"/naccum
done

rm bt-routine.csv
rm bt.csv
rm n-meds.csv

# consolidate data
echo "Week" '"Recorded Brushes per Week"' '"Micrograms Nicotine per Brush"' > "Toothbrushing and Nicotine".data
lastyear=0
for dir in 20*-*/
do
  label=${dir%/}
  if [ "$label" = "$(date +%G-wk%V)" ]
  then
    continue
  fi
  yr="${label%-*}"
  startsecs=$(date -d "$yr"-01-01 +%s)
  wk="${label#*-wk}"
  wk="${wk#0}"
  if [ "$yr" == "$lastyear" ]
  then
    label="$(date -d @$((startsecs+wk*60*60*24*7-60*60*24)) +'"%b %-d"')"
  else
    lastyear="$yr"
    label="$(date -d @$((startsecs+wk*60*60*24*7-60*60*24)) +'"%Y %b %-d"')"
  fi
  if [ -e "$dir"nct ]
  then
    nct=$(($(<"$dir"nct)))
    naccum=$(($(<"$dir"naccum)))
    nbrush=$((naccum/nct))
  else
    nbrush=0
  fi
  if [ -e "$dir"brushes ]
  then
    brushes=$(($(<"$dir"brushes)))
  else
    brushes=0
  fi
  rm -rf "$dir"
  echo "$label" $((brushes)) $((nbrush))
done | tee -a "Toothbrushing and Nicotine".data

cat <<EOF | gnuplot
set terminal 'png' size 1024, 512
set output 'Toothbrushing and Nicotine.png'
set key left autotitle columnhead opaque
set xtics rotate
set y2tics
set ylabel "Brushes/Wk"
set y2label "µg Nicotine/Brush"
set grid ytics y2tics
plot 'Toothbrushing and Nicotine.data' using 0:2:xticlabels(1) with lines lw 2, \
  '' using 0:3 with lines lw 2 axes x1y2
EOF
