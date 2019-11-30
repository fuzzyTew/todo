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
    #if [ x"$extra" = x"" ]
    #then
      nct=$(($(<"$wk"/nct) + 1))
    #fi
    naccum=$(($(<"$wk"/naccum) + nmicrog))
  fi
  echo $((nct)) > "$wk"/nct
  echo $((naccum)) > "$wk"/naccum
  #echo "$(date -d "$day") naccum = $naccum nct = $nct nbrush = $((naccum/nct))"
done

rm bt-routine.csv
rm bt.csv
rm n-meds.csv

maxnicval=0
maxnicidx=0
maxbshval=0
maxbshidx=0
nstartidx=0

# consolidate data
echo "Week" '"Recorded Brushes per Week"' '"Nicotine per Brush"' '"Nicotine per Day"' > "Toothbrushing and Nicotine".data
lastyear=0
lastmo=
rowidx=0
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
  datesecs=$((startsecs+wk*60*60*24*7-60*60*24))
  mo="$(date -d @$((datesecs)) +'"%b"')"
  if [ "$yr" == "$lastyear" ]
  then
    if [ "$mo" == "$lastmo" ]
    then
      label='""'
    else
      lastmo="$mo"
      label="$(date -d @$((datesecs)) +'"%b %-d"')"
    fi
  else
    lastyear="$yr"
    lastmo="$mo"
    label="$(date -d @$((datesecs)) +'"%Y %b %-d"')"
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
  echo "$label" $((brushes)) $((nbrush)) $((naccum)) | tee -a "Toothbrushing and Nicotine".data
  if ((nstartidx == 0)) && ((nbrush > 0))
  then
    nstartidx=$((rowidx))
  fi
  if ((nbrush > maxnicval))
  then
    maxnicval=$((nbrush))
    maxnicidx=$((rowidx))
  fi
  if ((brushes > maxbshval))
  then
    maxbshval=$((brushes))
    maxbshidx=$((rowidx))
  fi
  rowidx=$((rowidx + 1))
done
rowidx=$((rowidx - 1))
echo "[$((nstartidx)):$((rowidx))]"

cat <<EOF | gnuplot
set terminal 'png' fontscale 2 size 1350, 975
set output 'Toothbrushing and Nicotine.png'
set key left autotitle columnhead opaque
set xtics rotate
set y2tics
set ylabel "Brushes/Wk"
set yrange [0:$((maxbshval))]
set y2label "Micrograms Nicotine/Brush"                                                        
set y2range [0:$((maxnicval))]
set grid ytics y2tics
b(x) = a*x + b
fit b(x) 'Toothbrushing and Nicotine.data' using 0:2 via a,b
b(x) = a*x*x*x*x*x + b*x*x*x*x + c*x*x*x + d*x*x + e*x + f
fit b(x) 'Toothbrushing and Nicotine.data' using 0:2 via a,b,c,d,e,f
n(x) = z*x + y
fit n(x) 'Toothbrushing and Nicotine.data' using 0:3 via z,y
n(x) = w*x*x*x*x*x + v*x*x*x*x + u*x*x*x + t*x*x + s*x + r
fit n(x) 'Toothbrushing and Nicotine.data' using 0:3 via w,v,u,t,s,r
plot 'Toothbrushing and Nicotine.data' using 0:2:xticlabels(1) with lines lw 5 lc rgbcolor "black", \
  '' using 0:3 with lines lw 5 lc rgbcolor "grey50" axes x1y2, \
  b(x) lw 6 lc rgbcolor "black", \
  n(x) lw 6 lc rgbcolor "grey50" axes x1y2
EOF
cat <<EOF | gnuplot
set terminal 'png' fontscale 2 size 1350, 975
set output 'Nicotine over Time.png'
set key left autotitle columnhead opaque
set xtics rotate
set y2tics
set ylabel "Micrograms Nicotine/Brush"
set y2label "Micrograms Nicotine/Day"
set grid ytics y2tics
b1(x) = a*x + b
b2(x) = c*x + d
fit [$((nstartidx)):$((maxbshidx))] b1(x) 'Toothbrushing and Nicotine.data' using 0:2 via a,b
fit [$((maxbshidx)):$((rowidx))] b2(x) 'Toothbrushing and Nicotine.data' using 0:2 via c,d
b(x) = a*x + b
fit [$((nstartidx)):$((rowidx))] b(x) 'Toothbrushing and Nicotine.data' using 0:2 via a,b
n(x) = a*x*x*x*x*x + b*x*x*x*x + c*x*x*x + d*x*x + e*x + f
fit [$((nstartidx)):$((rowidx))] n(x) 'Toothbrushing and Nicotine.data' using 0:3 via a,b,c,d,e,f
n2(x) = w*x*x*x*x*x + v*x*x*x*x + u*x*x*x + t*x*x + s*x + r
fit [$((nstartidx)):$((rowidx))] n2(x) 'Toothbrushing and Nicotine.data' using 0:4 via w,v,u,t,s,r
plot [$((nstartidx)):$((rowidx))] 'Toothbrushing and Nicotine.data' using 0:3:xticlabels(1) with lines lw 5 lc rgbcolor "black", \
  '' using 0:4 with lines lw 5 lc rgbcolor "grey50" axes x1y2, \
  n(x) lw 6 lc rgbcolor "black", \
  n2(x) lw 6 lc rgbcolor "grey50" axes x1y2
EOF
