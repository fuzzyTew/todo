///bin/bash -c '. /usr/local/bin/thisroot.sh; /usr/local/bin/root "'"$0"'"'; exit $?

#include <iostream>
#include <fstream>
#include <vector>
#include <strstream>
#include <string>

using namespace std;

vector<pair<double, double>> data;
TGraph * gr = 0;

void dispensevolume()
{
  fstream infile("dispensertests.txt");

  string token;
  string dummy;


  double volume = 0;
  double prevolume = 0;
  double postvolume = 0;

  while (true)
  {
    infile >> token;
    if (infile.eof())
    {
      break;
    }
    cout << "read: " << token << endl;
    if (token == "comment")
    {
      getline(infile, dummy);
      cout << "comment: " << dummy << endl;
    }
    else if (token == "date" || token == "time")
    {
      getline(infile, dummy);
      cout << "date/time: " << dummy << endl;
    }
    else if (token == "set")
    {
      getline(infile, dummy);
      cout << "set: " << dummy << endl;
    }
    else if (token == "prefill")
    {
      infile >> prevolume;
    }
    else if (token == "dofill")
    {
      double lastvolume = prevolume;
      infile >> prevolume;
      cout << "dofill " << lastvolume << " - " << prevolume << " = " << (lastvolume - prevolume) << endl;
      volume += lastvolume - prevolume;
    }
    else if (token == "fill")
    {
      cout << "predicted fill to " << volume << endl;
      infile >> volume;
      cout << "actual fill to " << volume << endl;
    }
    else if (token == "start")
    {
      infile >> postvolume;
      cout << "postvolume: " << postvolume << endl;
      cout << "fill: " << volume << endl;
    }
    else
    {
      std::stringstream ss(token);
      double nextvolume;
      ss >> nextvolume;
      double amt = nextvolume - postvolume;
      data.push_back({volume, amt});
      postvolume = nextvolume;
      volume -= amt;
      cout << volume << ": " << amt << endl;
    }
  }

  std::vector<Double_t> xs, ys;
  for (auto d : data)
  {
    xs.push_back(d.first);
    ys.push_back(d.second);
  }

  gr = new TGraph(xs.size(), xs.data(), ys.data());
  gr->Draw("A*");
}
