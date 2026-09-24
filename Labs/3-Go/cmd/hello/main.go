package main

import (
	"fmt"
	"log"

	"github.com/vcTaz/CS-452-Data-Centers/Labs/3-Go/internal/greetings"
)

func main() {
	/*
		var message string
		message = greetings.Hello("Killijiros:)
	*/
	log.SetPrefix("greetings: ")
	log.SetFlags(0)

	message, err := greetings.Hello("Killijiros")
	if err != nil {
		log.Fatal(err)
	}

	fmt.Printf("%v\n", message)
}
