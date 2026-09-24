package main

import (
	"fmt"
	"log"
	"math/rand/v2"

	"github.com/vcTaz/CS-452-Data-Centers/Labs/3-Go/internal/greetings"
)

const MaxSize = 3

func main() {
	/*
		var message string
		message = greetings.Hello("Killijiros:)
	*/
	log.SetPrefix("greetings: ")
	log.SetFlags(0)

	var names []string
	var name string
	// depricated: for i := 0; i < MaxSize; i++ {
	for range MaxSize {
		fmt.Printf("Enter a name:\n")
		fmt.Scan(&name)
		names = append(names, name)
	}

	/*
		for i := range MAX_SIZE {
			fmt.Printf("%v\n", names[i])
		}
	*/

	message, err_hello := greetings.Hello(names[rand.IntN(len(names))])

	namesMap, err_hellos := greetings.Hellos(names)
	//message, err := greetings.Hello(names[rand.Int() % len(names)])
	//message, err := greetings.Hello("Killijiros")
	if err_hello != nil {
		log.Fatal(err_hello)
	}

	fmt.Printf("%v\n", message)

	if err_hellos != nil {
		log.Fatal(err_hellos)
	}

	for _, name := range names {
		fmt.Printf("%v\n", namesMap[name])
	}
}
