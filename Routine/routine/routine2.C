///bin/bash -c '/usr/bin/env root -l "'"$0"'"'; exit $?
/* .C file for routine stuff
 *
 * NOW Thu Morn: SCRIPT GOAL judge history.  reorder routine. THEN run routine!  YES c++ root
 *
 */

// TODO NOW: adjust reordering metric to order almost completely by value (but rank lowest if learned degree >= 1)

// issue list:
// - [X] routine script is not passed the name of the script
// - [X] brushing is broken up into multiple steps that will be shuffled by script
//      options:
//        - change brushing to one step
//          -> ended up doing this one
//        - provide for multiple steps to task <=
// - [X] crash after items are removed from routine
//        -> I had removed the reinforcement event
// - [X] default goals are filled with 1% rather than 100%
// - [X] primary task is repeatedly announced as new
//  -> i added some logic changes, but the real issue here appears to be that the primary task is not retaining the strat_paoe keyval
// - [X] /1w is not simplified away to /w
// - [/] show current status towards goal to verify functionality

// NOTES FOR STRATEGIES:
//   independent dose:
//   	order after brushing event such that goals are met.  reorder prior to & during brushing event such that behavior is learned.
//   dependent dose or dosing:
//   	move learned habits farther from dose, but keep dose dependent on them, to retain but dissociate

// focus. work this script. memory loss.
// keep focus. handle environ. because keep work.
// yes yes =) work script c++, root, shell script! YES YES
//
// refill nic LATER due to this task importance.
// maybe when spit? remember: schedule, refill nicotine to keep nic strength high

// arguments? => methods on Routine, or global shortcuts
// -> script has main function calls script macro function
// type commands! function calls!
// make global object? maybe!
// at end, for crash. (something is wrong with making global object, so put it at the end in case causes problem.  solve later, much later)

// consolide notes

// RESIST distraction when swishing

// CSV: all in routinedata.csv, one big file
// Code, Routine, Start Time, Stop Time, Description
// separator = ", " and it tails the line
//
// process csv using c++? or system(3)?
//  c++ -> need to look up how to split on token
//  could use string loop
//  ok
//  c++ ->  need to look up how to read line
//  use root to infer
//  routinedata.csv
//  
//
// system(3)
// int system(const char *command)
// really uses execl("/bin/sh", "sh", "-c", command, (char *) 0)
// buts wraps using a synchronous fork()
// RETURNS: exist status, also nonzero for error

#include <fstream>
#include <iostream>
#include <map>
#include <stdlib.h>
#include <string>
#include <utility>
#include <vector>
#include <RooDouble.h>
#include <TMap.h>
#include <TObjString.h>

template <typename ...chars>
std::string delimAdvance(char const * & pos, chars const & ...delims)
{
  char dlms[] = {0,(char)delims...};
  char const * start = pos;
  bool contDefault = true;
  for (auto check : dlms)
  {
    if (check < 0) contDefault = false;
  }
  bool cont;
  -- pos;
  do
  {
    cont = contDefault;
    ++ pos;
    for (auto const & check : dlms)
    {
      if (check >= 0)
      {
        if (*pos == check) goto done;
      }
      else // check < 0, break if not present
      {
        if (*pos == -check) cont = true;
      }
    }
  } while(cont);

done:
  return {start,pos};
}

class RoutineHistoryEntry
{
public:
  RoutineHistoryEntry() {}
  RoutineHistoryEntry(std::string code, std::string routine, time_t startTime, time_t stopTime, std::string description, std::string comment)
  : code(code),
    routine(routine),
    startTime(startTime),
    stopTime(stopTime),
    description(description),
    comment(comment)
  {}

