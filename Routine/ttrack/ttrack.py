#!/usr/bin/python2

import argparse, time, sys, tty

# I want to update the priorities to include current stuff, but I might want to lookup the meaning and use first.
# I'll want reports on time spent doing automatic brushing routines, but also the pieces of them: nvc, awareness, task switching ...
# does it report descriptions or only categories?
# FIXED brokenness: expected details file to have header
# LEARNED routines: the routines file lists the goal, name, and hours between each tracked routine
#                   Brush Teeth matches the name, so it's been being added .. but not the whole routine tracked

# interesting categories now?  I should probably add labels to a central file.
# PUB
#   => git remote project
# LIFE
#   => NVC
#   => awareness
#   - finding nice groups
#   - sourdough bread
#   - acorns
# SAFE
#   => measuring S.E.
#   - improving noiscillate or emap
# RESPONS
#   => logistics
#   - mental maintainance? e.g. memorizing taskorg?
#   - grooming / medical stuff
# TASKORG
#   => n2 scheduling / nic box
#   - information tasks
#   - personal /possessions organization / finding items
#   - airgap phone data transfer
# BOILERPLATE
#   - verifying tasks
#   - moving between tasks
#   - accomplishment log since need feels more met?
# what else do I do with my time?
# places I might find goals: [X] brushing task, [ ] 00-organizer, [ ] present concerns list
# some tasks here are more important than others in the same category
#   let's give them attributes, like a priority; could it be a third field somewhere?
#  i guess for now not tracked ...  have to do manually.  Whenever I'm doing a category, gotta do the high priority item in that category


parser = argparse.ArgumentParser(description='Tracks time')
parser.add_argument('-d', '--details', default='time_details.csv', type=argparse.FileType('a+'), help='csv to store details in')
parser.add_argument('-p', '--priorities', default='goals_priorities.csv', type=argparse.FileType('a+'), help='csv to read priorities from')
parser.add_argument('-u', '--routines', default='routines.csv', type=argparse.FileType('a+'), help='csv to read routines from')
pgroup = parser.add_mutually_exclusive_group(required=True)
pgroup.add_argument('-w', '--work', metavar=('GOAL', 'TASK'), nargs='+', help='track work towards a goal')
pgroup.add_argument('-r', '--report', action='store_true', help='report on time usage')
pgroup.add_argument('-s', '--suggest', action='store_true', help='recommend goal to work toward')

TIME_COL = 'Time'
HOURS_COL = 'Hours'
EVENT_COL = 'Action'
GOAL_COL = 'Goal'
TASK_COL = 'Task'
RATIO_COL = 'Ratio'
EVENT_START = 'start'
EVENT_HEARTBEAT = 'heartbeat'
EVENT_STOP = 'stop'

class CSV(object):
    def __init__(self, file, format=None):
        self.file = file
        self.format = format
        self.file.seek(0)
        while True:
            self.headerpos = self.file.tell()
            line = self.file.readline()
            if not line:
                # end of file
                self.headerpos = self.file.tell()
                self.file.write(','.join(self.format))
                self.file.write('\n')
                self.file.seek(self.headerpos)
                header = self.file.readline()[0:-1].split(',')
                break
            header = line[0:-1].split(',')
            if self.format and len(line) == len(self.format):
                if self.headerpos == 0:
                    break
                if ','.join(header) == ','.join(self.format):
                    break;
            if self.format == None and len(line) > 1:
                break
        if self.format == None:
            self.format = header
    def read_all(self):
        self.file.seek(self.headerpos)
        header = self.file.readline()[0:-1].split(',')
        for line in self.file.readlines():
            row = line[0:-1].split(',')
            if len(row) == 1:
                continue
            if len(row) != len(header):
                break
            fullrow = dict()
            for i in range(len(row)):
                fullrow[self.format[i]] = row[i]
            yield fullrow
    def output(self, cols):
        if self.headerpos != 0:
            raise Exception("cannot risk clobbering other data in undedicated file")
        self.file.seek(0, 2)
        self.file.write(','.join([str(cols[x]) for x in self.format]))
        self.file.write('\n')
        self.file.flush()

class Format1(CSV):
    FORMAT1 = [TIME_COL, EVENT_COL, GOAL_COL, TASK_COL]
    def __init__(self, file):
        super(Format1, self).__init__(file, Format1.FORMAT1)

