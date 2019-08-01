#!/usr/bin/python

import re

rawlines = open("Affirmations.txt").readlines()

statements = set()

for line in rawlines:
	reprefix = '^You (can|may|are free to) (.*?) (in|from|about)? ?'
	resuffix = '\.?\s*'
	res1 = re.match(reprefix + '(whomever|as .* as|however|whenever|however and whenever|any .*?|whoever|whatever ?.*?|anything|anyone|anywhere) (you want|you would like)' + resuffix, line)
	words1 = ('can','may','are free to')
	words4 = ('you want', 'you\'d like', 'you feel like', 'you like', 'you desire', 'you care to', 'you want to', 'you feel to', 'you choose')
	if res1:
		res1 = res1.groups()
		words2 = [res1[1]]
		if res1[2]:
			words3 = ['{} {}'.format(res1[2], res1[3])]
		else:
			words3 = ['{}'.format(res1[3])]
			if re.match('anything|whatever', res1[3]):
				words3.append('whatever')
				words3.append('anything')
			if re.match('as much as|however and whenever|however|whenever', res1[3]):
				words3.append('as much as')
				words3.append('whenever')
				words3.append('however')
			if re.match('anywhere|where-ever', res1[3]):
				words3.append('anywhere')
				words3.append('where-ever')
				words3.append('however')
			if re.match('anyone|whoever|whomever', res1[3]):
				words3.append('anyone')
				words3.append('whoever')
				words3.append('whomever')

		for word1 in words1:
			for word2 in words2:
				for word3 in words3:
					for word4 in words4:
						statement = "You {} {} {} {}.".format(word1, word2, word3, word4)
						#print statement
						statements.add(statement)
	res2 = re.match(reprefix + '(freely|all .*?|every .*?|and not .*?)' + resuffix, line)
	if res2:
		res2 = res2.groups()
		if res2[2]:
			words2 = ['{} {}'.format(res2[1], res2[2])]
		else:
			words2 = ['{}'.format(res2[1])]
		words3 = [res2[3]]
		for word1 in words1:
			for word2 in words2:
				for word3 in words3:
					statements.add('You {} {} {}.'.format(word1, word2, word3))
	if not res1 and not res2:
		statements.add(line)
		continue
	#for firstword in ("can", "may", "are free to"):
		
for statement in statements:
	print statement
