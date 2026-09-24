BIN_DIR := bin
CMDS    := $(notdir $(wildcard cmd/*))

.PHONY: all build run test cover fmt vet tidy clean

all: fmt vet test build

build:
	@mkdir -p $(BIN_DIR)
	@for c in $(CMDS); do go build -o $(BIN_DIR)/$$c ./cmd/$$c; done

run:
	go run ./cmd/hello

test:
	go test ./...

cover:
	go test -cover ./...

fmt:
	gofmt -l -w .

vet:
	go vet ./...

tidy:
	go mod tidy

clean:
	rm -rf $(BIN_DIR)
