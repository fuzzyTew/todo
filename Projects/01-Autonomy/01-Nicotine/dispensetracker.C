///bin/bash -c '. /usr/bin/thisroot.sh; exec /usr/bin/root -l "'"$0"'"'

#include <TFile.h>

class SoluteEvent
{
public:
	SoluteEvent(double totalVolume = 0, double totalSolute = 0, char const * event = 0)
	: totalVolume(totalVolume), totalSolute(totalSolute), event(event)
	{}

	double totalVolume;
	double totalSolute;
	char const * event;

	void Print()
	{
		std::cout << "Event: " << event << std::endl;
		std::cout << "Volume: " << totalVolume << " mL" << std::endl;
		std::cout << "Solute: " << totalSolute << " mg" << std::endl;
	}

	ClassDef(SoluteEvent, 2)
};
ClassImp(SoluteEvent)

class DispenseTracker
{
public:
	DispenseTracker(std::string fname, double dispenseConstant = 0.597035, double dispenseFillProportion = 0.00164173)
	: _file(fname.c_str(), "UPDATE"),
	  _dispenseConstant(dispenseConstant),
	  _dispenseFillProportion(dispenseFillProportion)
	{
		if (!_file.IsOpen())
		{
			throw std::runtime_error("Failed to open " + fname);
		}
		read();
		if (_lastEvent == 0)
		{
			static SoluteEvent se;
			_lastEvent = &se;
		}
	}

	double volume_ml()
	{
		return _lastEvent->totalVolume;
	}

	double solute_mg()
	{
		return _lastEvent->totalSolute;
	}

	void setTotal(double ml, double mg)
	{
		write(ml, mg, "setTotal");
		_lastEvent->Print();
	}

	void add(double ml, double mg)
	{
		write(ml + volume_ml(), mg + solute_mg(), "addVolume");
		_lastEvent->Print();
	}

	SoluteEvent dispenseGuess(int count = 1)
	{
		double totalExpectedVolume = 0;
		double totalExpectedSolute = 0;
		for (int i = 0; i < count; ++ i) {
			double expectedVolume = _dispenseConstant + _dispenseFillProportion * volume_ml();
			double expectedSolute = solute_mg() * expectedVolume / volume_ml();
			write(volume_ml() - expectedVolume, solute_mg() - expectedSolute, "dispense");
			totalExpectedVolume += expectedVolume;
			totalExpectedSolute += expectedSolute;
		}
		SoluteEvent ret {totalExpectedVolume, totalExpectedSolute, "dispense"};
		ret.Print();
		return ret;
	}

	void write()
	{
		_file.Write();
		_file.Flush();
		_file.ReOpen("READ");
		_file.ReOpen("UPDATE");
	}


	~DispenseTracker()
	{
		write();
		delete _lastEvent;
	}

private:
	void read()
	{
		_file.GetObject("solute", _lastEvent);
		auto keys = _file.GetListOfKeys();
		TKeyXML* bestKey = 0;
		for (TObject* obj : *keys)
		{
			auto key = static_cast<TKeyXML*>(obj);
			if (!bestKey)
			{
				bestKey = key;
			}
			if (key->GetDatime() >= bestKey->GetDatime())
			{
				bestKey = key;
			}
		}
		_lastEvent = bestKey->ReadObject<SoluteEvent>();
	}

	void write(double ml, double mg, std::string event)
	{
		_lastEvent->totalVolume = ml;
		_lastEvent->totalSolute = mg;
		_lastEvent->event = event.c_str();
		_file.WriteObject(_lastEvent, "solute");
		read();
	}

	TXMLFile _file;
	SoluteEvent * _lastEvent;
	double _dispenseConstant;
	double _dispenseFillProportion;
};

#include <iostream>

void dispensetracker()
{
	std::cout << "Usage: " << std::endl;
	std::cout << "] DispenseTracker dt(\"solute.xml\")" << std::endl;
	std::cout << "] dt.setTotal(ml, mg)" << std::endl;
	std::cout << "] dt.add(ml, mg)" << std::endl;
	std::cout << "] dt.dispenseGuess()" << std::endl;
	std::cout << "] dt.write()" << std::endl;
	std::cout << "] .q" << std::endl;
}
