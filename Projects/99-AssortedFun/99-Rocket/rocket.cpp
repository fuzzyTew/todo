#include <iostream>
#include <armadillo>

#include <chrono>
#include <deque>
#include <vector>

#include <curses.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

using namespace std;
using namespace arma;
using namespace std::chrono;

// make rocket move
// make exhaust less

// rocket currently stays at ground and makes huge cloud of exhaust

// SIMULATED TINY ROCKET
// - [X] TODO: fix bug with rocket scrolling off right wrongly
// - [X] TODO: stop rocket from scrolling in from left; start with landing on ground
// - [X] TODO: detect width of display
// - [X] TODO: use ncurses to make rocket go upwards
// - [X] TODO: leave cursor at head or tail of rocket
// - [ ] TODO: add locations for guidance-force-points-and-directions
// 		this is important!!! rockets can crash !!! we need to plan how to handle it
// 			[rocket has no guidance systems atm !!!]
// - [ ] TODO: write code to detect subtle wobble and fix with guidance system
// 			-> guidance will want to use feedback due to changing conditions
// 			use accelerometers and position-tracking?
// - [ ] TODO: _simulate_ subtle inaccuracies in rocket propellant direction and aiming
// 			include wind
// - [ ] TODO: use guidance systems to turn rocket so can aim at interstellar trajectory !!!!
// - [ ] TODO: add fins
// - [ ] TODO: animate exhaust a little
// - [ ] TODO: track fuel usage and decrease mass.  have inaccuracy between guidance-mass-prediction and real mass.
//
// remember: two redundant systems for everything

// karl is asking internet 'how-to-make-roughly-a-rocket-guidance-system-in-modern-way'
// karl is sad because of 'rocket man' song
//
// omigod how-to-live-on-a-rocket
// 	more up karl's alley than simulate-a-rocket ;p
// 		NEED TO SIMULATE ROCKET BEFORE CAN LIVE ON IT

// for guidance system.  main thrust can also be modelled this way.

struct Vector3 : public vec::fixed<3>
{
public:
	Vector3()
	{
		this->zeros();
	}
	Vector3(double x, double y, double z)
	{
		(*this)[0] = x;
		(*this)[1] = y;
		(*this)[2] = z;
	}
	double x() { return (*this)[0]; }
	double y() { return (*this)[1]; }
	double z() { return (*this)[2]; }
};

struct Mat3 : public mat::fixed<3,3>
{
public:
	Mat3()
	{
		this->eye();
	}
};
// that is good advice, redundancy.
// 	this is already done.  insid ourselves inherently.  please do not overdescribe.
//
//	it is outlet for something else, overdescribing
//		errrrrrrrrrr we are tracking old issue happening inside rocket building
//			boss is looking for reason-to-inhibit
//				maybe uncomfortable around real reason
//			WHO WANTS A PLAY ROCKET?
//			YOU'RE NOT ABLE TO MAKE MY ROCKET
//
//			T_T
//
// how-to-solve-a-software-problem
// 	pattern inhibited, have reported before, looking to rebuild report
// 	- you have something happening that is not right
// 	- you have something related to causing this happen, somehow a source
// 	you want to narrow down understanding of reason for not-right-thing
// 	there are many approaches
//
//
// say my iphone was broken.  [this is very hard because it is very hard to access inside iphone
//  and apple hides innrads] what would i do?
//  			TAKE IT TO A STORE OR GO TO IFIXIT.COM ?
//  				you could take a dedicated worker to ifixit.com and save some money!
//  	OKAY.  PLEASE FIX YOUR IPHONE.
//
//  	oooh!!!!
//


struct Body
{
	Body()
	: position(),
	  orientation()
	{}
	Vector3 position;
	Mat3 orientation;
};

struct FuelInfo
{
	double mass;
	double massBurnedPerForce;
};

struct Jet : public Body
{
	Jet(Body body, FuelInfo & fuelInfo)
	: Body(body), fuelInfo(fuelInfo)
	{ }
	// exert force in Z direction by spewing hot gasses that are super hot
	FuelInfo & fuelInfo;
	// want to reference copies of fuel info so jets using same supply can drain from it
};

// options:
// make fuelInfo a shared pointer
//
// ohhh RAII.  so Rocket should manage lifetime of fuel-tracking-structure.
// make functions to produce fuel
// 	karl is not doing the right solution because the amount of typing required
// 	doesn't match boss's request for directness.

