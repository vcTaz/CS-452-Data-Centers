# Lab 3 — Go

## Layout

```
3-Go/
├── go.mod                  # module github.com/vcTaz/CS-452-Data-Centers/Labs/3-Go
├── cmd/
│   └── hello/main.go       # executables: one directory per binary
├── internal/
│   └── greetings/          # packages private to this module
├── docs/                   # reference material
└── Makefile
```

New program → `cmd/<name>/main.go`. New shared package → `internal/<pkg>/`.

## Usage

```sh
make run      # go run ./cmd/hello
make test     # go test ./...
make build    # binaries into bin/
make          # fmt + vet + test + build
```