  static RoutineHistoryEntry fromCSVLine(std::string line)
  {
    char const * csvLine = line.c_str();
    char const * chunk = csvLine;

    if (!*chunk) throw std::logic_error("csv line is empty");

    // code
    std::string code = delimAdvance(chunk, ',');
    ++ chunk;
    delimAdvance(chunk, -' ');

    if (!*chunk) throw std::runtime_error("missing line in history csv");

    // routine
    std::string routine = delimAdvance(chunk, ',');
    ++ chunk;
    delimAdvance(chunk, -' ');

    // startTime
    struct tm _tm;
    time_t startTime;
    if (*chunk != ',')
    {
      chunk = strptime(chunk, line, &_tm);
      startTime = mktime(&_tm);
    }
    else
    {
      startTime = 0;
    }
    
    if (*chunk != ',') throw std::runtime_error(std::string("unexpected data after startTime: ") + chunk);
    ++ chunk;
    delimAdvance(chunk, -' ');

    // stopTime
    chunk = strptime(chunk, line, &_tm);
    time_t stopTime = mktime(&_tm);

    if (*chunk != ',') throw std::runtime_error(std::string("unexpected data after stopTime: ") + chunk);
    ++ chunk;
    delimAdvance(chunk, -' ');

    // description
    std::string description = delimAdvance(chunk, ',');
    ++ chunk;

    // comment
    std::string comment = delimAdvance(chunk, ',');
    ++ chunk;

    // obj
    return {code, routine, startTime, stopTime, description, comment};
  }

  std::string code;
  std::string routine;
  // time_t is UTC
  time_t startTime;
  time_t stopTime;
  std::string description;
  std::string comment;

  private:
  static char const * strptime(char const * str, std::string & line, struct tm * _tm)
  {
    char const * ret = ::strptime(str, "%FT%T%z", _tm);
    if (*ret == ':')
    {
      if (ret[1] >= '0' && ret[1] <= '9' && ret[2] >= '0' && ret[2] <= '9')
      {
        size_t offset = str - line.c_str();
        line.erase(ret - line.c_str(), 1);
        ret = ::strptime(line.c_str() + offset, "%FT%T%z", _tm);
      }
    }
    return ret;
  }
};

// blargh i didn't generalize it enough
// the iterator returned by begin()/end() is not consistent
// to change, do a thing ...
//  -> want consistent begin()/end()
//  -> iterator interface not the best for derived class
//  -> would like virtual-func-based inheritance
//  -> need provide virtual func for base class provide iteration
//  base class just needs next func really
//  

class RoutineHistorySource
{
public:
  virtual void rewind() = 0;
  virtual RoutineHistoryEntry next() = 0;

  RoutineHistorySource & begin()
  {
    ended = false;
    rewind();
    val = next();
    return *this;
  }

  RoutineHistorySource & end()
  {
    // TODO: make iterator subclass
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wnonnull"
#pragma clang diagnostic ignored "-Wnull-dereference"
    return *static_cast<RoutineHistorySource *>(0);
#pragma clang diagnostic pop
  }

  bool operator!=(RoutineHistorySource &other)
  {
    return (&other != &end() || !ended) && (&other != this);
  }

  void operator++()
  {
    try
    {
      val = next();
    }
    catch (std::range_error const & e)
    {
      ended = true;
    }
  }

  RoutineHistoryEntry const & operator*() const
  {
    return val;
  }

  virtual ~RoutineHistorySource() = default;
private:
  bool ended;
  RoutineHistoryEntry val;
};

class RoutineHistoryCSVSource : public RoutineHistorySource
{
public:
  RoutineHistoryCSVSource(std::string fname = "routinedata.csv")
  : file(fname)
  {
    rewind();
  }

  virtual void rewind()
  {
    char linebuf[1024];
    file.clear();
    file.seekg(0);
    // read header line and discard
    file.getline(linebuf, sizeof(linebuf));
  }

  virtual RoutineHistoryEntry next()
  {
    char linebuf[4096];
    file.getline((char*)linebuf, sizeof(linebuf));
    if (file.fail() || file.eof())
    {
      file.clear(); // reset state flags
      file.get(); // try to read a byte
      if (file.fail())
      {
        throw std::range_error("EOF");
      }
      else
      {
        throw std::runtime_error("History CSV line longer than allocated buffer");
      }
    }
    //std::cerr << linebuf << std::endl;
    if (*linebuf == 0)
      return this->next();
    return RoutineHistoryEntry::fromCSVLine({linebuf});
  }

private:
  std::ifstream file;
};

