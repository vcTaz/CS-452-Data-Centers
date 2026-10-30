# Homework Assignment 2

Submission Deadline: October 30, 2026

This is an individual assignment to be conducted individually by each student.

## Part 1: Building Inverted Index

Inverted indices are widely used in computer science, and are particularly useful in document searching. Broadly speaking, an inverted index is a map from interesting facts about the underlying data, to the original location of that data. For example, in the context of search, it might be a map from keywords to documents that contain those words. 

For this exercise, you will have you build Map and Reduce functions for generating an inverted index.

We have created a second binary in `cmd/invertedindex/main.go` that is very similar to the `cmd/wordcount/main.go` you built earlier. You should modify `mapF` and `reduceF` in `cmd/invertedindex/main.go` so that they together produce an inverted index. 

#### Map Function

The `mapF` function processes each document and generates a list of (word, filename) pairs. For every word in the document, emit a pair with the word as the key and the document name as the value. 

```
Input: (filename, contents)

Output: [(word1, filename), (word2, filename), …]
```

#### Reduce Function

The `reduceF` function receives a word and a list of all document names in which that word appeared. Its job is to produce a single string containing the number of documents followed by the filenames in sorted, comma-separated order.

```
Input: (word, list of filenames)

Output: (word, "#documents file1,file2,…")
```

#### Note on duplicates

You need to ensure that each document is counted only once per word in the final output. How you handle duplicates is flexible: you can remove duplicates either in the map function (emitting each word once per document) or in the reduce function (filtering the list of filenames). Both approaches are valid as long as the final index reflects unique documents for each word.

#### Testing

Running `cmd/invertedindex/main.go` should output a list of tuples, one per line, in the following format. 

```
$ go run `cmd/invertedindex/main.go master sequential test/data/pg-*.txt`
$ head -n5 mrtmp.iiseq
A: 16 pg-being_ernest.txt,pg-dorian_gray.txt,pg-dracula.txt,pg-emma.txt,pg-frankenstein.txt,pg-great_expectations.txt,pg-grimm.txt,pg-huckleberry_finn.txt,pg-les_miserables.txt,pg-metamorphosis.txt,pg-moby_dick.txt,pg-sherlock_holmes.txt,pg-tale_of_two_cities.txt,pg-tom_sawyer.txt,pg-ulysses.txt,pg-war_and_peace.txt
ABC: 2 pg-les_miserables.txt,pg-war_and_peace.txt
ABOUT: 2 pg-moby_dick.txt,pg-tom_sawyer.txt
ABRAHAM: 1 pg-dracula.txt
ABSOLUTE: 1 pg-les_miserables.txt
```

If it is not clear from the listing above, the format is:

```
word: #documents documents,sorted,and,separated,by,commas
```

You can test your implementation's correctness with the following command, which should produce these resulting last 10 items in the index:

