#include <iostream>

#include <curses.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

using namespace std;

const char* name = "ROCKET";
const int namelen = strlen(name);
const char* trail = "`!|@@@ ";
const int traillen = strlen(trail);

// - [X] TODO: fix bug with rocket scrolling off right wrongly
// - [X] TODO: stop rocket from scrolling in from left; start with landing on ground
// - [X] TODO: detect width of display
// - [X] TODO: use ncurses to make rocket go upwards
// - [X] TODO: leave cursor at head or tail of rocket
// - [ ] TODO: animate exhaust a little
// - [ ] TODO: simulate subtle error in rocket aiming systems

int main()
{
	struct winsize w;
	int launchpad;

	WINDOW* curswin = initscr();
	cbreak();
	noecho();

	launchpad = COLS / 2;

	for (int tip_position = namelen; tip_position <= LINES + namelen + traillen; ++ tip_position)
	{
		erase();
		int a;
		for (a = tip_position - namelen - traillen; a < tip_position - namelen && a < LINES; ++ a)
			mvaddch(LINES - 1 - a, launchpad, trail[traillen + a - tip_position + namelen]);
		for (; a < tip_position && a < LINES; ++ a)
			mvaddch(LINES - 1 - a, launchpad, name[tip_position - 1 - a]);
		if (tip_position > namelen)
			move(LINES - 1 - tip_position + traillen, launchpad);
		else
			move(LINES - 1, launchpad);
		refresh();
		usleep(4000000 / (tip_position - namelen + 1));
	}
	endwin();
	return 0;
}