class Data():
    def __init__(self, args):
        self.csv_details = Format1(args.details)

        self.csv_prio = CSV(args.priorities, [GOAL_COL, RATIO_COL])
        self.prios = {}
        self.prios_total = 0
        
        for prio in self.csv_prio.read_all():
            goal = prio[GOAL_COL]
            prio = float(prio[RATIO_COL])
            self.prios[goal] = prio
            self.prios_total += prio

        self.csv_rout = CSV(args.routines, [GOAL_COL, TASK_COL, HOURS_COL])
        self.rout_hours = {}
        self.rout_goals = {}
        for rout in self.csv_rout.read_all():
            task = rout[TASK_COL]
            self.rout_goals[task] = rout[GOAL_COL]
            self.rout_hours[task] = float(rout[HOURS_COL])

        if args.work:
            goal = args.work.pop(0)
            goal = goal.upper()
            tasks = ' '.join(args.work)
            self.do_work(goal, tasks)
        elif args.report:
            self.do_report()
        elif args.suggest:
            self.do_suggest()

    def cumulate(self):
        self.rout_time = {}
        for task in self.rout_hours:
            self.rout_time[task] = 0
        self.total = 0
        self.cumulated = {}
        started = {}
        for goal in self.prios:
            self.cumulated[goal] = 0
        for detail in self.csv_details.read_all():
            goal = detail[GOAL_COL]
            event = detail[EVENT_COL]
            task = detail[TASK_COL]
            time = float(detail[TIME_COL])
            amt = 0
            if event == EVENT_START:
                if goal not in started:
                    started[goal] = [0, set()]
                started[goal][0] = time
                started[goal][1].add(task)
                if goal not in self.cumulated:
                    self.cumulated[goal] = 0
                if goal not in self.prios:
                    self.prios[goal] = 0
            elif event == EVENT_HEARTBEAT:
                amt = time - started[goal][0]
                started[goal][0] = time
            elif event == EVENT_STOP:
                if task in self.rout_time:
                    self.rout_time[task] = started[goal][0]
                amt = time - started[goal][0]
                started[goal][1].discard(task)
                if len(started[goal][1]) > 0:
                    started[goal][0] = time 
                else:
                    started[goal][0] = 0
            if self.prios[goal] > 0:
                self.total += amt
            self.cumulated[goal] += amt
    
    def do_report(self):
        self.cumulate()
        order = self.cumulated.keys()
        order.sort(lambda a, b: cmp(self.cumulated[b], self.cumulated[a]))
        for goal in order:
            print('%s: %.2f hours (%.2f%% vs goal of %.2f%%)' % (goal, self.cumulated[goal]/60/60, self.cumulated[goal]*100/self.total, self.prios[goal]*100/self.prios_total))

    def do_suggest(self):
        self.cumulate()
        for task in self.rout_time:
            since = time.time() - self.rout_time[task]
            since = since / 60 / 60
            if (since >= self.rout_hours[task]):
                print('%.2f hours since %s for %s' % (since, task, self.rout_goals[task]))
        needed = {}
        for goal in self.cumulated:
            #needed[goal] = self.prios[goal]*self.total/self.prios_total - self.cumulated[goal]
            desiredpct = self.prios[goal] / self.prios_total
            needed[goal] = (self.cumulated[goal] - self.total * desiredpct) / (desiredpct - 1)
        order = needed.keys()
        order.sort(lambda a, b: cmp(needed[b], needed[a]))
        for goal in order[0:4]:
            print('%s needs at least %.2f more hours' % (goal, needed[goal] / 60 / 60))

    def do_work(self, goal, tasks):
        gotchar = False
        fd = sys.stdin.fileno()
        old = tty.tcgetattr(fd)
        tty.setcbreak(fd)
        def getchar():
            global gotchar
            gotchar = False
            signal.setitimer(signal.ITIMER_REAL, 2*60*60, 0.1)
            ret = sys.stdin.read(1)
            gotchar = True
            return ret
        def alarm(a,b):
            global gotchar
            sys.stdout.write("\\x07")

        getchar = lambda: sys.stdin.read(1)
        try:
            ts = time.time()
            if goal not in self.prios:
                self.csv_prio.output({GOAL_COL: goal, RATIO_COL: 1})
            print('Beginning work on %s towards %s at %s' % (tasks, goal, time.ctime(ts)))
            self.csv_details.output({TIME_COL: ts, EVENT_COL: EVENT_START, GOAL_COL: goal, TASK_COL: tasks})
            print('Press spacebar to indicate you are still working.')
            print('Press enter to indicate you have stopped.')
            #key = 
            while True:
                key = getchar()
                if key == '\n':
                    break
                if key != ' ':
                    print('\x07!! Unrecognized keypress.  Working on %s for %s.  Press enter to stop, space to continue.' % (tasks, goal))
                    continue
                ts = time.time()
                print('Still working on %s towards %s at %s' % (tasks, goal, time.ctime(ts)))
                self.csv_details.output({TIME_COL: ts, EVENT_COL: EVENT_HEARTBEAT, GOAL_COL: goal, TASK_COL: tasks})
            ts = time.time()
            print('Stopped working on %s towards %s at %s' % (tasks, goal, time.ctime(ts)))
            self.csv_details.output({TIME_COL: ts, EVENT_COL: EVENT_STOP, GOAL_COL: goal, TASK_COL: tasks})
        finally:
            tty.tcsetattr(fd, tty.TCSAFLUSH, old)
    

data = Data(parser.parse_args())