```
sort -k1,1 mrtmp.iiseq | sort -snk2,2 mrtmp.iiseq | grep -v '16' | tail -10
women: 15 pg-being_ernest.txt,pg-dorian_gray.txt,pg-dracula.txt,pg-emma.txt,pg-frankenstein.txt,pg-great_expectations.txt,pg-huckleberry_finn.txt,pg-les_miserables.txt,pg-metamorphosis.txt,pg-moby_dick.txt,pg-sherlock_holmes.txt,pg-tale_of_two_cities.txt,pg-tom_sawyer.txt,pg-ulysses.txt,pg-war_and_peace.txt
won: 15 pg-being_ernest.txt,pg-dorian_gray.txt,pg-dracula.txt,pg-frankenstein.txt,pg-great_expectations.txt,pg-grimm.txt,pg-huckleberry_finn.txt,pg-les_miserables.txt,pg-metamorphosis.txt,pg-moby_dick.txt,pg-sherlock_holmes.txt,pg-tale_of_two_cities.txt,pg-tom_sawyer.txt,pg-ulysses.txt,pg-war_and_peace.txt
wonderful: 15 pg-being_ernest.txt,pg-dorian_gray.txt,pg-dracula.txt,pg-emma.txt,pg-frankenstein.txt,pg-great_expectations.txt,pg-grimm.txt,pg-huckleberry_finn.txt,pg-les_miserables.txt,pg-moby_dick.txt,pg-sherlock_holmes.txt,pg-tale_of_two_cities.txt,pg-tom_sawyer.txt,pg-ulysses.txt,pg-war_and_peace.txt
words: 15 pg-dorian_gray.txt,pg-dracula.txt,pg-emma.txt,pg-frankenstein.txt,pg-great_expectations.txt,pg-grimm.txt,pg-huckleberry_finn.txt,pg-les_miserables.txt,pg-metamorphosis.txt,pg-moby_dick.txt,pg-sherlock_holmes.txt,pg-tale_of_two_cities.txt,pg-tom_sawyer.txt,pg-ulysses.txt,pg-war_and_peace.txt
worked: 15 pg-dorian_gray.txt,pg-dracula.txt,pg-emma.txt,pg-frankenstein.txt,pg-great_expectations.txt,pg-grimm.txt,pg-huckleberry_finn.txt,pg-les_miserables.txt,pg-metamorphosis.txt,pg-moby_dick.txt,pg-sherlock_holmes.txt,pg-tale_of_two_cities.txt,pg-tom_sawyer.txt,pg-ulysses.txt,pg-war_and_peace.txt
worse: 15 pg-being_ernest.txt,pg-dorian_gray.txt,pg-dracula.txt,pg-emma.txt,pg-frankenstein.txt,pg-great_expectations.txt,pg-grimm.txt,pg-huckleberry_finn.txt,pg-les_miserables.txt,pg-moby_dick.txt,pg-sherlock_holmes.txt,pg-tale_of_two_cities.txt,pg-tom_sawyer.txt,pg-ulysses.txt,pg-war_and_peace.txt
wounded: 15 pg-being_ernest.txt,pg-dorian_gray.txt,pg-dracula.txt,pg-emma.txt,pg-frankenstein.txt,pg-great_expectations.txt,pg-grimm.txt,pg-huckleberry_finn.txt,pg-les_miserables.txt,pg-moby_dick.txt,pg-sherlock_holmes.txt,pg-tale_of_two_cities.txt,pg-tom_sawyer.txt,pg-ulysses.txt,pg-war_and_peace.txt
yes: 15 pg-being_ernest.txt,pg-dorian_gray.txt,pg-dracula.txt,pg-emma.txt,pg-great_expectations.txt,pg-grimm.txt,pg-huckleberry_finn.txt,pg-les_miserables.txt,pg-metamorphosis.txt,pg-moby_dick.txt,pg-sherlock_holmes.txt,pg-tale_of_two_cities.txt,pg-tom_sawyer.txt,pg-ulysses.txt,pg-war_and_peace.txt
younger: 15 pg-being_ernest.txt,pg-dorian_gray.txt,pg-dracula.txt,pg-emma.txt,pg-frankenstein.txt,pg-great_expectations.txt,pg-grimm.txt,pg-huckleberry_finn.txt,pg-les_miserables.txt,pg-moby_dick.txt,pg-sherlock_holmes.txt,pg-tale_of_two_cities.txt,pg-tom_sawyer.txt,pg-ulysses.txt,pg-war_and_peace.txt
yours: 15 pg-being_ernest.txt,pg-dorian_gray.txt,pg-dracula.txt,pg-emma.txt,pg-frankenstein.txt,pg-great_expectations.txt,pg-grimm.txt,pg-huckleberry_finn.txt,pg-les_miserables.txt,pg-moby_dick.txt,pg-sherlock_holmes.txt,pg-tale_of_two_cities.txt,pg-tom_sawyer.txt,pg-ulysses.txt,pg-war_and_peace.txt
```

(this sample result is also found in test/scripts/test-ii.out)

To make testing easy for you, from the project directory, run:

```
$ sh ./test/scripts/test-ii.sh
```

and it will report if your solution is correct or not.

## Part 2: Evaluating Inverted Index

To better understand the performance characteristics and scalability of distributed MapReduce, you will evaluate your implementation locally on a single machine by spawning multiple concurrent worker processes alongside the master.

Unlike sequential mode, distributed mode decouples the master coordinator from the worker processes. You can simulate a local cluster by running the master in your primary terminal and launching multiple workers as background processes using distinct ports.

Start the Master (specifying your input files):

```Bash
go run cmd/invertedindex/main.go master localhost:7777 test/data/pg-*.txt
```

Start Local Workers in the background (using separate ports for each worker):

```Bash
go run cmd/invertedindex/main.go worker localhost:7777 localhost:8080 &
go run cmd/invertedindex/main.go worker localhost:7777 localhost:8081 &
```

Conduct the following three performance experiments using your local multi-worker setup:

- Sensitivity to Number of Workers: Fix your dataset to all 16 Project Gutenberg files, and vary the number of active local worker processes (e.g., 1, 2, 4, 8) and measure the total execution time. Observe how well work is distributed across local CPU cores. 

- Sensitivity to Dataset Size: Fix your cluster configuration, and vary the input dataset size by selecting subsets of the corpus (e.g., 1, 4, 8, and all 16 text files). Determine whether execution time scales linearly, sub-linearly, or super-linearly with data size.

Plot execution time against each varied parameter. Provide a brief explanation of your findings. 

Hint: If you want to test larger dataset sizes beyond the 16 bundled Project Gutenberg files, you can quickly generate a larger pool of input files by copying and renaming the existing ones into a new directory.

## Submission

Commit and push to your GitHub Classroom repository:

```bash
git commit -m "Homework 2 submission: results and report"
git push -u origin main
```

You may push multiple times; grading will use your last push.
