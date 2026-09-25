package greetings

import (
	"errors"
	"fmt"
)

func Hello(name string) (string, error) {
	if name == "" {
		return "", errors.New("empty name")
	}

	message := fmt.Sprintf("Hi, %v. Welcome!", name)

	return message, nil
}

func Hellos(names []string) (map[string]string, error) {
	if len(names) == 0 {
		return nil, errors.New("empty slice of names")
	}

	namesMap := make(map[string]string)
	var err error
	for _, name := range names {
		namesMap[name], err = Hello(name)
		if err != nil {
			return nil, err
		}
	}

	return namesMap, nil
}
