AWS_REGION ?= us-east-1
S3_BUCKET ?= dmc-srodriguez-20181130

bootstrap:
	aws s3api create-bucket --bucket $(S3_BUCKET) --region $(AWS_REGION)

test:
	docker-compose build && docker-compose up

run:
	docker-compose build && docker-compose up redis datastax

all-test: bootstrap test

all: bootstrap run

teardown:
	@echo Are you sure you want to delete the bucket, $(S3_BUCKET)? You have 10 seconds to CTRL+C and cancel. && \
	sleep 10 && \
	docker-compose stop && \
	aws s3 rm --recursive s3://$(S3_BUCKET)/ && \
	echo "Deleting S3 bucket: $(S3_BUCKET)" && \
	aws s3api delete-bucket --bucket $(S3_BUCKET)