class RoutineEntry
{
public:
  enum GoalType {
    COUNT_PERCENT,
    COUNT_PERTIME,
    TIME_PERTIME,
  };

  // let's provide a key/value store using TMap.
  // The keys can be TObjStrings.  The TString contained can be converted to a double with Atof()
  // Can check if a TString if a number with IsFloat()
  // Can actually read to a delim with member func TString::ReadToDelim(istream, delim).
  RoutineEntry(std::string code, std::string description, double value = 0.0, std::string reason = "", double goal = 1.0, GoalType goalType = COUNT_PERCENT, double goalDenominator = 1.0)
  : code(code),
    description(description),
    value(value),
    reason(reason),
    goalNumerator(goal),
    goalType(goalType),
    goalDenominator(goalDenominator),
    keyvals(new TMap())
  { }

  RoutineEntry(RoutineEntry &&) = default;
  RoutineEntry(RoutineEntry const & other)
  : code(other.code),
    description(other.description),
    value(other.value),
    reason(other.reason),
    goalNumerator(other.goalNumerator),
    goalType(other.goalType),
    goalDenominator(other.goalDenominator),
    keyvals(new TMap())
  {
    TMapIter iter(&*other.keyvals);
    for (TObjString * key; (key = (TObjString*)iter.Next());)
    {
      keyvals->Add(key, other.keyvals->GetValue(key));
    }
  }

  void toTextStream(std::ostream & txts)
  {
    txts << code << "\t" << description << "{VALUE: " << value << "; REASON: " << reason << "; GOAL: ";
    static std::vector<std::pair<char,double>> const timechars{
      {'s',1},
      {'m',60},
      {'h',60*60},
      {'d',60*60*24},
      {'w',60*60*24*7},
      {'y',60*60*24*365.25}
    };
    size_t timeidx;
    double denom;
    // - [X] TODO: STORE THE NUMERATOR AND DENOMINATOR WHEN READ, DON'T REGENERATE THEM
    // - [X] write goal using numerator and denominator
    // - [X] update other classes to use numerator and denominator (getGoal method)
    switch (goalType)
    {
    case COUNT_PERCENT:
      // goal is pct
      txts << goalNumerator * 100 / goalDenominator << "%";
      break;
    case COUNT_PERTIME:
      // goal is number / sec, stored is number / timeunit
      // - [X] write using numerator and denominator
      for (timeidx = 1; fmod(goalDenominator, timechars[timeidx].second) == 0; ++ timeidx);
      -- timeidx;
      txts << goalNumerator << "/";
      denom = goalDenominator / timechars[timeidx].second;
      if (denom != 1) txts << denom;
      txts << timechars[timeidx].first;
      break;
    case TIME_PERTIME:
      // - [X] write using numerator and denominator
      for (timeidx = 1; fmod(goalNumerator, timechars[timeidx].second) == 0; ++ timeidx);
      -- timeidx;
      txts << (goalNumerator / timechars[timeidx].second) << timechars[timeidx].first << "/";
      for (timeidx = 1; fmod(goalDenominator, timechars[timeidx].second) == 0; ++ timeidx);
      -- timeidx;
      denom = goalDenominator / timechars[timeidx].second;
      if (denom != 1) txts << denom;
      txts << timechars[timeidx].first;
      break;
    }
    // - [X] write all other fields -> '; KEY: value'
    TMapIter iter(&*keyvals);
    for (TObjString * key; (key = (TObjString*)iter.Next());)
    {
      std::string keySS = key->GetName();
      txts << "; " << keySS << ": " << getString(keySS);
    }
    // - [X] close with '}'
    txts << "}" << std::endl;
  }