struct MovingBody : public Body
{
	Vector3 velocity;
	Vector3 spinAngle;
	double spinVelocity;
};

struct ExhaustClump : public MovingBody
{
	double radius;
};

class Rocket : public MovingBody
{
public:
	// what if main and guidance use same fuel
	// need flexible fuel tracking structure
	//  oh no !!!!
	//	karl wants a variable number of central fuel repositories
	//	1 - n, configurable
	//	he is not sure how to pass this and has forgotten his tool to do this
	Rocket(string name, string tail, double massNoFuel, FuelInfo mainFuel, bool defaultPropulsion = true)
	: name(name),
	  tail(tail),
	  bodyMass(massNoFuel)
	{
		addFuel(mainFuel);
		addJet(Body(), 0); // main engine
		if (defaultPropulsion) {
			// STUB TODO
			//throw nullptr; // FIXME NEED PROPULSION LAYOUT
			// random guidance system.
			// pick random locations on rocket body and place jets aiming random directions.
			// ensure robustness of guidance code.
		}
		// be sure to refuse to launch if impossible to keep rocket safe due to jet placement
	}

	void addTime(double seconds)
	{
		// TODO: integrate acceleraiton and velocity rather than discrete form
		position += velocity * seconds;
		velocity[2] += seconds / 10;

		if (exhaustClumps.front().radius > 10)
			exhaustClumps.pop_front();
		for (auto & clump : exhaustClumps)
		{
			clump.position += clump.velocity * seconds;
			clump.radius *= pow(4, seconds);
			if (clump.position[2] <= 0) {
				clump.position[2] = -clump.position[2];
				clump.velocity[2] = -clump.velocity[2] / 2;
			}
		}
		static double totalTime = 0;
		static double nextTime = 0;
		totalTime += seconds;
		if (totalTime >= nextTime) {
			ExhaustClump exhaust;
			exhaust.position = position;
			exhaust.velocity[2] = -0.25;
			exhaust.radius = 0.5;
			exhaustClumps.push_back(exhaust);
			nextTime = totalTime + 0.1;
		}
		// iterate jets
		// emit force to push rocket
		// produce exhaust clouds
		// move rocket
		// move exhaust clouds

		// problem: karl wants to use calculus to perform integration of acceleration
		// over time.
		// also, we haven't handle torque
		// please ignore jet positions for now
		// 	karl inhibition growing.  need close.
		// 		yes karl is making a small simulation
		// 		but he is steadily adding more and more realistic parts to it
		//
	}

	string const & getName() { return name; }
	string const & getTail() { return tail; }
	double getLength() { return name.size(); }

	vector<Jet> const & getJets() { return jets; }
	vector<FuelInfo> const & getFuels() { return fuels; }
	deque<ExhaustClump> const & getExhaustClumps() { return exhaustClumps; }

	Jet & addJet(Body jet, size_t fuel)
	{
		jets.emplace_back(jet, fuels[fuel]);
		return jets.back();
	}
	FuelInfo & addFuel(FuelInfo fuel)
	{
		fuels.emplace_back(fuel);
		return fuels.back();
	}

private:
	string name;
	string tail;
	double length;

	vector<Jet> jets;
	vector<FuelInfo> fuels;
	deque<ExhaustClump> exhaustClumps;
	
	double bodyMass;
};

class NCursesGraphics
{
public:
	NCursesGraphics()
	{
		initscr();
		cbreak();
		noecho();
	}
	~NCursesGraphics()
	{
		endwin();
	}

	void show()
	{
		refresh();
		erase();
	}

