package greetings

import (
	"regexp"
	"testing"
)

// TestHelloName calls Hello with a name, checking for a valid return value.
func TestHelloName(t *testing.T) {
	name := "Killijiros"
	want := regexp.MustCompile(`\b` + name + `\b`)
	msg, err := Hello(name)

	if !want.MatchString(msg) || err != nil {
		t.Fatalf(`Hello(%q) = %q, %v, want match for %q, nil`, name, msg, err, want)
	}
}

// TestHelloEmpty calls Hello with an empty string, checking for an error.
func TestHelloEmpty(t *testing.T) {
	msg, err := Hello("")

	if msg != "" || err == nil {
		t.Fatalf(`Hello("") = %q, %v, want "", error`, msg, err)
	}
}

func TestHellosName(t *testing.T) {
	names := []string{"Test1", "Test2", "Test3"}

	namesRegEx := make(map[string]*regexp.Regexp)

	for _, name := range names {

		namesRegEx[name] = regexp.MustCompile(`\b` + name + `\b`)
	}

	namesMap, err_hellos := Hellos(names)

	if err_hellos != nil {
		t.Fatalf(`Hellos() returned an error: %v`, err_hellos)
	}

	for _, name := range names {
		if !namesRegEx[name].MatchString(namesMap[name]) || err_hellos != nil {
			t.Errorf(`Hellos(), for %q = %q, %v, want match for %q, nil`, name, namesMap[name], err_hellos, namesRegEx[name])
		}
	}
}