  static RoutineEntry fromTextStream(std::istream & txts)
  {
    // code
    std::string code;
    txts >> code;

    if (txts.eof())
    {
      throw std::range_error("EOF");
    }

    // description
    char line[1024];
    txts.getline(line, sizeof(line));
    char const * chunk = line;
    delimAdvance(chunk, -' ', -'\t');
    std::string description = delimAdvance(chunk, '{');

    RoutineEntry ret{code, description};
  
    // key-values
    if (*chunk == '{')
    {
      ++ chunk;
      while (*chunk != '}' && *chunk)
      {
        std::string keySS = delimAdvance(chunk, ':', '}');
        delimAdvance(++chunk, -' ');
        std::string valueSS = delimAdvance(chunk, ';', '}');
        delimAdvance(++chunk,  -' ');

        ret.set(keySS, valueSS);
      }
    }
    
    // obj
    return ret;
  }

  template <typename Processor>
  static void processTextfile(Processor processor, std::string filename)
  {
    std::ifstream file(filename);

    try
    {
      while (true)
      {
        processor(fromTextStream(file));
      }
    }
    catch (std::range_error e)
    { }
  }

  std::string code;
  std::string routine;
  std::string description;

  double value;
  std::string reason;
  double goalNumerator;
  double goalDenominator;
  GoalType goalType;
  std::unique_ptr<TMap> keyvals;

  double getGoal() const
  {
    return goalNumerator / goalDenominator;
  }

  std::string getString(std::string name)
  {
    try
    {
      return getVal(name)->GetName();
    }
    catch(std::runtime_error)
    {
      return {};
    }
  }

  double getDouble(std::string name)
  {
    return getVal(name)->String().Atof();
  }

  void set(std::string name, std::string value)
  {
    if (name == "GOAL")
    {
      if (value.back() == '%')
      {
        // percent
        goalNumerator = std::stod(value);
        goalDenominator = 100;
        goalType = COUNT_PERCENT;
      }
      else
      {
        char const * chunk = value.c_str();
        std::string numerator = delimAdvance(chunk, '/');
        std::string denominator = ++chunk;
        if (denominator.size() == 0)
        {
          throw std::runtime_error("no denominator in routine entry");
        }
        static std::map<char,double> const timechars{
          {'s',1},
          {'m',60},
          {'h',60*60},
          {'d',60*60*24},
          {'w',60*60*24*7},
          {'y',60*60*24*365.25}
        };
        if (!timechars.count(denominator.back()))
        {
          throw std::runtime_error("denominator has no time unit");
        }
        goalDenominator = timechars.find(denominator.back())->second * (denominator.size() > 1 ? std::stod(denominator) : 1);
        if (timechars.count(numerator.back()))
        {
          goalType = TIME_PERTIME;
          goalNumerator = timechars.find(numerator.back())->second * (numerator.size() > 1 ? std::stod(numerator) : 1);
        }
        else
        {
          goalType = COUNT_PERTIME;
          goalNumerator = std::stod(numerator);
        }
      }
    }
    else if (name == "VALUE")
    {
      std::size_t ct;
      this->value = std::stod(value, &ct);
      if (ct != value.size()) throw std::runtime_error("trailing stuff after value " + value);
    }
    else if (name == "REASON")
    {
      reason = value;
    }
    else
    {
      auto key = new TObjString(name.c_str());
      keyvals->DeleteEntry(key);
      keyvals->Add(key, new TObjString(value.c_str()));
    }
  }

private:
  TObjString * getVal(std::string const & name)
  {
    TObjString * val = static_cast<TObjString*>(keyvals->GetValue(name.c_str()));
    if (!val) throw std::runtime_error("not found: " + name);
    return val;
  }
};

void swap(RoutineEntry &a, RoutineEntry &b)
{
  using std::swap;
  swap(a.code, b.code);
  swap(a.routine, b.routine);
  swap(a.description, b.description);
  swap(a.value, b.value);
  swap(a.reason, b.reason);
  swap(a.goalNumerator, b.goalNumerator);
  swap(a.goalDenominator, b.goalDenominator);
  swap(a.goalType, b.goalType);
  swap(a.keyvals, b.keyvals);
}

class RoutineList
{
public:
  // ordered list of routines
  // each has a code and a description
  RoutineList(std::string filename = "")
  : filename(filename)
  {}