	void draw(Rocket & rocket)
	{
		auto rocketPos = rocket.position;
		auto rocketDir = rocket.orientation.col(2);
		string rocketName = rocket.getName();

		// paint exhaust via additive array
		static vector<char> kindsOfExhaust = {'@','*','`'};
		std::map<std::pair<int,int>,double> exhaustVoxels;
		for (ExhaustClump const & clump: rocket.getExhaustClumps())
		{
			for (int x = clump.position[0] - clump.radius + 0.5;
				x <= clump.position[0] + clump.radius + 0.5;
				++ x)
			{
				double r = sqrt(clump.radius * clump.radius - x*x);
				for (int y = clump.position[2] - r + 0.5;
					y <= clump.position[2] + r + 0.5;
					++ y)
				{
					// paint
					exhaustVoxels[{x,y}] += 1 / (3.14159265358979 * clump.radius * clump.radius);
				}
			}
		}
		for (auto & voxel : exhaustVoxels) {
			auto coords = voxel.first;
			auto kind = kindsOfExhaust.size() - voxel.second - 0.5;
			if (kind < 0) kind = 0;
			mvaddch(LINES - 1 - coords.second - 0.5, coords.first + 0.5 + COLS/2, kindsOfExhaust[kind]);
		}

		// paint rocket in front of exhaust
		for (int rocketBit = 0; rocketBit < rocketName.size(); ++ rocketBit)
		{
			auto bitPos = rocketPos + rocketDir * rocketBit;
			mvaddch(LINES - 1 - bitPos[2] - 0.5, bitPos[0] + 0.5 + COLS/2, rocketName[rocketName.size() - 1 - rocketBit]);
		}

		// place cursor at butt of rocket
		move(LINES - 1 - rocketPos[2] + rocketDir[2] - 0.5, rocketPos[0] - rocketDir[0] + 0.5 + COLS/2);
	}
};

//             fuel_oxidizer
double impulse_UDMH_under_N2O4 = 266;

int main()
{
	//struct winsize w;
	//int launchpad;
		// this is just a simulation
		//
	Rocket rocket("ROCKET", "`!|@@@@@@@", 131000, {2200000, impulse_UDMH_under_N2O4});

	NCursesGraphics graphics;
	Vector3 simulationMinBounds(0,-LINES,0);
	Vector3 simulationMaxBounds(COLS,LINES,LINES);

	// move code to organization system
	// rocket is like a module now

	/*
	WINDOW* curswin = initscr();
	cbreak();
	noecho();

	launchpad = COLS / 2;
	*/

	// simulate rocket wobbles a little while rising
	// wobble relates to inaccuracy in thrust
	// wobble moves center of mass, which changes how wobble progresses
	// 	rocket will [no longer] crash _IN SIMULATION_ and then we can make guidance system to stop crash
	// 	plz make guidance system _FIRST_!!!
	// 	ok
	// 	bvetter research rocket guidance systems
	// 			like usual had trouble researching
	// 			but had some luck on uspto.gov a little
	// 			basically a rocket guidance system is going ot be able to exert
	// 			a net force on the rocket relative to its existing stuff
	// 			the force will be exerted such that there is net torque too
	// 				net torque is too general
	// 				we want to know where guidance system sends force from
	// 			will parameterize it as placeable jets?
	// 				what if it funtions by adkusting flow of main propellant?
	// 				 could parameterize that too ...
	// 				this is modelable roughly as jets-at-bottom !
	// 					we are modeling arbitrary guidance systems
	// 					assuming placement of force-emitters on
	// 					static orientations on rocket body

	// draws rocket.
	// hmm.
	// also moves it.
	// convert to time loop that waits until rocket leaves simulation
	auto startTime = steady_clock::now();
	auto lastTime = startTime;
	while (true)
	{
		auto nextTime = steady_clock::now();

		rocket.addTime(duration_cast<microseconds>(nextTime - lastTime).count() / 1000000.);

		graphics.draw(rocket);
		graphics.show();

		lastTime = nextTime;

		if (rocket.position[2] >= simulationMaxBounds[2]) {
			bool done = true;
			for (auto & exhaustClump : rocket.getExhaustClumps()) {
				if (exhaustClump.position[2] - exhaustClump.radius < simulationMaxBounds[2])
				{
					done = false;
					break;
				}
			}
			if (done) break;
		}
	}
	/*
	for (int tip_position = namelen; tip_position <= LINES + namelen + traillen; ++ tip_position)
	{
		erase();
		int a;
		for (a = tip_position - namelen - traillen; a < tip_position - namelen && a < LINES; ++ a)
			mvaddch(LINES - 1 - a, launchpad, trail[traillen + a - tip_position + namelen]);
		for (; a < tip_position && a < LINES; ++ a)
			mvaddch(LINES - 1 - a, launchpad, name[tip_position - 1 - a]);
		if (tip_position > namelen)
			move(LINES - tip_position + namelen, launchpad);
		else
			move(LINES - 1, launchpad);
		refresh();
		usleep(4000000 / (tip_position - namelen + 1));
	}*/
	return 0;
}
