#include <iostream>

#include <unistd.h>
#include <string.h>

using namespace std;

const char* name = "ROCKET !!!";
const int namelen = strlen(name);
const char* trail = "~~### ";
const int traillen = strlen(trail);

// - [X] TODO: fix bug with rocket scrolling off right wrongly
// - [ ] TODO: stop rocket from scrolling in from left; start with landing on ground

int main()
{
	const int width = 100;
	for (int tip_position = namelen; tip_position <= width + namelen + traillen; ++ tip_position)
	{
		int a;
		cout << "\r";
		for (a = 0; a < tip_position - namelen - traillen && a < width; ++ a)
		{
			cout << " ";
		}
		for (; a < tip_position - namelen && a < width; ++ a)
		{
			cout << trail[traillen + a - tip_position + namelen];
		}
		for (; a < tip_position && a < width; ++ a)
		{
			cout << name[namelen + a - tip_position];
		}
		cout << flush;
		//if (tip_position - namelen == 0) {
		//	usleep(500000);
		//} else {
			usleep(1000000 / (tip_position - namelen + 1));
		//}
	}
	cout << "\n";
	return 0;
}