  static RoutineList fromTextfile(std::string filename)
  {
    RoutineList ret(filename);

    RoutineEntry::processTextfile([&ret](RoutineEntry && entry){ ret.entries.emplace_back(entry); }, filename);

    return ret;
  }

  void toTextfile()
  {
    std::ofstream file(filename);

    for (auto & entry : entries)
    {
      entry.toTextStream(file);
    }
  }

  std::vector<RoutineEntry> entries;
  std::string filename;
};

RoutineHistoryCSVSource defaultRoutineHistory{};

class RoutineMetric
{
public:
  virtual double measure(RoutineEntry const & routine, RoutineHistorySource & history) = 0;
  virtual ~RoutineMetric() = default;
};

// these might make good TObject's so they can have reflectable parameters, such as duration to consider
class RoutineMetricValue : public RoutineMetric
{
public:
  virtual double measure(RoutineEntry const & routine, RoutineHistorySource & history)
  {
    return routine.value;
  }
};

class RoutineMetricDevelopment : public RoutineMetric
{
public:
  RoutineMetricDevelopment(double days)
  : duration(days * 24 * 60 * 60 + 0.5)
  { }

  virtual double measure(RoutineEntry const & routine, RoutineHistorySource & history)
  {
    time_t cutoff = time(0) - duration;
    double total = 0;
    double success = 0;
    time_t accumulation = 0;
    history.rewind();
    while (true)
    {
      try
      {
        RoutineHistoryEntry entry = history.next();
        if (entry.code != routine.code) continue;
        if (entry.startTime < cutoff)
        {
          if (entry.stopTime >  cutoff) accumulation += entry.stopTime - cutoff;
          continue;
        }

        ++ total;
        accumulation += entry.stopTime - entry.startTime;
        if (entry.comment != "UNFINISHED") ++ success;
      }
      catch (std::range_error const & e)
      {
        break;
      }
    }

    auto goal = routine.goalNumerator / routine.goalDenominator;
    switch (routine.goalType)
    {
      case RoutineEntry::COUNT_PERCENT:
        return success / total / goal;
      case RoutineEntry::COUNT_PERTIME:
        return success / duration / goal;
      case RoutineEntry::TIME_PERTIME:
        return accumulation / static_cast<double>(duration) / goal;
      default:
	throw std::invalid_argument("bad goal type");
    }
  }

private:
  time_t duration;
};

// Notes on judgement:
//  - we'll want to track the state of different learning things, can store this in routine file for now a keyvals
//  - each learning thing may be
//    - more or less responsive to learning
//    - happen on its own more or less easily
//    - affect the learning process more or less
//  ^-- these can be measured
//    - presently worked on to a different degree (idea of one major learning goal, held for a while)
//          - auxiliary idea of there being different "ways" in which different goals may be learned
//       includes idea of primary goal, etc
//       perhaps: once primary hits upper threshhold, different primary until drops to lower threshhold
//            could use halfway point between goal and max as upper threshhold, consider there are metrics
//              to track for ranking and judging learning strategies

// how will I mark metrics wrt in what way they might be judged?
// maybe custom, passed to judgement constructor.
// this would make the judgement the same as a metric.
class RoutineMetricJudgement : public RoutineMetric
{
  // todo? retrieve metrics used for judgement
};

// judgement ... uses two metrics, value and development.
//
// planned strategy is to pick one valuable routine
// and focus on it
// judgements needed: which routine to pick? when is routine done?
// which routine to pick: this is a learning-importance metric
// can just call importance
template <typename Callable, typename... Metrics>
class RoutineMetricJudgementLambda : public RoutineMetricJudgement
{
public:
  RoutineMetricJudgementLambda(Callable callable, Metrics & ... metrics)
  : callable(callable),
    metrics(metrics...)
  { }

  virtual double measure(RoutineEntry const & routine, RoutineHistorySource & history)
  {
    return doMeasure(routine, history, std::make_index_sequence<sizeof...(Metrics)>());
  }

  template <std::size_t... idxs>
  double doMeasure(RoutineEntry const & routine, RoutineHistorySource & history, std::index_sequence<idxs...>)
  {
    return callable(std::get<idxs>(metrics).measure(routine, history)...);
  }

