PROJECTNAME=$(shell basename "$(PWD)")
DOCKERCMD=docker
TAG?=latest
IMG_NAME=order_book

## docker: Create the docker image
docker: docker-build

## docker-build: Create the docker image.
docker-build:
	$(DOCKERCMD) build -t $(IMG_NAME):$(TAG) .
	$(DOCKERCMD) tag $(IMG_NAME):$(TAG) $(IMG_NAME):latest


.PHONY: help
all: help
help: Makefile
	@echo
	@echo " Choose a command run in "$(PROJECTNAME)":"
	@echo
	@sed -n 's/^##//p' $< | column -t -s ':' |  sed -e 's/^/ /'
	@echo
