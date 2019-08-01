class TrackUI
{
public:
};

class TrackLog
{
public:
};

class TrackState
{
friend class TrackCore;
public:
	std::string name();
protected:
	virtual void coreEnters() = 0;
	virtual void coreLeaves() = 0;
};

class TrackCore
{
public:
	TrackCore(TrackUI & ui, TrackLog & log)
	: curState(nullptr)
	{ }

	void run()
	{
		if (curState == 0)
		{
			throw std::logic_error("No state set.");
		}
		// probably wait for input on the ui
		// and offer status output

		// I guess each state will manage something or other.
		// Downtime can have a status that's displayed, and a category it records events of

		// Then working task, similar, but can have substates depending on task worked.
		// timed task could be form of working task: needs to set timer

	}

	void setState(TrackState * state)
	{
		if (curStats != nullptr)
			curState->coreLeaves();
		curState = state;
		curState->coreEnters();
	}

	TrackState & getState()
	{
		return *curState;
	}

private:
	TrackState * curState;
};

class MostBasicUI : public TrackUI
{
public:
	
};

// WHOOPS: ttrack already meets the immediate goal spawning this.  just need to adopt ttrack and integrate w brushing
class 

int main()
{
	return 0;
}