  Callable callable;
  std::tuple<Metrics &...> metrics;
};

template <typename Callable, typename... Metrics>
RoutineMetricJudgementLambda<Callable,Metrics...> gRoutineMetricJudgementLambda(Callable callable, Metrics &... metrics)
{
  return {callable, metrics...};
}

// now we'll need a strategy for ordering the routines to practice
// and in general a strategy for building routines
//
// strategy for building routines -> ordering routine file
// strategy for ordering routine file -> pick one routine to work on, and place it before the brushing
// event.  once it reaches threshhold, pick different one.
//   substrategy of handling non-primary goals: perhaps order them after the event?
//   secondary goal would go after brushing event
//   other goals?
//   sounds valuable to hold spae for secondary goal
//   onec goals are learne, let's place them after the secondary until they need relearning
//   order of secondaries?
//   let's order by development, so well-developed goals go at the end.
//
// - overall strategy regarding ordering routine file: Routine{} class
// - ordering strategy:
//    - parameter brushing event to place behind primary
//    - metric importance to select new primary goal
//    - data storage: primary and secondary goals
//    - metric development to select tertiary goal ordering

class OrderingStrategy
{
public:
  virtual void reorder(RoutineList & list, RoutineHistorySource & history) = 0;
  virtual ~OrderingStrategy() = default;
};

class OrderingStrategyPrimaryAheadOfEvent : public OrderingStrategy
{
public:
  static constexpr char const * STATE_KEY_PRIMARY = "strat_paoe";

  OrderingStrategyPrimaryAheadOfEvent(std::string reinforceCode, RoutineMetric & selectionMetric, RoutineMetric & learnedMetric, double learnedCutoff, RoutineMetric & tertiaryOrderingMetric)
  : reinforceCode(reinforceCode),
    selectionMetric(selectionMetric),
    learnedMetric(learnedMetric),
    learnedCutoff(learnedCutoff),
    tertiaryOrderingMetric(tertiaryOrderingMetric)
  {}

  void reorder(RoutineList & list, RoutineHistorySource & history)
  {
    // we'll need to store custom data in the list, regarding which routine is primary and which secondary
    // --> the entries can hold custom data using .getString(ss), .getDouble(ss), and .set(name, value_ss)

    // RoutineMetric has double .measure(RoutineEntry &, RoutineHistory &)
    RoutineEntry * primary = 0;
    RoutineEntry * nextPrimary = 0;
    RoutineEntry * reinforce = 0;
    double bestSelectionMetric = -std::numeric_limits<double>::infinity();
    auto lastEntryOrderingMetric = std::numeric_limits<double>::infinity();

    for (auto entryIt = list.entries.begin(), lastIt = entryIt; entryIt != list.entries.end(); lastIt = entryIt, ++ entryIt)
    {
      auto & entry = *entryIt;
      if (entry.code == reinforceCode)
      {
        reinforce = &entry;
        continue;
      }
      if (entry.getString(STATE_KEY_PRIMARY) == "primary")
      {
        auto learnedPct = learnedMetric.measure(entry, history) * 100 / learnedCutoff;
        if (learnedPct >= 100)
        {
          std::cout << "CONGRATULATIONS !! Successful learned to " << learnedPct << "%: " << entry.code << ": " << entry.description << std::endl;
          entry.set(STATE_KEY_PRIMARY, "learned");
        }
        else
        {
          std::cout << "Currently prioritizing (" << learnedPct << "%) " << entry.code << ": " << entry.description << std::endl;
          primary = &entry;
          continue;
        }
      }
      auto entrySelectionMetric = selectionMetric.measure(entry, history);
      if (entrySelectionMetric > bestSelectionMetric)
      {
        bestSelectionMetric = entrySelectionMetric;
        if (primary == 0)
        {
          if (learnedMetric.measure(entry, history) < learnedCutoff)
          {
            nextPrimary = &entry;
          }
        }
      }
      auto entryOrderingMetric = tertiaryOrderingMetric.measure(entry, history);
      if (entryOrderingMetric > lastEntryOrderingMetric && &*lastIt != reinforce)
      {
        // swap this with last
        std::cout << "Increasing priority of " << entryIt->code << ": " << entryIt->description << std::endl;
        swap(*lastIt, *entryIt);
      }
      lastEntryOrderingMetric = entryOrderingMetric;
    }

    if (primary == 0)
    {
      primary = nextPrimary;
      if (nextPrimary)
      {
        std::cout << "Next we will develop " << primary->code << ": " << primary->description << std::endl;
      }
      else
      {
        std::cout << "YOU HAVE LEARNED ALL YOUR GOAL HABITS.  Let's move forward." << std::endl;
      }
    }

    if (reinforce == 0)
    {
      throw std::runtime_error("no " + reinforceCode + " event found in list");
    }

    // place reinforce event as entry 1
    swap(*reinforce, list.entries[1]);

    if (primary)
    {
      // place primary event as entry 0
      primary->set(STATE_KEY_PRIMARY, "primary");
      swap(*primary, list.entries[0]);
      // - [X] place primary prior to reinforce event; rest of list stays same
    }

    // - [X] events are already [bubble?] sorting towards ordering metric

    // - [X] caller rewrites reordered list
  }

