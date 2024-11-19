// WordCount.cpp

#include "WordCount.h"

using namespace std;

// Default constructor
WordCount::WordCount() {}

// Simple hash function. Do not modify.
size_t WordCount::hash(std::string word) const {
	size_t accumulator = 0;
	for (size_t i = 0; i < word.size(); i++) {
		accumulator += word.at(i);
	}
	return accumulator % CAPACITY;
}

int WordCount::getTotalWords() const {
	// STUB - your solution from Lab06 goes here
	return -1;
}

int WordCount::getNumUniqueWords() const {
	// STUB - your solution from Lab06 goes here
	return -1;
}

int WordCount::getWordCount(std::string word) const {
	// STUB - your solution from Lab06 goes here
	return -1;
}
	
int WordCount::incrWordCount(std::string word) {
	// STUB - your solution from Lab06 goes here
	return -1;
}

int WordCount::decrWordCount(std::string word) {
	// STUB - your solution from Lab06 goes here
	return -2;
}


bool WordCount::isWordChar(char c) {
	// STUB - your solution from Lab06 goes here
	return false;
}

std::string WordCount::makeValidWord(std::string word) {
	// STUB - your solution from Lab06 goes here
	return "";
}

void WordCount::dumpWordsSortedByWord(std::ostream &out) const {
	// STUB
	return "";
}

void WordCount::dumpWordsSortedByOccurence(std::ostream &out) const {
	// STUB
	return "";
}

void WordCount::addAllWords(std::string text) {
	// STUB
	return;
}