  // guess i'll want to take a list with a history
  // and just plain reorder the list
  // will need to write the list back out afterward, that will be done elsewhere

  std::string reinforceCode;
  RoutineMetric & selectionMetric;
  RoutineMetric & learnedMetric;
  double learnedCutoff;
  RoutineMetric & tertiaryOrderingMetric;

};

class Interface
{
public:
  virtual void runPrompts(class Routine & routine, RoutineList & list) = 0;
  virtual ~Interface() = default;
};

class Routine
{
public:
  // process history using csv files.
  // produce ordering of brushing.routine using metrics
  //  NEW METRIC: success of having task.  if task is success, put other one for learning.
  //  separate out how to order and judge
  //  do in SMALL SIMPLE classes! need result!
  //
  // 1. infer how well the task has been acquired as a new metric
  // 2. combine importance with how well acquired to produc next task
  //      perhaps mutate importance to a minimum degree of acquiring the task
  // "development" and "target development"
  // how about a target of times done per time unit
  //
  // [X] 1: mark tasks with goal frequency / time unit
  // [X] 2: rate performance to reach goal task development
  // [X] 3: judge importance based on goal and performance, modular
  //        -> Difference metric
  // [ ] 4: order tasks based on importance and modular strategy
  // 5: modify reward to occur immediately after primary task
  // 6: make dispenser solid before switching off of toothbrushing as route of administration

  Routine(RoutineList list, RoutineHistorySource & history = defaultRoutineHistory)
  : list(list), history(history)
  { }

  Routine(std::string routinefile, RoutineHistorySource & history = defaultRoutineHistory)
  : list(RoutineList::fromTextfile(routinefile)), history(history)
  { }

  void run(OrderingStrategy & orderingStrategy, Interface & interface)
  {
    orderingStrategy.reorder(list, history);
    interface.runPrompts(*this, list);
  }

  // - [X] add prompting strategy to run func above (just call existing routine script)
  //      CELEBRATE! so close! YES YES!
  //
  //      dang prompting strategy requires filename ...
  //      prompting strategy needs routine filename and script path
  //      I guess they're in the constructor =S
  //
  // - [ ] call Routine.run() and fix bugs

  RoutineList list;
  RoutineHistorySource & history;
};

// WARNING: highly insecure if not used only by sysop
class InterfaceRoutineScript : public Interface
{
public:
  InterfaceRoutineScript(std::string scriptCommand = "./routine")
  : scriptCommand(scriptCommand)
  { }
  virtual void runPrompts(Routine & routine, RoutineList & list)
  {
    list.toTextfile();
    std::string cmdline = scriptCommand + " " + list.filename + " fromroot";
    auto ret = system(cmdline.c_str());
    if (ret) throw std::runtime_error("script command faile");
  }

  std::string scriptCommand;
};

Routine gRoutineBrushing("brushing.routine");

// - [ ] provide metrics for strat1
//      - [ ] check proper directionality of metrics
//
// SELECTION
//  looks like I had some idea above that might have been a difference relationship between value and development.
//  Value measures the provided 'value' for the entry -- high values will be desired first
//  Development measures the degree to which the task goal is met -- low values will be desired first
//  so a good selection metric could be a combination of value and development
//  note that fully-developed habits do not need to be learned any further
//  otherwise, undeveloped habits may be learned in a combination of value and development needed
//  since we want full development to result in lowest possible values, we might use e.g. multipleication somewhere here ...
//  importance = value * (1 - development)
//  importance = value / development
//  selectionMetric selects the highest one, so it will pick the highest value with the lowest development.
RoutineMetricValue gMetricValue;
RoutineMetricDevelopment gMetricDevelopment(7);
auto gMetricNeededDevelopment = gRoutineMetricJudgementLambda(
  [](double development) -> double
  {
    return 1 - development;
  },
  gMetricDevelopment
);
auto gMetricImportanceValueTimesNeededDevelopment = gRoutineMetricJudgementLambda(
  [](double value, double neededDevelopment) -> double
  {
    return value * neededDevelopment;
  },
  gMetricValue,
  gMetricNeededDevelopment
);
auto gMetricImportanceValueThenNeededDevelopment = gRoutineMetricJudgementLambda(
  [](double value, double development) -> double
  {
    // when unlearned, value is first
    // when learned ... I guess neededDevelopment is okay, maybe make it negative?
    return development < 1.0 ? value : -development;
  },
  gMetricValue,
  gMetricDevelopment
);

//OrderingStrategyPrimaryAheadOfEvent gRoutOrderStrat1("BT2Z", gMetricImportanceValueTimesNeededDevelopment, gMetricDevelopment, 1.0, gMetricNeededDevelopment);
//OrderingStrategyPrimaryAheadOfEvent gRoutOrderStrat2("BT2Z", gMetricImportanceValueTimesNeededDevelopment, gMetricDevelopment, 1.0, gMetricImportanceValueTimesNeededDevelopment);
OrderingStrategyPrimaryAheadOfEvent gRoutOrderStrat3("BT2Z", gMetricImportanceValueThenNeededDevelopment, gMetricDevelopment, 1.0, gMetricImportanceValueThenNeededDevelopment);

InterfaceRoutineScript gInterfaceOldScript("./routine");

void routine2()
{
  // macro function
  gRoutineBrushing.run(gRoutOrderStrat3, gInterfaceOldScript);
}

// quick summary for us: Karl doesn't want to fight, and has a strategy known to resolve conflicts without fighting.
//    K: one woman told me it is like a magic bullet, _if_ the people are committed to going through with it.
//
// K: I've been through a crazy ton and have adapted to my fate one might say.  I don't want anyone to suffer
//    around hurting me.  I do not support altering people's experiences, though, unless they desire it.

// I believe in using Nonviolent Communication to resolve problems.  It requires being able to talk to people
// about something reliable.
// Nonviolnt Communication has been used in warzones to resolve violent conflict.  Also with families etc.
// The idea behind it is that there is always a strategy that results in all parties' needs being met without
// conflict (this has always ended up being the case), but it requires them to be able to learn to hear correctly
// the real needs behind the struggle.
// It is very flexible and can handle most restrictions, but some communication is needed.
// I am not experienced in this.  I have just found it and would like to learn or use it.
//
// It is more efficient to use NVC than to fight, because your energy goes directly into the needs involved,
// rather than being expended in the struggle.  Wars have been resolved in days.
//
// I've heard of this pattern from the NVC book, of 
// so you haven't done this. 
//  K: yes i'm just learning of it.  it takes about a year of practice I hear.
//    and I'm learning in a strange way because of my mental situation.
//    also not practicing regularly
//
// Karl reached out to a few NVC mediators/counselors/etc, but has become confused around continuing to engage any of them.

int main(int argc, const char **argv)
{
  routine2();
  return 0;
}
